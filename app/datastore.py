import sqlite3
from pathlib import Path
from typing import Iterable 
from datetime import datetime 

from app.models import SensorReading 

import json



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
                    raw_json TEXT NOT NULL,
                    ingested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    device_id TEXT NULL, 
                    received_at TEXT NULL,
                    payload_b64 TEXT NULL,
                    decode_status TEXT NOT NULL
                    );
                """)
        conn.commit()
        conn.close()
   
    @classmethod
    def save_raw_only(cls, decode_status, raw_json, device_id=None, received_at=None, payload_b64=None):
        conn = cls._get_conn()
        cur = conn.cursor()

        raw_json_text = json.dumps(raw_json)

        # convert received_at if present
        received_at_text = (
            received_at.isoformat()
            if isinstance(received_at, datetime)
            else received_at
        )

        cur.execute(
            """
            INSERT INTO raw_payloads(
                raw_json,
                device_id,
                received_at,
                payload_b64,
                decode_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                raw_json_text,      # raw_json
                device_id,          # device_id
                received_at_text,   # received_at
                payload_b64,        # payload_b64
                decode_status,      # decode_status
            ),
        )

        raw_id = cur.lastrowid
        conn.commit()
        conn.close()
        return raw_id


    

    @classmethod
    def save_readings(cls, readings: list[SensorReading]) -> None:
        conn = cls._get_conn()
        cur = conn.cursor()

        for reading in readings:
            device_id = reading.device_id
            sensor_name = reading.sensor_name
            value = reading.value
            unit = reading.unit
            measured_at = reading.measured_at


            cur.execute("""
                INSERT INTO sensor_readings(device_id, sensor_name, value, unit, measured_at)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, sensor_name, value, unit, measured_at.isoformat()))

        conn.commit()
        conn.close()




