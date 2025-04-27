import numpy as np
import subprocess
import time
import csv

# Matriz de transição (exemplo aleatório)
P = np.array([
    [0.7, 0.2, 0.1],
    [0.3, 0.4, 0.3],
    [0.2, 0.3, 0.5]
])

# Estados: 0 = ocioso, 1 = moderado (10Mbps), 2 = alto (50Mbps)
current_state = 0
states = []
bytes_transmitted = []

def next_state(current_state):
    """
    Determines the next state transition based on the transition matrix P and current state.
    
    Args:
        current_state (int): Current state of the system (0=idle, 1=moderate, 2=high)
        
    Returns:
        int: Next state randomly chosen according to transition probabilities
    """
    return np.random.choice([0, 1, 2], p=P[current_state])

def run_iperf(bandwidth_mbps):
    # Simulates an iperf execution for 1 second
    # Change 'localhost' and other configs according to your environment
    result = subprocess.run(
        ["iperf3", "-c", "127.0.0.1", "-u", "-b", f"{bandwidth_mbps}M", "-t", "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output = result.stdout
    # Extract bytes transmitted from the output
    bytes_sent = 0
    for line in output.splitlines():
        if "MBytes" in line and "sender" in line:
            try:
                # Extract the MBytes value and convert to bytes
                mbytes = float(line.split()[4])
                bytes_sent = int(mbytes * 1024 * 1024)  # Convert MB to bytes
            except:
                pass
    return bytes_sent

for step in range(100):
    print(f"Step {step+1}/100 - Estado {current_state}")
    if current_state == 0:
        bytes_sent = 0
        time.sleep(1)
    elif current_state == 1:
        bytes_sent = run_iperf(10)
    elif current_state == 2:
        bytes_sent = run_iperf(50)
    
    states.append(current_state)
    bytes_transmitted.append(bytes_sent)
    
    current_state = next_state(current_state)

# Save to CSV
with open('traffic_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['step', 'state', 'bytes_transmitted'])
    for i in range(100):
        writer.writerow([i, states[i], bytes_transmitted[i]])

print("Finished and saved to traffic_data.csv")
