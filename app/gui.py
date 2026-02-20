
from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui


def register_pages() -> None: 
    @ui.page("/")
    def gui_home():
        ui.dark_mode().bind_value(nicegui_app.storage.user, "dark_mode")

        ui.label("Sensor Dashboard").classes("text-2xl font-bold")
        ui.checkbox('dark mode').bind_value(nicegui_app.storage.user, 'dark_mode')