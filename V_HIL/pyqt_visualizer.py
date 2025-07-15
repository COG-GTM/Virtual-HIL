# Project: V_HIL_V2 - Enhanced Virtual HiL Battery Controller Test

# Existing modules (unchanged):
# bms_module.py, can_emulator.py, battery_simulator.py, can_messages.py, data_logger.py, main.py

# --- New Visualization Modules ---

# File: pyqt_visualizer.py

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar

class BatteryVisualizer(QWidget):
    def __init__(self, num_cells):
        super().__init__()
        self.setWindowTitle("Battery Status (PyQt5)")
        self.layout = QVBoxLayout()
        self.bars = []
        for i in range(num_cells):
            label = QLabel(f"Cell {i+1}")
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(500)
            self.layout.addWidget(label)
            self.layout.addWidget(bar)
            self.bars.append(bar)
        self.temp_label = QLabel("Temperature: 0°C")
        self.soc_label = QLabel("State of Charge: 0%")
        self.layout.addWidget(self.temp_label)
        self.layout.addWidget(self.soc_label)
        self.setLayout(self.layout)

    def update_display(self, voltages, temp, soc):
        for i, v in enumerate(voltages):
            self.bars[i].setValue(int(v * 100))
        self.temp_label.setText(f"Temperature: {temp:.1f}°C")
        self.soc_label.setText(f"State of Charge: {soc:.1f}%")

