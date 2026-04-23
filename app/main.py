from fastapi import FastAPI
from app.mqtt_client import MQTTClient
from app.uplink_handler import UplinkHandler
from app.datastore import DataStore
from app.models import DownlinkCommand, IntervalRequest
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui 
from app.gui import register_pages
from app.downlink_encoder import DownlinkEncoder
import uvicorn
import base64
from fastapi.responses import RedirectResponse



mqtt_service = MQTTClient(on_uplink=UplinkHandler.handle_uplink)

@asynccontextmanager
async def lifespan(app: FastAPI):
    DataStore.init_db()
    print("Starting MQTT Service...")
    mqtt_service.connect()
    yield
    print("Stopping MQTT Service...")
    mqtt_service.disconnect()

app = FastAPI(lifespan=lifespan)




@app.get("/")
async def root():
    return RedirectResponse(url="/gui")


@app.get("/devices")
async def list_devices():
    return DataStore.get_devices()

@app.get("/devices/{device_id}/raw")
async def device_raw(device_id: str, limit: int = 10):
    return DataStore.get_device_raw_payloads(device_id, limit=limit)


@app.get("/devices/{device_id}/readings")
async def device_readings(device_id: str, limit: int = 20):
    return DataStore.get_device_readings(device_id, limit=limit)    

@app.get("/devices/{device_id}/readings/recent")
async def recent_device_readings(device_id: str):
    return DataStore.get_recent_device_readings(device_id)


@app.get("/devices/{device_id}/{sensor_name}/readings")
async def individual_sensor_readings(device_id: str, sensor_name: str, limit: int  = 20):
    return DataStore.get_device_sensor_readings(device_id, sensor_name, limit=limit)

@app.get("/devices/{device_id}/{sensor_name}/readings/since")
async def device_readings_since(device_id: str, sensor_name: str, since: datetime):
    return DataStore.get_device_sensor_readings_since(device_id, sensor_name, since)

@app.get("/devices/{device_id}/readings/between")
async def device_readings_between(device_id: str, start: datetime, end: datetime):
    return DataStore.get_device_readings_between(device_id, start, end)

@app.get("/devices/{device_id}/{sensor_name}/readings/between")
async def singular_device_readings_between(device_id: str, sensor_name: str, start: datetime, end: datetime):
    return DataStore.get_device_singlular_sensor_readings_between(device_id, sensor_name, start, end)

@app.get("/devices/{device_id}/{sensor_name}/stats")
async def sensor_stats(device_id: str, sensor_name: str, start: datetime, end: datetime, limit: int = 20):
    return DataStore.get_sensor_stats(device_id, sensor_name, start, end)

@app.get("/devices/{device_id}/last-seen")
async def device_last_seen(device_id: str):
    return DataStore.get_device_last_seen(device_id)



#DOWNLINK ROUTES 

#helper to send commands 
def send_command(device_id: str, payload_bytes: bytes):
    payload_b64 = base64.b64encode(payload_bytes).decode()

    DataStore.save_downlink_command(
        device_id=device_id,
        cmd=payload_bytes[0],
        target=payload_bytes[1],
        length=payload_bytes[2],
        payload_b64=payload_b64,
        status="queued"
    )

    mqtt_service.send_downlink(device_id, payload_b64)

    return payload_b64


@app.post("/devices/{device_id}/interval/{sensor}")
async def set_interval(device_id: str, sensor: str, interval_minutes: int):

    sensor_id = DownlinkEncoder.get_sensor_id(sensor)

    payload = DownlinkEncoder.encode_set_interval(sensor_id, interval_minutes)

    send_command(device_id, payload)

    return {
        "status": "queued",
        "sensor": sensor,
        "interval_minutes": interval_minutes
    }



@app.post("/devices/{device_id}/status/request")
async def request_status(device_id: str):

    payload = DownlinkEncoder.encode_request_status()

    send_command(device_id, payload)

    return {
        "status": "queued",
        "command": "request_status"
    }


@app.post("/devices/{device_id}/region/request")
async def get_region(device_id: str):

    payload = DownlinkEncoder.encode_get_region()

    send_command(device_id, payload)

    return {
        "status": "queued",
        "command": "get_region"
    }



REGION_MAP = {
    "EU868": 1,
    "US915": 2,
    "AU915": 3,
}

@app.post("/devices/{device_id}/region/set")
async def set_region(device_id: str, region: str):

    region = region.upper()

    if region not in REGION_MAP:
        return {"error": f"Invalid region. Options: {list(REGION_MAP.keys())}"}

    region_id = REGION_MAP[region]

    payload = DownlinkEncoder.encode_set_region(region_id)

    send_command(device_id, payload)

    return {
        "status": "queued",
        "region": region
    }

@app.post("/devices/{device_id}/reset")
async def reset_device(device_id: str):

    payload = DownlinkEncoder.encode_reset()

    send_command(device_id, payload)

    return {
        "status": "queued",
        "command": "reset"
    }




@app.get("/devices/{device_id}/downlinks")
def get_downlinks(device_id: str, limit: int = 50):
    return DataStore.get_device_downlinks(device_id, limit)


register_pages()



ui.run_with(
    app,
    mount_path="/gui",
    storage_secret="pick-your-private-secret-here",
)



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=True)