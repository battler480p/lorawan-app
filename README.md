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
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

