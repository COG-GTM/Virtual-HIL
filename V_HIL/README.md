# 🔋 V_HIL_V2 — Virtual Hardware-in-the-Loop Battery Test Platform

A modular Python-based virtual HiL (Hardware-in-the-Loop) simulation environment for testing Battery Management Systems (BMS) without physical hardware. Includes real-time CAN emulation, PyQt5 GUI, Flask web dashboard, and Docker support.

---

## 🚀 Features

- 🔌 **CAN Protocol Emulation** — Simulates real CAN traffic and BMS communication
- 🔋 **Battery Pack Simulator** — Cell voltage, SOC, and temperature modeling
- 🧠 **BMS Logic Module** — Fault detection, balancing, thermal control (customizable)
- 📈 **Dual Visualization**
  - `PyQt5` for native desktop GUI
  - `Flask` dashboard with live charts (Voltage, Temp, SOC) and control buttons
- 🐳 **Docker + Docker Compose** — Easy setup and deployment

---

## 🧰 Project Structure

```
V_HIL_V2/
├── bms_module.py           # BMS logic and safety rules
├── battery_simulator.py    # Battery state simulator
├── can_emulator.py         # CAN message emulation
├── can_messages.py         # Message ID definitions and parsing
├── data_logger.py          # Logging system (optional)
├── pyqt_visualizer.py      # PyQt GUI for real-time monitoring
├── flask_dashboard.py      # Flask-based dashboard with Chart.js
├── main.py                 # Simulation controller and orchestrator
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Compose setup
└── README.md               # You're here
```

---

## 🧪 Running the Project

### Option 1: Local (Python 3.10+)

```bash
pip install -r requirements.txt
python main.py
```

Access dashboard at: [http://localhost:5001](http://localhost:5001)

### Option 2: Docker

```bash
docker-compose up --build
```

---

## 🎯 Use Cases

- BMS development and debugging
- Virtual prototyping of battery systems
- Academic demos and simulation-based testing
- Training/testing without expensive hardware

---

## 📌 TODO / Extensions

- CAN DBC file parser integration
- Model predictive BMS controller
- External DB logging (InfluxDB/Grafana)
- Load cycling and battery aging simulation

---

## 📄 License

MIT License

---

## 👨‍🔬 Author

Created by [Vishal] — Battery Simulation Expert & System Modeling Enthusiast.
