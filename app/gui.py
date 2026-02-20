from fastapi import FastAPI
from app.mqtt_client import MQTTClient
from app.uplink_handler import UplinkHandler
from app.datastore import DataStore
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui 
import uvicorn


def register_pages() -> None: 
    @ui.page("/")
    def gui_home():
        ui.dark_mode().bind_value(nicegui_app.storage.user, "dark_mode")

        ui.label("Sensor Dashboard").classes("text-2xl font-bold")
        ui.checkbox('dark mode').bind_value(nicegui_app.storage.user, 'dark_mode')