# Project: V_HIL_V2 - Enhanced Virtual HiL Battery Controller Test

# File: bms_module.py

import logging

VOLTAGE_LIMIT = 4.2  # V
TEMP_LIMIT = 60      # Celsius
CELL_BALANCE_THRESHOLD = 0.05
CAN_TIMEOUT = 3.0    # s without a battery status frame

class BMS:
    def __init__(self, num_cells, can_timeout=CAN_TIMEOUT):
        self.num_cells = num_cells
        self.voltage_limit = VOLTAGE_LIMIT
        self.temp_limit = TEMP_LIMIT
        self.can_timeout = can_timeout
        self.last_frame_time = None

    def frame_received(self, t):
        self.last_frame_time = t

    def arm_can_watchdog(self, t):
        self.last_frame_time = t

    def check_can_timeout(self, t):
        if self.last_frame_time is not None and t - self.last_frame_time >= self.can_timeout:
            logging.error(f"CAN timeout: no battery status for {t - self.last_frame_time:.2f}s. Stopping charge.")
            return False
        return True

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

