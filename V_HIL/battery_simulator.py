
# File: battery_simulator.py

import numpy as np
import random
import logging

class BatterySimulator:
    def __init__(self, num_cells):
        self.num_cells = num_cells
        self.soc = 100  # percent

    def simulate_cell_voltage(self):
        base_voltage = 3.7 + (self.soc - 50) * 0.005
        return [np.random.normal(loc=base_voltage, scale=0.05) for _ in range(self.num_cells)]

    def simulate_temperature(self):
        return np.random.normal(loc=25, scale=2)

    def inject_fault(self, voltages):
        if random.random() < 0.1:
            fault_idx = random.randint(0, self.num_cells - 1)
            voltages[fault_idx] = 4.3  # Inject overvoltage
            logging.warning(f"Fault injected: Cell {fault_idx+1} overvoltage!")
        return voltages

    def update_soc(self, drain=0.1):
        self.soc = max(0, self.soc - drain)
        return self.soc

