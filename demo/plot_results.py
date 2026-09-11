"""Plot SOC / cell voltages / temperature from the V_HIL CSV log with fault-injection markers."""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

V_LIMIT, T_LIMIT = 4.2, 60
COLORS = {"overvoltage": "#e0453a", "imbalance": "#f0a202", "overtemp": "#d9480f"}


def main(csv_path, png_path):
    rows = list(csv.DictReader(open(csv_path)))
    t = [int(r["time"]) for r in rows]
    cells = [[float(r[f"v{i}"]) for r in rows] for i in range(1, 5)]
    temp = [float(r["temperature"]) for r in rows]
    soc = [float(r["soc"]) for r in rows]
    faults = [r["fault"] for r in rows]
    open_ = [r["contactor"] == "OPEN" for r in rows]

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fig.suptitle("V_HIL Stage 5 - BMS response to injected faults (from vhil_log.csv)", fontsize=14)

    for i, c in enumerate(cells):
        axes[0].plot(t, c, lw=1.8, label=f"Cell {i+1}")
    axes[0].axhline(V_LIMIT, color="r", ls="--", lw=1, label="Limit 4.20 V")
    axes[0].set_ylabel("Cell voltage [V]")
    axes[0].set_ylim(3.2, 4.5)

    axes[1].plot(t, temp, color="#f0a202", lw=2, label="Pack temperature")
    axes[1].axhline(T_LIMIT, color="r", ls="--", lw=1, label="Limit 60 C")
    axes[1].set_ylabel("Temperature [C]")

    axes[2].plot(t, soc, color="#2a9d8f", lw=2, label="SOC")
    axes[2].fill_between(t, 0, soc, color="#2a9d8f", alpha=0.15)
    axes[2].set_ylabel("SOC [%]")
    axes[2].set_xlabel("time [s]")

    # fault windows + contactor-open windows
    seen = set()
    for ax in axes:
        start = None
        for i, f in enumerate(faults + [""]):
            if f and start is None:
                start, name = i, f
            elif start is not None and f != name:
                lbl = f"fault: {name}" if name not in seen else None
                seen.add(name)
                ax.axvspan(t[start], t[min(i, len(t) - 1)], color=COLORS.get(name, "grey"), alpha=0.18, label=lbl)
                start = None if not f else i
                name = f
        for i, o in enumerate(open_):
            if o:
                ax.axvline(t[i], color="k", alpha=0.25, lw=3)
        ax.grid(alpha=0.3)
    for i, o in enumerate(open_):
        if o:
            axes[0].plot([], [], color="k", alpha=0.35, lw=3, label="BMS contactor OPEN")
            break
    for ax in axes:
        ax.legend(loc="upper right", fontsize=8, ncol=3)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(png_path, dpi=130)
    print(f"wrote {png_path}  ({len(rows)} samples, {sum(open_)} s contactor-open, faults={sorted(seen)})")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "out")
    main(os.path.join(out, "vhil_log.csv"), os.path.join(out, "bms_fault_response.png"))
