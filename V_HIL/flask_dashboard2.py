# File: flask_dashboard2.py

from flask import Flask, render_template_string, jsonify, request
import threading

app = Flask(__name__)

battery_data = {
    "voltages": [],
    "temperature": 0.0,
    "soc": 0.0,
    "running": True,
    "history": {
        "voltages": [],
        "temperature": [],
        "soc": []
    }
}

@app.route("/")
def index():
    return render_template_string("""
    <html>
    <head>
        <title>Battery Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            canvas { max-width: 700px; margin-bottom: 30px; }
            button { margin: 10px; padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h1>Battery Dashboard</h1>
        <p>Voltages: <span id="voltages"></span></p>
        <p>Temperature: <span id="temperature"></span> °C</p>
        <p>State of Charge: <span id="soc"></span> %</p>

        <button onclick="toggleSimulation()">Start/Stop Simulation</button>

        <canvas id="voltageChart"></canvas>
        <canvas id="tempChart"></canvas>
        <canvas id="socChart"></canvas>

        <script>
            const voltageCtx = document.getElementById('voltageChart').getContext('2d');
            const tempCtx = document.getElementById('tempChart').getContext('2d');
            const socCtx = document.getElementById('socChart').getContext('2d');

            let voltageChart = new Chart(voltageCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Voltage', data: [] }] },
                options: { responsive: true }
            });

            let tempChart = new Chart(tempCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Temperature (°C)', data: [] }] },
                options: { responsive: true }
            });

            let socChart = new Chart(socCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'State of Charge (%)', data: [] }] },
                options: { responsive: true }
            });

            function updateCharts(data) {
                const t = new Date().toLocaleTimeString();
                voltageChart.data.labels.push(t);
                voltageChart.data.datasets[0].data.push(data.voltages.reduce((a, b) => a + b, 0) / data.voltages.length);

                tempChart.data.labels.push(t);
                tempChart.data.datasets[0].data.push(data.temperature);

                socChart.data.labels.push(t);
                socChart.data.datasets[0].data.push(data.soc);

                voltageChart.update();
                tempChart.update();
                socChart.update();
            }

            function toggleSimulation() {
                fetch('/toggle', { method: 'POST' });
            }

            setInterval(() => {
                fetch('/data').then(r => r.json()).then(data => {
                    document.getElementById('voltages').textContent = data.voltages.join(', ');
                    document.getElementById('temperature').textContent = data.temperature;
                    document.getElementById('soc').textContent = data.soc;
                    if (data.running) updateCharts(data);
                });
            }, 1000);
        </script>
    </body>
    </html>
    """)

@app.route("/data")
def data():
    return jsonify(battery_data)

@app.route("/toggle", methods=["POST"])
def toggle():
    battery_data["running"] = not battery_data["running"]
    return ('', 204)

def start_flask():
    app.run(debug=False, port=5001)