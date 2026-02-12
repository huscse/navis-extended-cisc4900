from fastapi import APIRouter
from backend.db.postgres import get_conn

router = APIRouter()

@router.get("/")
def list_datasets():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM navis.datasets")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
