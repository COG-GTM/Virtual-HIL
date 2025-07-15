
# File: data_logger.py

import csv
from datetime import datetime

class DataLogger:
    def __init__(self, filename_prefix="vhil_log"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"{filename_prefix}_{timestamp}.csv"
        self.fields = ["time", "voltages", "temperature", "soc"]
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writeheader()

    def log(self, t, voltages, temp, soc):
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fields)
            writer.writerow({
                "time": t,
                "voltages": ";".join([f"{v:.2f}" for v in voltages]),
                "temperature": f"{temp:.2f}",
                "soc": f"{soc:.2f}"
            })

