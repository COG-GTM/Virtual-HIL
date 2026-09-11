# Stage 5 — Virtual HIL System Validation (BMS) — Talk Track

*(~140 words, < 3 min demo)*

This is full-system validation without a battery pack. The battery plant model streams
cell voltages, temperature and SOC over an emulated CAN bus; the BMS only ever sees those
CAN frames — exactly as it would on a real HIL bench.

Now we inject faults you could never safely inject on hardware. Over-voltage: cell 2 driven
to 4.35 volts. The BMS trips, opens the contactor, and publishes a fault frame on CAN 0x101.
Cell imbalance: a weak cell sags 400 millivolts — the BMS flags it but keeps the pack online.
Over-temperature: coolant loss, the pack ramps past 60 degrees, contactor opens again.

Everything is logged to CSV and plotted with the fault windows overlaid — that is our
evidence pack.

One more thing: this bench caught a real BMS defect. Cell balancing ran *before* the safety
check, so balancing masked the over-voltage. Fixed, re-run, verified.

## What you're seeing
- Live dashboard (`/demo`): per-cell bars, pack temperature, SOC trends, BMS status banner, contactor state
- REST fault injection (`POST /fault/overvoltage|imbalance|overtemp|clear`) — buttons or `curl`
- Terminal: decoded CAN frames — `0x100` battery status every tick, `0x101` fault status when the BMS trips
- `demo/out/bms_fault_response.png`: SOC / cell voltages / temperature from the CSV log with fault + contactor-open markers
- Real defect found and fixed in `bms_module.py` (safety check now precedes balancing)

## Hand-off
Stage 6 takes these same fault scenarios and the CSV evidence into an automated test, diagnostics and release-gate pipeline (Virtual-HIL-Framework).
