
from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui


def register_pages() -> None:
    @ui.page("/")
    def dashboard_page():
        ui.label("Sensor Dashboard").classes("text-2xl font-bold")

        ## create widget, store state, on change update state and call refresh, refresh pulls from db and updates widget

        #widgets
        device_select = ui.select(options=[], label="Device").classes("w-80")
        last_seen_label = ui.label("Last seen: (select a device)")

        sensor_select = ui.select(options = [], label = "Sensor").classes("w-80")
        # sensor_info_label = ui.label("Sensor: (select a sensor)")


        ##states as a dict 

        selected_device_id = {"value": None}
        selected_sensor_name = {"value": None}

        
        #refresh functions

        def refresh_devices() -> None:
            devices = DataStore.get_devices() #load device options from DB and update dropdown options 
            device_select.options = devices #drop down 
            if selected_device_id["value"] not in devices:
                selected_device_id["value"] = devices[0] if devices else None 
                device_select.value = selected_device_id["value"]

        def refresh_last_seen() -> None: #update the last seen label based on selected device 
            device_id = selected_device_id["value"]
            if not device_id:
                last_seen_label.text = "Last seen: (no devices yet)"
                return
            last_seen = DataStore.get_device_last_seen(device_id)
            last_seen_label.text = f"Last seen: {last_seen.isoformat() if last_seen else '(never)'}"


        def refresh_sensors() -> None: #update sensor list based on selected device and update sensor dropdown
            device_id = selected_device_id["value"]
            if not device_id:
                sensor_select.options = []
                sensor_select.value = None
                selected_sensor_name["value"] = None
                # sensor_info_label.text = "Sensor: (no device selected)"
                return 
            
            sensors = DataStore.get_device_sensors(device_id)
            sensor_select.options = sensors 

            if selected_sensor_name["value"] not in sensors:
                selected_sensor_name["value"] = sensors[0] if sensors else None 
                sensor_select.value = selected_sensor_name["value"]
            
            # sensor_info_label.text = f"Sensor: {selected_sensor_name['value'] or '(none)'}"

            

        
    #event handlers 
        def on_device_change(event) -> None: 
            selected_device_id["value"] = event.value
            refresh_last_seen()
            refresh_sensors()
        
        def on_sensor_change(event) -> None: 
            selected_sensor_name["value"] = event.value
            # sensor_info_label.text = f"Sensor: {selected_sensor_name['value'] or '(none)'}"
            
        device_select.on("update:model-value", on_device_change)
        sensor_select.on("update:model-value", on_sensor_change)
        
        
        #initialize 
        refresh_devices()
        refresh_last_seen()
        refresh_sensors()

