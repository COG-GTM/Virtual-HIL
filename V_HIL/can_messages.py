
# File: can_messages.py

BATTERY_STATUS_ID = 0x100
FAULT_STATUS_ID = 0x101
COMMAND_ID = 0x102


def encode_battery_status(voltages, temperature, soc):
    return {
        "voltages": [round(v, 3) for v in voltages],
        "temperature": round(temperature, 2),
        "soc": round(soc, 2)
    }


def decode_battery_status(data):
    voltages = data.get("voltages", [])
    temperature = data.get("temperature", None)
    soc = data.get("soc", None)
    return voltages, temperature, soc

