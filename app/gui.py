from app.datastore import DataStore
from datetime import datetime, timezone, timedelta
from nicegui import ui


def register_pages() -> None:

    @ui.page("/")
    def dashboard_page():

        # -----------------------------
        # state
        # -----------------------------
        selected_device_id = {"value": None}
        selected_sensor_name = {"value": None}
        selected_range = {"hours": 24}

        # -----------------------------
        # ui element placeholders 
        # -----------------------------
        device_select = None
        sensor_select = None
        last_seen_label = None
        stats_label = None
        recent_table = None
        chart = None

        # -----------------------------
        # refresh functions 
        # -----------------------------

        def refresh_stats():
            device_id = selected_device_id["value"]
            sensor_name = selected_sensor_name["value"]

            if not device_id or not sensor_name:
                stats_label.text = "Stats: (select a device + sensor)"
                return

            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=selected_range["hours"])

            stats = DataStore.get_sensor_stats(device_id, sensor_name, start, end)

            if stats is None:
                stats_label.text = f"Stats for {sensor_name}: (no data)"
                return

            stats_label.text = (
                f"{sensor_name} → "
                f"count={stats.count}, "
                f"min={stats.min:.2f}, "
                f"max={stats.max:.2f}, "
                f"avg={stats.avg:.2f}"
            )

        def refresh_devices():
            devices = DataStore.get_devices()
            device_select.options = devices

            if selected_device_id["value"] not in devices:
                selected_device_id["value"] = devices[0] if devices else None
                device_select.value = selected_device_id["value"]

        def refresh_last_seen():
            device_id = selected_device_id["value"]

            if not device_id:
                last_seen_label.text = "Last seen: (no device)"
                return

            last_seen = DataStore.get_device_last_seen(device_id)

            last_seen_label.text = (
                f"Last seen: {last_seen.isoformat() if last_seen else '(never)'}"
            )

        def refresh_sensors():
            device_id = selected_device_id["value"]

            if not device_id:
                sensor_select.options = []
                sensor_select.value = None
                selected_sensor_name["value"] = None
                return

            sensors = DataStore.get_device_sensors(device_id)
            sensor_select.options = sensors

            if selected_sensor_name["value"] not in sensors:
                selected_sensor_name["value"] = sensors[0] if sensors else None
                sensor_select.value = selected_sensor_name["value"]

        def refresh_recent_readings():
            device_id = selected_device_id["value"]

            if not device_id:
                recent_table.rows = []
                recent_table.update()
                return

            readings = DataStore.get_recent_device_readings(device_id)

            rows = [
                {
                    "row_id": f"{r.sensor_name}_{r.measured_at}",
                    "measured_at": str(r.measured_at),
                    "sensor_name": r.sensor_name,
                    "value": r.value,
                    "unit": r.unit,
                }
                for r in readings
            ]

            recent_table.rows = rows
            recent_table.update()
       
        def refresh_chart():
            device_id = selected_device_id["value"]
            sensor_name = selected_sensor_name["value"]

            if not device_id or not sensor_name:
                chart.options["series"][0]["data"] = []
                chart.update()
                return

            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=selected_range["hours"])

            readings = DataStore.get_device_sensor_readings_since(
                device_id, sensor_name, start
            )

            readings = sorted(readings, key=lambda r: r.measured_at)

            times = [
                datetime.fromisoformat(r.measured_at).strftime("%H:%M:%S")
                if isinstance(r.measured_at, str)
                else r.measured_at.strftime("%H:%M:%S")
                for r in readings
            ]

            values = [r.value for r in readings]

            chart.options["xAxis"]["data"] = times
            chart.options["series"][0]["data"] = values
            chart.options["series"][0]["name"] = sensor_name

            chart.update()

        # -----------------------------
        # event handlers
        # -----------------------------

        def on_device_change(event):
            selected_device_id["value"] = event.value
            refresh_last_seen()
            refresh_sensors()
            refresh_recent_readings()
            refresh_chart()

        def on_sensor_change(event):
            selected_sensor_name["value"] = event.value
            refresh_stats()
            refresh_chart()

        def set_range(hours: int):
            selected_range["hours"] = hours
            refresh_stats()
            refresh_chart()

        # -----------------------------
        # ui layout 
        # -----------------------------

        with ui.column().classes("w-full items-center"):

            # header card
            with ui.card().classes("w-full max-w-5xl"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("Sensor Dashboard").classes("text-2xl font-bold")
                    ui.button(
                        "Config",
                        on_click=lambda: ui.navigate.to("../docs"),
                    ).props("outline")

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

                with ui.row().classes("w-full justify-between mt-2"):
                    last_seen_label = ui.label("Last seen:").classes("text-sm")
                    stats_label = ui.label("Stats:").classes("text-sm")

            # chart card
            with ui.card().classes("w-full max-w-5xl mt-4"):
                ui.label("Sensor Trend").classes("text-lg font-semibold")

                chart = ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": []},
                    "yAxis": {"type": "value"},
                    "dataZoom": [{"type": "inside"}, {"type": "slider"}],
                    "series": [
                        {
                            "type": "line",
                            "smooth": True,
                            "data": [],
                        }
                    ],
                }).classes("w-full h-80")

            # table card
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
                    row_key="row_id",
                ).classes("w-full")

        # -----------------------------
        # initialization 
        # -----------------------------
        refresh_devices()
        refresh_last_seen()
        refresh_sensors()
        refresh_stats()
        refresh_recent_readings()
        refresh_chart()

        # -----------------------------
        # auto refresh 
        # -----------------------------
        ui.timer(
            5.0,
            lambda: (
                refresh_devices(),
                refresh_sensors(),
                refresh_stats(),
                refresh_recent_readings(),
                refresh_last_seen(),
                refresh_chart(),
            )
            if selected_device_id["value"]
            else None,
        )