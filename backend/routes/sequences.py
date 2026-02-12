from fastapi import APIRouter, Query
from backend.db.postgres import get_conn

router = APIRouter()

@router.get("/")
def list_sequences(dataset_id: int = Query(...)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM navis.sequences WHERE dataset_id = %s",
        (dataset_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
