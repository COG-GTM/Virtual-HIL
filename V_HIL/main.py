
# File: main.py

import time
import logging
from bms_module import BMS
from battery_simulator import BatterySimulator
from can_emulator import CANBus
from can_messages import BATTERY_STATUS_ID, encode_battery_status, decode_battery_status
from data_logger import DataLogger

# File: main.py (Additions for Visualization)
# Add these imports
from flask_dashboard2 import battery_data, start_flask
#from pyqt_visualizer import BatteryVisualizer
from threading import Thread
#from PyQt5.QtWidgets import QApplication

# --- Configuration ---
NUM_CELLS = 4
TIME_STEP = 1       # seconds
SIM_DURATION = 60   # seconds

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def run_virtual_hil():
    logging.info("Starting V_HIL_V2 Battery Controller Test")
    # Inside run_virtual_hil(), add this near the top:
    app_thread = Thread(target=start_flask, daemon=True)
    app_thread.start()

#    qt_app = QApplication([])
#    visual = BatteryVisualizer(NUM_CELLS)
#    visual.show()
    
    battery = BatterySimulator(NUM_CELLS)
    bms = BMS(NUM_CELLS)
    can = CANBus()
    logger = DataLogger()

    for t in range(0, SIM_DURATION, TIME_STEP):
        voltages = battery.simulate_cell_voltage()
        temperature = battery.simulate_temperature()
        soc = battery.update_soc()

        voltages = battery.inject_fault(voltages)

        can.send(msg_id=BATTERY_STATUS_ID, data=encode_battery_status(voltages, temperature, soc))
        msg = can.receive()

        if msg and msg[0] == BATTERY_STATUS_ID:
            voltages, temperature, soc = decode_battery_status(msg[1])

        volt_str = ', '.join(f"{v:.2f}V" for v in voltages)
        logging.info(f"Time {t}s | Voltages: [{volt_str}] | Temp: {temperature:.2f}°C | SoC: {soc:.2f}%")

        safe, voltages = bms.run_control_logic(voltages, temperature)
        logger.log(t, voltages, temperature, soc)

        if not safe:
            logging.info("System shutting down due to safety trigger.")
            break
        # Inside loop, just before time.sleep():
#        visual.update_display(voltages, temperature, soc)
        if battery_data["running"]:
            battery_data["voltages"] = [round(v, 2) for v in voltages]
            battery_data["temperature"] = round(temperature, 2)
            battery_data["soc"] = round(soc, 2)
#        qt_app.processEvents()

# End of update
        
        time.sleep(TIME_STEP)

    logging.info("Test complete.")


if __name__ == "__main__":
    run_virtual_hil()
