import json
from pathlib import Path
from functools import lru_cache
from typing import Any


CONFIG_PATH = Path("config/sensors.json")


class SensorConfig:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.sensors = data.get("sensors", {})
        self.regions = data.get("regions", {})

    def get_reading_defs(self) -> dict[str, tuple[str, str]]:
        """
        returns:
            {
                "temperature_c": ("temperature", "C"),
                ...
            }
        """
        return {
            decoded_key: (cfg["name"], cfg["unit"])
            for decoded_key, cfg in self.sensors.items()
        }

    def get_sensor_id(self, sensor_name: str) -> int:
        if sensor_name == "all":
            return 0xFF

        for cfg in self.sensors.values():
            if cfg["name"] == sensor_name:
                target_id = cfg.get("target_id")

                if target_id is None:
                    raise ValueError(
                        f"Sensor '{sensor_name}' does not support downlink commands"
                    )

                return int(target_id)

        raise ValueError(f"Unknown sensor: {sensor_name}")

    def get_region_id(self, region: str) -> int:
        region = region.upper()

        if region not in self.regions:
            raise ValueError(
                f"Invalid region. Options: {list(self.regions.keys())}"
            )

        return int(self.regions[region])


@lru_cache
def get_sensor_config() -> SensorConfig:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return SensorConfig(data)