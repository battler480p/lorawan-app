
from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui


def register_pages() -> None:
    @ui.page("/")
    def dashboard_page():
        ui.label("Sensor Dashboard").classes("text-2x1 font-bold")
        devices_label = ui.label("")


        status_label = ui.label("Devices: not loaded")

        def on_refresh_click():
            devices = DataStore.get_devices()
            status_label.text = f"Devices: {len(devices)} found"
            devices_label.text = ", ".join(devices) if devices else "(none yet)"

        ui.button("Refresh", on_click=on_refresh_click)

