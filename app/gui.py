
from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import app as nicegui_app
from nicegui import ui


def register_pages() -> None:
    @ui.page("/")
    def dashboard_page():
        
        #placeholders
        device_select = None
        sensor_select = None
        device_select = None
        sensor_select = None
        last_seen_label = None
        stats_label = None
        recent_table = None




        ##states as a dict 

        selected_device_id = {"value": None}
        selected_sensor_name = {"value": None}
        selected_range = {"hours": 24}

        
        #refresh functions
       
        def refresh_stats() -> None: 
            device_id = selected_device_id["value"]
            sensor_name = selected_sensor_name["value"]

            if not device_id or not sensor_name: 
                stats_label.text = "Stats (last 24h): (select a device + sensor)"
                return 
            
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=selected_range["hours"])
            
            stats = DataStore.get_sensor_stats(device_id, sensor_name, start, end)
            if stats is None:
                stats_label.text = f"Stats (last 24h) for {sensor_name}: (no data)"
                return 
            
            stats_label.text = (
                f"Stats (last {selected_range['hours']} hours) for {stats.sensor_name}: "
                f"count={stats.count}, min={stats.min:.3f}, max={stats.max:.3f}, avg={stats.avg:.3f}"
            )




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
            


            
        
        def refresh_recent_readings() -> None: 
            device_id = selected_device_id["value"]
            if not device_id: 
                recent_table.rows = []
                return 
            
            readings = DataStore.get_recent_device_readings(device_id)
            
            rows = []
            for r in readings:
                rows.append({
                    "measured_at": str(r.measured_at),
                    "sensor_name": r.sensor_name,
                    "value": r.value,
                    "unit": r.unit,
                })
            
            recent_table.rows = rows 


        #event handlers 

        def set_range(hours: int) -> None:
            selected_range["hours"] = hours
            refresh_stats()

            
        def on_device_change(event) -> None: 
            selected_device_id["value"] = event.value
            refresh_last_seen()
            refresh_sensors()
            refresh_recent_readings()
        
        def on_sensor_change(event) -> None:
            selected_sensor_name["value"] = event.value
            refresh_stats()



        with ui.column().classes("w-full items-center"):

            # main card
            with ui.card().classes("w-full max-w-5xl"):

                ui.label("Sensor Dashboard").classes("text-2xl font-bold")

                # contrl row 
                with ui.row().classes("w-full items-end gap-4"):

                    device_select = ui.select(
                        options=[],
                        label="Device",
                        on_change=on_device_change,
                    ).classes("w-64")

                    sensor_select = ui.select(
                        options=[],
                        label="Sensor",
                        on_change=on_sensor_change,
                    ).classes("w-64")

                    with ui.row().classes("gap-2"):
                        ui.button("1h", on_click=lambda: set_range(1))
                        ui.button("24h", on_click=lambda: set_range(24))
                        ui.button("7d", on_click=lambda: set_range(168))

                # info
                with ui.row().classes("w-full justify-between mt-2"):
                    last_seen_label = ui.label(
                        "Last seen: (select a device)"
                    ).classes("text-sm opacity-80")

                    stats_label = ui.label(
                        "Stats: (select a device + sensor)"
                    ).classes("text-sm")

            # recent readings card 
            with ui.card().classes("w-full max-w-5xl mt-4"):
                ui.label("Recent Readings").classes("text-lg font-semibold")

                recent_table = ui.table(
                    columns=[
                        {"name": "measured_at", "label": "Time", "field": "measured_at"},
                        {"name": "sensor_name", "label": "Sensor", "field": "sensor_name"},
                        {"name": "value", "label": "Value", "field": "value", "align": "right"},
                        {"name": "unit", "label": "Unit", "field": "unit"},
                    ],
                    rows=[],
                    row_key="measured_at",
                ).classes("w-full")


            

        
        
        #initialize 
        refresh_devices()
        refresh_last_seen()
        refresh_sensors()
        refresh_stats()
        refresh_recent_readings()

        ui.timer(5.0, lambda: refresh_recent_readings() if selected_device_id["value"] else None)

