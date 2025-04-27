# Network Traffic Simulation

This project simulates network traffic using a Markov chain model and iperf3 for actual network measurements.

## Prerequisites

- Python 3.x
- iperf3

## Setup

1. Install iperf3:
```bash
sudo apt install iperf3
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Simulation

1. Start the iperf3 server in a separate terminal:
```bash
iperf3 -s
```

2. Run the simulation:
```bash
python3 main.py
```

The simulation will run for 100 steps and save the results in `traffic_data.csv`.
