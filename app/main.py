from fastapi import FastAPI
from app.mqtt_client import MQTTClient
from app.uplink_handler import UplinkHandler
from app.datastore import DataStore
from contextlib import asynccontextmanager
from datetime import datetime

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
    return {"message": "API and MQTT are both running!"}


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







# @app.get("/devices/{device_id}/{sensor_name}")
# async def 




