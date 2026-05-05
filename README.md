# LoRaWAN Application Server

This repo contains the application module for the S26-15 LoRaWAN Sensor System MDE Project. It receives uplink data from TTN, stores decoded sensor readings in SQLite, and exposes HTTP
APIs using FastAPI.


## Requirements 
- Python 3.10+
- Virtual environment (.venv)
- pip 

## Setup
```bash
python -m venv .venv
source .venv/bin/activate # Mac/Linux 
.venv/Scripts/activate #Windows
pip install -r requirements.txt
```

## Environment Variables 
The MQTT client loads TTN connection settings from environment variables.
Create a .env file in the project root with this format:
```
TTN_MQTT_HOST=nam1.cloud.thethings.network
TTN_MQTT_PORT=8883
TTN_MQTT_USERNAME=your-ttn-application@ttn
TTN_MQTT_API_KEY=your-api-key
TTN_MQTT_TOPIC=v3/your-ttn-application@ttn/devices/+/up
```

## Sensor Configuration 

Sensor definitions are stored in: 

```
config/sensors.json
```

This file controls how decoded TTN payload fields are converted into application sensor readings. An example config is included. 

Example: 
```
{
  "sensors": {
    "temperature_c": {
      "name": "temperature",
      "unit": "C",
      "target_id": 0
    },
    "humidity_percent": {
      "name": "humidity",
      "unit": "%",
      "target_id": 0
    },
    "battery_mV": {
      "name": "battery",
      "unit": "mV",
      "target_id": null
    }
  },
  "regions": {
    "EU868": 1,
    "US915": 2,
    "AU915": 3
  }
}
```

After editing ```config/sensors.json``` restart the application because the config is cached when the app starts. 

The special name ```all``` doesn't need to be in config because it is handled in code and maps to ```0xFF``` which tells the MCU to apply the command to all sensors. 

## Adding a new sensor: 

1. Confirm the field name in TTN's 'decoded_payload'
2. Add a new entry to 'config/sensors.json'
3. Set the normalized 'name' 
4. Set the display/storage 'unit' 
5. Set 'target_id' if MCU supports interval downlinks for that sensor. Use 'null' if not. 
6. Restart the application 



## Running the Server 
To run the server, enter this command 
```bash 
uvicorn app.main:app --reload
```
The FastAPI server runs at 
```
http://127.0.0.1:8000
```


## Running Tests 
To run all unit tests, enter the virtual environment: 
```bash
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate     # Windows
```
Then run 
```
python -m pytest
```



