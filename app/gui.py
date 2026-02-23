
from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui


def register_pages() -> None:
    @ui.page("/")
    def dashboard_page():
        ui.label("Sensor Dashboard").classes("text-2x1 font-bold")

        ## create widget, store state, on change update state and call refresh, refresh pulls from db and updates widget

        #widgets
        device_select = ui.select(options=[], label="Device")
        last_seen_label = ui.label("Last seen: (select a device)")

        ##states as a dict 

        selected_device_id = {"value": None}


        def refresh_devices() -> None:
            devices = DataStore.get_devices()
            device_select.options = devices #drop down 
            if selected_device_id["value"] not in devices:
                selected_device_id["value"] = devices[0] if devices else None 
                device_select.value = selected_device_id["value"]

        def refresh_last_seen() -> None: 
            device_id = selected_device_id["value"]
            if not device_id:
                last_seen_label.text = "Last seen: (no devices yet)"
                return
            last_seen = DataStore.get_device_last_seen(device_id)
            last_seen_label.text = f"Last seen: {last_seen.isoformat() if last_seen else None}"

        def on_device_change(event) -> None: 
            selected_device_id["value"] = event.value
            refresh_last_seen()
            
        device_select.on("update:model-value", on_device_change)
        refresh_devices()
        refresh_last_seen()

