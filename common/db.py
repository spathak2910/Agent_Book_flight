import os
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DB_PATH=Path(ROOT/"travel.db")

def query(sql, params=()):
    """Run a select and return a list of dictionaries"""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as conn:
        conn.row_factory=sqlite3.Row
        return [dict(row) for row in conn.execute(sql, params).fetchall()]

def execute(sql,params=()):
    """Run an insert/update and save it"""
    with closing(sqlite3.connect(DB_PATH, timeout=10)) as conn:
        res=conn.execute(sql, params)
        conn.commit()
        return res.lastrowid