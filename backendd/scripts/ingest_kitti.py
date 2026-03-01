import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add /backend to sys.path

from db.postgres import get_conn

# >>>> SET THIS to your actual local KITTI path <<<<
KITTI_ROOT = "/Users/husnainkhaliq/Desktop/latitude-ai/backend/data/kitti"


def ingest_kitti():
    if not os.path.isdir(KITTI_ROOT):
        raise RuntimeError(f"KITTI_ROOT not found: {KITTI_ROOT}")

    conn = get_conn()
    cur = conn.cursor()

    # 1) Upsert dataset (safe to re-run)
    cur.execute("""
        INSERT INTO navis.datasets (slug, name, provider, media_base_uri)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE
            SET name = EXCLUDED.name,
                provider = EXCLUDED.provider,
                media_base_uri = EXCLUDED.media_base_uri
        RETURNING id;
    """, (
        "kitti",
        "KITTI",
        "local",
        "file:///" + KITTI_ROOT.rstrip("/") + "/",
    ))
    dataset_id = cur.fetchone()["id"]
    print(f"✅ Dataset 'kitti' id = {dataset_id}")

    # 2) Walk nested structure:
    # KITTI/<scene_type>/<date>/<sequence_sync>/<sensor>/data/*.png
    for scene_type in os.listdir(KITTI_ROOT):  # City, Residential, Campus, Road
        scene_type_path = os.path.join(KITTI_ROOT, scene_type)
        if not os.path.isdir(scene_type_path):
            continue

        for date_folder in os.listdir(scene_type_path):  # 2011_09_26
            date_path = os.path.join(scene_type_path, date_folder)
            if not os.path.isdir(date_path):
                continue

            for sequence_folder in os.listdir(date_path):  # 2011_09_26_drive_0001_sync
                if not sequence_folder.endswith("_sync"):
                    continue
                sequence_path = os.path.join(date_path, sequence_folder)
                if not os.path.isdir(sequence_path):
                    continue

                # Inside sequence: image_00, image_01, image_02, image_03...
                for sensor_folder in os.listdir(sequence_path):
                    sensor_path = os.path.join(sequence_path, sensor_folder)
                    if not os.path.isdir(sensor_path):
                        continue

                    data_dir = os.path.join(sensor_path, "data")
                    if not os.path.isdir(data_dir):
                        continue

                    # 3) Upsert sequence per (dataset, scene_token, sensor)
                    cur.execute("""
                        INSERT INTO navis.sequences (dataset_id, scene_token, sensor)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (dataset_id, scene_token, sensor) DO UPDATE
                            SET sensor = EXCLUDED.sensor
                        RETURNING id;
                    """, (dataset_id, sequence_folder, sensor_folder))
                    sequence_id = cur.fetchone()["id"]

                    # 4) Insert frames (ignore duplicates on rerun)
                    batch = []
                    for frame_file in os.listdir(data_dir):
                        if not frame_file.lower().endswith((".png", ".jpg", ".jpeg")):
                            continue
                        media_key = os.path.join(
                            scene_type,
                            date_folder,
                            sequence_folder,
                            sensor_folder,
                            "data",
                            frame_file
                        )
                        batch.append((sequence_id, frame_file, media_key))

                    if batch:
                        # Use executemany for speed
                        cur.executemany("""
                            INSERT INTO navis.frames (sequence_id, sample_token, media_key)
                            VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING;
                        """, batch)

                        print(f"Inserted ~{len(batch):4d} frames -> {scene_type}/{date_folder}/{sequence_folder}/{sensor_folder}")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ KITTI ingestion completed!")

if __name__ == "__main__":
    ingest_kitti()
