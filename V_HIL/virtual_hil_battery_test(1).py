# Virtual Hardware-in-the-Loop (HiL) Battery Pack Controller Simulation

import numpy as np
import time
import random
import logging

# --- Configuration ---
NUM_CELLS = 4
VOLTAGE_LIMIT = 4.2  # V
TEMP_LIMIT = 60       # Celsius
TIME_STEP = 1         # seconds
SIM_DURATION = 60     # seconds

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# --- Battery Cell Simulator ---
def simulate_cell_voltage():
    return np.random.normal(loc=3.7, scale=0.05)  # Simulate normal variation

def simulate_temperature():
    return np.random.normal(loc=25, scale=2)      # Simulate normal ambient

# --- Fault Injector ---
def inject_fault(cells):
    if random.random() < 0.1:
        fault_idx = random.randint(0, NUM_CELLS - 1)
        cells[fault_idx] = 4.3  # Overvoltage fault
        logging.warning(f"Fault injected: Cell {fault_idx+1} overvoltage!")
    return cells

# --- Battery Management Logic ---
def check_safety(cell_voltages, temperature):
    for idx, v in enumerate(cell_voltages):
        if v > VOLTAGE_LIMIT:
            logging.error(f"Cell {idx+1} overvoltage: {v:.2f}V. Stopping charge.")
            return False
    if temperature > TEMP_LIMIT:
        logging.error(f"Overtemperature: {temperature:.2f}°C. Stopping charge.")
        return False
    return True

# --- Main Loop ---
def run_virtual_hil():
    logging.info("Starting Virtual HiL Battery Controller Test")
    for t in range(0, SIM_DURATION, TIME_STEP):
        cell_voltages = [simulate_cell_voltage() for _ in range(NUM_CELLS)]
        temperature = simulate_temperature()

        # Possibly inject fault
        cell_voltages = inject_fault(cell_voltages)

        # Log current state
        volt_str = ', '.join(f"{v:.2f}V" for v in cell_voltages)
        logging.info(f"Time {t}s | Voltages: [{volt_str}] | Temp: {temperature:.2f}°C")

        # Check system safety
        if not check_safety(cell_voltages, temperature):
            logging.info("System shutting down due to safety trigger.")
            break

        time.sleep(TIME_STEP)  # simulate real-time delay

    logging.info("Test complete.")

if __name__ == "__main__":
    run_virtual_hil()
