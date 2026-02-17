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


    @classmethod
    def get_devices(cls):
        conn = cls._get_conn()
        cur = conn.cursor()

        query = """
                SELECT device_id
                FROM raw_payloads
                WHERE device_id IS NOT NULL
                GROUP BY device_id
                ORDER BY MAX(ingested_at) DESC
                """
        
        cur.execute(query)
        rows = cur.fetchall()

        conn.close()

        return [row["device_id"] for row in rows]
    
    @classmethod
    def get_device_readings(cls, device_id: str, limit: int = 100) -> list[SensorReading]:

        conn = cls._get_conn()
        cur = conn.cursor()

        query = """
                SELECT device_id, 
                sensor_name, 
                value,
                unit, 
                measured_at
                FROM sensor_readings
                WHERE device_id = ?
                ORDER BY measured_at DESC 
                LIMIT ?
                """
        
        cur.execute(query, (device_id, limit))
        rows = cur.fetchall()
        conn.close()

        return [
            SensorReading(
                device_id=row["device_id"],
                sensor_name=row["sensor_name"],
                value=row["value"],
                unit=row["unit"],
                measured_at=row["measured_at"]
            ) 
            for row in rows
        ]


    @classmethod
    def get_device_raw_payloads(cls, device_id: str, limit: int = 50) -> list[dict]:
        conn = cls._get_conn()
        cur = conn.cursor()

        query = """
            SELECT id, ingested_at, received_at, decode_status, raw_json, payload_b64
            FROM raw_payloads
            WHERE device_id = ?
            ORDER BY ingested_at DESC
            LIMIT ?
        """
        cur.execute(query, (device_id, limit))
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "ingested_at": row["ingested_at"],   # stored as text
                "received_at": row["received_at"],   # stored as text or null
                "decode_status": row["decode_status"],
                "payload_b64": row["payload_b64"],
                "raw_json": row["raw_json"],         # JSON string
            }
            for row in rows
        ]
    
    @classmethod
    def get_recent_device_readings(cls, device_id: str) -> list[SensorReading]:
        conn = cls._get_conn()
        cur = conn.cursor()


        #select rows
        #from table
        #join subquery
            #select max measured_at
            #group by sensor_name
            #ON
            #AND?
        


        query = """
                SELECT r.device_id, r.sensor_name, r.value, r.unit, r.measured_at 
                FROM sensor_readings r 
                JOIN (
                SELECT sensor_name, MAX(measured_at) as max_ts
                FROM sensor_readings
                WHERE device_id = ?
                GROUP BY sensor_name 
                ) latest ON r.sensor_name = latest.sensor_name
                AND r.measured_at = latest.max_ts
                WHERE r.device_id = ?
                """
        
        cur.execute(query, (device_id, device_id))
        rows = cur.fetchall()
        conn.close()

        
        return [
            SensorReading(
                device_id=row["device_id"],
                sensor_name=row["sensor_name"],
                value=row["value"],
                unit=row["unit"],
                measured_at=row["measured_at"]
            ) 
            for row in rows
        ]



    



