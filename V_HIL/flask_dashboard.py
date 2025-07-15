
# File: flask_dashboard.py

from flask import Flask, render_template_string, jsonify
import threading

app = Flask(__name__)

battery_data = {
    "voltages": [],
    "temperature": 0.0,
    "soc": 0.0
}

@app.route("/")
def index():
    return render_template_string("""
    <html>
    <head><title>Battery Dashboard</title></head>
    <body>
    <h1>Battery Dashboard</h1>
    <div id="content"></div>
    <script>
        setInterval(() => {
            fetch('/data').then(r => r.json()).then(data => {
                document.getElementById('content').innerHTML =
                    '<p>Voltages: ' + data.voltages.join(', ') + '</p>' +
                    '<p>Temperature: ' + data.temperature + ' °C</p>' +
                    '<p>State of Charge: ' + data.soc + ' %</p>';
            });
        }, 1000);
    </script>
    </body>
    </html>
    """)

@app.route("/data")
def data():
    return jsonify(battery_data)

def start_flask():
    app.run(debug=False, port=5001)
