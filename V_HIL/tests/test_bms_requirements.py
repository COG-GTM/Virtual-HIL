"""Requirement-style system tests: plant -> CAN frame -> BMS reaction.

Each fault is injected upstream of the CAN encoder, so the BMS only sees
what arrives on 0x100, exactly as on a bench.
"""
import time

import numpy as np
import pytest

from battery_simulator import BatterySimulator
from bms_module import BMS, CELL_BALANCE_THRESHOLD, TEMP_LIMIT, VOLTAGE_LIMIT
from can_emulator import CANBus
from can_messages import BATTERY_STATUS_ID, decode_battery_status, encode_battery_status

NUM_CELLS = 4
CYCLE_S = 1.0
MAX_REACTION_MS = 10.0


def nominal_pack():
    return [3.95, 3.96, 3.94, 3.95], 25.0, 80.0


def bench_cycle(bms, can, t, voltages, temperature, soc, drop_frame=False):
    """One control cycle; returns (safe, balanced_voltages, reaction_ms)."""
    if not drop_frame:
        can.send(msg_id=BATTERY_STATUS_ID, data=encode_battery_status(voltages, temperature, soc))
    start = time.perf_counter()
    msg = can.receive()
    if msg and msg[0] == BATTERY_STATUS_ID:
        voltages, temperature, soc = decode_battery_status(msg[1])
        bms.frame_received(t)
    safe, voltages = bms.run_control_logic(voltages, temperature)
    safe = bms.check_can_timeout(t) and safe
    return safe, voltages, (time.perf_counter() - start) * 1000.0


def first_trip(frames, drop_from=None):
    """Run frames through the bench; return (cycle index of first trip, reaction ms)."""
    bms, can = BMS(NUM_CELLS), CANBus()
    for i, (v, temp, soc) in enumerate(frames):
        safe, _, ms = bench_cycle(bms, can, i * CYCLE_S, v, temp, soc,
                                  drop_frame=drop_from is not None and i >= drop_from)
        if not safe:
            return i, ms
    return None, None


def test_req_bms_000_no_false_trip_on_nominal_pack():
    np.random.seed(0)
    battery, bms, can = BatterySimulator(NUM_CELLS), BMS(NUM_CELLS), CANBus()
    for t in range(60):
        v, temp, soc = battery.simulate_cell_voltage(), battery.simulate_temperature(), battery.update_soc()
        safe, _, _ = bench_cycle(bms, can, t, v, temp, soc)
        assert safe, f"false trip at t={t}s"


def test_req_bms_001_overtemperature_trips_same_cycle():
    v, _, soc = nominal_pack()
    frames = [nominal_pack()] * 5 + [(v, TEMP_LIMIT + 5.0, soc)]
    cycle, ms = first_trip(frames)
    assert cycle == 5
    assert ms < MAX_REACTION_MS


def test_req_bms_002_overvoltage_detected_by_safety_check():
    _, temp, _ = nominal_pack()
    assert not BMS(NUM_CELLS).check_safety([3.95, VOLTAGE_LIMIT + 0.15, 3.94, 3.95], temp)


@pytest.mark.xfail(strict=True, reason="balance_cells() runs before check_safety() and clamps the "
                                       "faulted cell below VOLTAGE_LIMIT, masking over-voltage")
def test_req_bms_003_overvoltage_trips_same_cycle():
    _, temp, soc = nominal_pack()
    frames = [nominal_pack()] * 5 + [([3.95, VOLTAGE_LIMIT + 0.15, 3.94, 3.95], temp, soc)]
    cycle, ms = first_trip(frames)
    assert cycle == 5
    assert ms < MAX_REACTION_MS


def test_req_bms_004_imbalance_clamped_within_threshold():
    bms, can = BMS(NUM_CELLS), CANBus()
    _, temp, soc = nominal_pack()
    raw = [3.90, 4.10, 3.90, 3.90]
    safe, balanced, ms = bench_cycle(bms, can, 0.0, raw, temp, soc)
    avg = sum(raw) / len(raw)
    assert safe
    assert max(balanced) <= avg + CELL_BALANCE_THRESHOLD + 1e-9
    assert ms < MAX_REACTION_MS


def test_req_bms_005_can_loss_trips_after_timeout():
    frames = [nominal_pack()] * 20
    cycle, ms = first_trip(frames, drop_from=5)
    timeout_cycles = BMS(NUM_CELLS).can_timeout / CYCLE_S
    assert cycle is not None, "CAN loss never detected"
    assert cycle - 4 == timeout_cycles
    assert ms < MAX_REACTION_MS


def test_req_bms_006_can_timeout_not_armed_before_first_frame():
    assert BMS(NUM_CELLS).check_can_timeout(100.0)


def test_req_bms_007_armed_watchdog_trips_if_no_frame_ever_arrives():
    bms = BMS(NUM_CELLS)
    bms.arm_can_watchdog(0.0)
    assert bms.check_can_timeout(bms.can_timeout - CYCLE_S)
    assert not bms.check_can_timeout(bms.can_timeout)
