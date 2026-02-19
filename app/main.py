from fastapi import FastAPI
from app.mqtt_client import MQTTClient
from app.uplink_handler import UplinkHandler
from app.datastore import DataStore
from contextlib import asynccontextmanager

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


@app.get("/devices/{device_id}/{sensor_name}/sensor_readings")
async def sensor_readings(device_id: str, sensor_name: str, limit: int  = 20):
    return DataStore.get_device_sensor_readings(device_id, sensor_name, limit=limit)


