# Project: V_HIL_V2 - Enhanced Virtual HiL Battery Controller Test

# File: bms_module.py

import logging

VOLTAGE_LIMIT = 4.2  # V
TEMP_LIMIT = 60      # Celsius
CELL_BALANCE_THRESHOLD = 0.05

class BMS:
    def __init__(self, num_cells):
        self.num_cells = num_cells
        self.voltage_limit = VOLTAGE_LIMIT
        self.temp_limit = TEMP_LIMIT

    def check_safety(self, cell_voltages, temperature):
        for idx, v in enumerate(cell_voltages):
            if v > self.voltage_limit:
                logging.error(f"Cell {idx+1} overvoltage: {v:.2f}V. Stopping charge.")
                return False
        if temperature > self.temp_limit:
            logging.error(f"Overtemperature: {temperature:.2f}°C. Stopping charge.")
            return False
        return True

    def balance_cells(self, voltages):
        avg = sum(voltages) / len(voltages)
        balanced = [min(v, avg + CELL_BALANCE_THRESHOLD) for v in voltages]
        logging.debug("Cell balancing applied.")
        return balanced

    def run_control_logic(self, cell_voltages, temperature):
        cell_voltages = self.balance_cells(cell_voltages)
        return self.check_safety(cell_voltages, temperature), cell_voltages

