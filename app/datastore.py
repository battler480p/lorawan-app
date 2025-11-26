import sqlite3
from pathlib import Path
from typing import Iterable 
from datetime import datetime 

from app.models import SensorReading 



class DataStore:

    DB_PATH: Path = Path("data.db")
   
    @classmethod
    def _get_conn(cls) -> sqlite3.Connection:
        #create connection to SQLite databse file
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row 
        return conn
    
    @classmethod
    def init_db(cls) -> None: 
        conn = DataStore._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                sensor_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                measured_at TEXT NOT NULL
            );
            """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_payloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    payload_b64 TEXT,
                    received_at TEXT NOT NULL,
                    decode_status TEXT NOT NULL
                    );
                """)
        conn.commit()
        conn.close()
   
    @classmethod
    def save_raw_only(cls, device_id, raw_b64, received_at, status):
        conn = cls._get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO raw_payloads(device_id, payload_b64, received_at, decode_status)
            VALUES (?, ?, ?, ?)
        """, (device_id, raw_b64, received_at.isoformat(), status))

        conn.commit()
        conn.close()

