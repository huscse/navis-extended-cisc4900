import psycopg
from psycopg.rows import dict_row
import os

def get_conn():
    # Try DATABASE_URL first (production), fallback to local
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Production:
        return psycopg.connect(database_url, row_factory=dict_row)
    else:
        # Local development
        return psycopg.connect(
            host="localhost",
            port=5432,
            dbname="navis",
            user="navis",
            password="navis",
            row_factory=dict_row,
        )