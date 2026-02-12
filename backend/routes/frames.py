from fastapi import APIRouter, Query
from backend.db.postgres import get_conn

router = APIRouter()

@router.get("/")
def list_frames(sequence_id: int = Query(...)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM navis.frames WHERE sequence_id = %s LIMIT 100",
        (sequence_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
