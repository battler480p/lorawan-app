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


