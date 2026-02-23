
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
        last_seen_label = ui.label("Last seen: (select a device)")
        stats_label = ui.label("Stats (last 24h): (select a device + sensor)")

        device_select = ui.select(options=[], label="Device").classes("w-80")
        sensor_select = ui.select(options=[], label="Sensor").classes("w-80")

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





        def refresh_sensors() -> None:
            device_id = selected_device_id["value"]
            if not device_id:
                sensor_select.options = []
                sensor_select.value = None
                selected_sensor_name["value"] = None
                refresh_stats()  
                return

            sensors = DataStore.get_device_sensors(device_id)
            sensor_select.options = sensors


            if selected_sensor_name["value"] not in sensors:
                selected_sensor_name["value"] = sensors[0] if sensors else None
                sensor_select.value = selected_sensor_name["value"]

            refresh_stats()  
            




        def refresh_stats() -> None: 
            device_id = selected_device_id["value"]
            sensor_name = selected_sensor_name["value"]

            if not device_id or not sensor_name: 
                stats_label.text = "Stats (last 24h): (select a device + sensor)"
                return 
            
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=24)
            
            stats = DataStore.get_sensor_stats(device_id, sensor_name, start, end)
            if stats is None:
                stats_label.text = f"Stats (last 24h) for {sensor_name}: (no data)"
                return 
            
            stats_label.text = (
                f"Stats (last 24h) for {stats.sensor_name}: "
                f"count={stats.count}, min={stats.min:.3f}, max={stats.max:.3f}, avg={stats.avg:.3f}"
            )

            

        
    #event handlers 
        def on_device_change(event) -> None: 
            selected_device_id["value"] = event.value
            refresh_last_seen()
            refresh_sensors()
        
        def on_sensor_change(event) -> None:
            selected_sensor_name["value"] = event.value
            refresh_stats()

            
            
        device_select.delete()
        sensor_select.delete()

        device_select = ui.select(
            options=[],
            label="Device",
            on_change=on_device_change,
        ).classes("w-80")

        sensor_select = ui.select(
            options=[],
            label="Sensor",
            on_change=on_sensor_change,
        ).classes("w-80")

        
        
        #initialize 
        refresh_devices()
        refresh_last_seen()
        refresh_sensors()
        refresh_stats()

