import sqlite3
from pathlib import Path
from typing import Iterable 
from datetime import datetime 

from app.models import SensorReading, SensorStats

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS downlink_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    cmd INTEGER NOT NULL,
                    target INTEGER NOT NULL,
                    length INTEGER NOT NULL,
                    payload_b64 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
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


    @classmethod
    def get_device_sensor_readings(cls, device_id: str, sensor_name: str, limit: int = 100):
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
                    AND sensor_name = ? 
                    ORDER BY measured_at DESC 
                    LIMIT ?
                    """
            cur.execute(query, (device_id, sensor_name, limit))
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
    def get_device_sensor_readings_since(cls, device_id: str, sensor_name: str, since):
            conn = cls._get_conn()
            cur = conn.cursor()
            query = """
                        SELECT device_id, sensor_name, value, unit, measured_at
                        FROM sensor_readings
                        WHERE device_id = ?
                         AND sensor_name = ?
                        AND measured_at >= ?
                        ORDER BY measured_at ASC
                        """
            cur.execute(query, (
                                    device_id,
                                    sensor_name,
                                    since.isoformat() if isinstance(since, datetime) else since
                                ))
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
    def get_device_readings_between(cls, device_id: str, start: datetime, end: datetime) -> list[SensorReading]:
         conn = cls._get_conn()
         cur = conn.cursor()
         query = """

                    SELECT device_id, sensor_name, value, unit, measured_at
                    FROM sensor_readings
                    WHERE device_id = ?
                    AND measured_at BETWEEN ? AND ?
                    ORDER BY measured_at ASC
                """
         
         cur.execute(query, (device_id, start.isoformat(), end.isoformat()))
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
    def get_device_singlular_sensor_readings_between(cls, device_id: str, sensor_name: str, start: datetime, end: datetime) -> list[SensorReading]:
         conn = cls._get_conn()
         cur = conn.cursor()
         query = """

                    SELECT device_id, sensor_name, value, unit, measured_at
                    FROM sensor_readings
                    WHERE device_id = ?
                    AND sensor_name = ?
                    AND measured_at BETWEEN ? AND ?
                    ORDER BY measured_at ASC
                """
         
         cur.execute(query, (device_id, sensor_name, start.isoformat(), end.isoformat()))
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
    def get_sensor_stats(cls, device_id: str, sensor_name: str, start:datetime, end:datetime):
         conn = cls._get_conn()
         cur = conn.cursor()
         query = """
                SELECT 
                MIN(value) as min_val,
                MAX(value) as max_val,
                AVG(value) as avg_val,
                COUNT(*) as count
                FROM sensor_readings
                WHERE device_id = ?
                AND sensor_name = ?
                AND measured_at BETWEEN ? AND ?
                """
         cur.execute(query, (device_id, sensor_name, start.isoformat(), end.isoformat()))
         row = cur.fetchone()
         conn.close()


         if row is None or row["count"] == 0:
              return None

         
         

         return SensorStats(
                   device_id=device_id,
                   sensor_name = sensor_name,
                   min = row["min_val"],
                   max = row["max_val"],
                   avg=row["avg_val"],
                   count = row["count"],
                   start=start,
                   end =end
              )
    
    @classmethod
    def get_device_last_seen(cls, device_id: str) -> datetime | None:
         conn = cls._get_conn()
         cur = conn.cursor()
         query = """
                SELECT MAX(measured_at) AS last_seen
                FROM sensor_readings
                WHERE device_id = ?
                """
         cur.execute(query, (device_id,))
         row = cur.fetchone()
         conn.close()

         if row["last_seen"] is None:
            return None
         
         return datetime.fromisoformat(row["last_seen"])
    
    @classmethod
    def get_device_sensors(cls, device_id) -> list[str]:
         conn = cls._get_conn()
         cur = conn.cursor()
         query = """
         SELECT sensor_name
         FROM sensor_readings
         WHERE device_id = ?
         GROUP BY sensor_name
         ORDER BY MAX(measured_at) DESC
         """

         cur.execute(query, (device_id,))
         rows = cur.fetchall()
         conn.close()
    
        
         return [row["sensor_name"] for row in rows]
    
    @classmethod
    def save_downlink_command(cls, device_id, cmd, target, length, payload_b64, status="queued"):
        conn = cls._get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO downlink_commands(
                device_id,
                cmd,
                target,
                length,
                payload_b64,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (device_id, cmd, target, length, payload_b64, status))

        conn.commit()
        conn.close()


    @classmethod
    def get_device_downlinks(cls, device_id: str, limit: int = 50):
        conn = cls._get_conn()
        cur = conn.cursor()

        query = """
            SELECT id, device_id, cmd, target, length, payload_b64, status, created_at
            FROM downlink_commands
            WHERE device_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """

        cur.execute(query, (device_id, limit))
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "device_id": row["device_id"],
                "cmd": row["cmd"],
                "target": row["target"],
                "length": row["length"],
                "payload_b64": row["payload_b64"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]





    



