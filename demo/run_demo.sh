#!/usr/bin/env bash
# Stage 5 demo entrypoint: battery model -> CAN -> BMS -> dashboard/CSV, with scripted REST fault injection.
# Usage: demo/run_demo.sh [--interactive]   (interactive = no scripted faults, use dashboard buttons / curl)
set -euo pipefail
cd "$(dirname "$0")"
OUT="$PWD/out"; mkdir -p "$OUT"
PORT="${PORT:-5001}"
DURATION="${DURATION:-75}"

python3 -c "import flask, numpy, matplotlib" 2>/dev/null || pip install -q flask numpy matplotlib

if [[ "${1:-}" == "--interactive" ]]; then
  echo ">> Interactive mode. Dashboard: http://localhost:$PORT/demo"
  echo ">> Inject:  curl -X POST localhost:$PORT/fault/{overvoltage|imbalance|overtemp|clear}"
  python3 vhil_demo.py --duration "$DURATION" --port "$PORT" --out "$OUT" | tee "$OUT/can_terminal.log"
else
  echo ">> Scripted run ($DURATION s): overvoltage@10s, imbalance@30s, overtemp@50s. Dashboard: http://localhost:$PORT/demo"
  python3 vhil_demo.py --scripted --duration "$DURATION" --port "$PORT" --out "$OUT" | tee "$OUT/can_terminal.log"
fi

python3 plot_results.py "$OUT"
sed 's/\x1b\[[0-9;]*m//g' "$OUT/can_terminal.log" > "$OUT/can_terminal.txt"
echo ">> Artifacts in $OUT:"; ls -1 "$OUT"
