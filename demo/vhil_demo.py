"""Stage-5 demo orchestrator: runs the V_HIL battery model -> CAN -> BMS -> dashboard/logger
loop using the repo's own modules, and adds a REST fault-injection API on the same Flask app.

Faults are injected upstream of the CAN bus (i.e. into the *plant*), so the BMS only ever
sees decoded CAN frames - exactly as it would on a real HIL bench.
"""
import argparse
import csv
import logging
import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "V_HIL"))

from battery_simulator import BatterySimulator  # noqa: E402
from bms_module import BMS, TEMP_LIMIT  # noqa: E402
from can_emulator import CANBus  # noqa: E402
from can_messages import (BATTERY_STATUS_ID, FAULT_STATUS_ID,  # noqa: E402
                          decode_battery_status, encode_battery_status)
from flask import jsonify  # noqa: E402
from flask_dashboard2 import app, battery_data  # noqa: E402

from dashboard_page import register as register_demo_page  # noqa: E402

register_demo_page(app)

NUM_CELLS = 4
FAULTS = {
    "overtemp": "Coolant loss: pack temperature ramps to 70 C",
    "overvoltage": "Charger runaway: cell 2 driven to 4.35 V",
    "imbalance": "Weak cell: cell 4 sags 0.30 V below the pack",
}

state = {
    "active_fault": None,
    "fault_since": None,
    "contactor": "CLOSED",
    "bms_status": "OK",
    "events": [],
    "tick": 0,
}
lock = threading.Lock()

CAN_TERM_FMT = "\033[36m[CAN 0x{id:03X}]\033[0m t={t:>3}s  V=[{v}]  T={temp:5.1f}C  SOC={soc:5.1f}%  {tag}"


def apply_fault(voltages, temperature, fault, elapsed):
    if fault == "overtemp":
        temperature = 25 + min(45, 12 * elapsed)  # ramps past TEMP_LIMIT (60 C) in ~3 s
    elif fault == "overvoltage":
        voltages[1] = 4.35
    elif fault == "imbalance":
        voltages[3] -= 0.30
    return voltages, temperature


@app.route("/fault/<name>", methods=["POST"])
def inject(name):
    if name == "clear":
        return clear()
    if name not in FAULTS:
        return jsonify({"error": f"unknown fault, choose one of {list(FAULTS)}"}), 400
    with lock:
        state["active_fault"] = name
        state["fault_since"] = state["tick"]
        state["events"].append({"t": state["tick"], "event": f"INJECT {name}"})
    logging.warning("REST fault injection: %s - %s", name, FAULTS[name])
    return jsonify({"injected": name, "description": FAULTS[name]})


def clear():
    with lock:
        state["active_fault"] = None
        state["events"].append({"t": state["tick"], "event": "CLEAR"})
    logging.warning("REST fault cleared")
    return jsonify({"cleared": True})


@app.route("/status")
def status():
    with lock:
        return jsonify({k: state[k] for k in ("active_fault", "contactor", "bms_status", "tick")})


def start_flask(port):
    app.run(debug=False, port=port, host="0.0.0.0", use_reloader=False)


def run(duration, step, out_dir, port, scripted):
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "vhil_log.csv")
    threading.Thread(target=start_flask, args=(port,), daemon=True).start()
    logging.info("Dashboard + fault API on http://localhost:%d/demo", port)

    battery = BatterySimulator(NUM_CELLS)
    bms = BMS(NUM_CELLS)
    can = CANBus()

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time", "v1", "v2", "v3", "v4", "temperature", "soc", "fault", "bms_status", "contactor"])

    for t in range(0, duration, step):
        with lock:
            state["tick"] = t
            fault = state["active_fault"]
            since = state["fault_since"]
        if scripted and t in scripted:
            if scripted[t] == "clear":
                clear_fault_scripted()
            else:
                inject_scripted(scripted[t], t)
            with lock:
                fault, since = state["active_fault"], state["fault_since"]

        voltages = battery.simulate_cell_voltage()
        temperature = float(battery.simulate_temperature())
        soc = battery.update_soc(drain=0.4)
        if fault:
            voltages, temperature = apply_fault(voltages, temperature, fault, t - since)

        # plant -> CAN bus -> BMS
        can.send(msg_id=BATTERY_STATUS_ID, data=encode_battery_status(voltages, temperature, soc))
        msg = can.receive()
        rx_v, rx_t, rx_soc = decode_battery_status(msg[1])

        safe, _balanced = bms.run_control_logic(list(rx_v), rx_t)
        spread = max(rx_v) - min(rx_v)
        if not safe:
            bms_status = "FAULT_OVERTEMP" if rx_t > TEMP_LIMIT else "FAULT_OVERVOLTAGE"
            contactor = "OPEN"
        elif spread > 0.2:
            bms_status, contactor = "WARN_IMBALANCE", "CLOSED"
        else:
            bms_status, contactor = "OK", "CLOSED"
        if bms_status != "OK":
            can.send(msg_id=FAULT_STATUS_ID, data={"status": bms_status, "contactor": contactor})
            fmsg = can.receive()
            print(f"\033[31m[CAN 0x{fmsg[0]:03X}]\033[0m t={t:>3}s  {fmsg[1]}")

        tag = f"\033[33m<-- {fault}\033[0m" if fault else ""
        print(CAN_TERM_FMT.format(id=msg[0], t=t, v=", ".join(f"{v:.2f}" for v in rx_v), temp=rx_t, soc=rx_soc, tag=tag), flush=True)

        with lock:
            state["bms_status"], state["contactor"] = bms_status, contactor
        battery_data["voltages"] = [round(v, 2) for v in rx_v]
        battery_data["temperature"] = round(rx_t, 2)
        battery_data["soc"] = round(rx_soc, 2)
        battery_data["bms_status"] = bms_status
        battery_data["contactor"] = contactor
        battery_data["active_fault"] = fault or "none"

        with open(csv_path, "a", newline="") as f:
            csv.writer(f).writerow([t, *[f"{v:.3f}" for v in rx_v], f"{rx_t:.2f}", f"{rx_soc:.2f}", fault or "", bms_status, contactor])
        time.sleep(step)

    logging.info("Run complete. CSV: %s", csv_path)


def inject_scripted(name, t):
    with lock:
        state["active_fault"], state["fault_since"] = name, t
        state["events"].append({"t": t, "event": f"INJECT {name}"})
    logging.warning("Scripted fault injection: %s - %s", name, FAULTS[name])


def clear_fault_scripted():
    with lock:
        state["active_fault"] = None
    logging.warning("Scripted fault cleared")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duration", type=int, default=90)
    p.add_argument("--step", type=int, default=1)
    p.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "out"))
    p.add_argument("--port", type=int, default=5001)
    p.add_argument("--scripted", action="store_true",
                   help="auto-inject overvoltage@10s, clear@20s, imbalance@30s, clear@40s, overtemp@50s, clear@60s")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    script = {10: "overvoltage", 20: "clear", 30: "imbalance", 40: "clear", 50: "overtemp", 60: "clear"} if a.scripted else {}
    run(a.duration, a.step, a.out, a.port, script)
