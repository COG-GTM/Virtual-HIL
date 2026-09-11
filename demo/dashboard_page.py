"""Adds a /demo route to the existing Flask dashboard app: per-cell voltage bars, BMS status
banner, contactor state and one-click REST fault-injection buttons on top of the Chart.js trends."""
from flask import render_template_string

PAGE = """
<!doctype html>
<html>
<head>
  <title>V_HIL - BMS Validation Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: -apple-system, Segoe UI, Arial, sans-serif; margin: 0; background:#0f1419; color:#e6e6e6; }
    header { padding: 14px 28px; background:#161c24; border-bottom:1px solid #263040; display:flex; align-items:center; gap:24px; }
    header h1 { font-size: 20px; margin:0; }
    .banner { padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 18px; letter-spacing: .5px; }
    .OK { background:#1f6f43; } .WARN_IMBALANCE { background:#a86a00; }
    .FAULT_OVERTEMP, .FAULT_OVERVOLTAGE { background:#b3261e; animation: blink 1s steps(2) infinite; }
    @keyframes blink { to { opacity: .55; } }
    main { display:grid; grid-template-columns: 340px 1fr; gap: 20px; padding: 20px 28px; }
    .card { background:#161c24; border:1px solid #263040; border-radius:8px; padding:16px; margin-bottom: 16px; }
    .card h2 { margin:0 0 12px; font-size:14px; text-transform: uppercase; color:#8fa3b8; letter-spacing: 1px; }
    .kv { display:flex; justify-content:space-between; padding:4px 0; font-size:15px; }
    .kv b { font-variant-numeric: tabular-nums; }
    .cell { margin: 6px 0; }
    .cell .bar { height: 18px; background:#263040; border-radius: 4px; overflow:hidden; }
    .cell .fill { height:100%; background:#3fa7d6; transition: width .4s; }
    .cell .fill.hi { background:#e0453a; } .cell .fill.lo { background:#f0a202; }
    .cell label { display:flex; justify-content:space-between; font-size:13px; color:#b8c4d0; }
    button { border:0; border-radius:6px; padding:10px 14px; font-weight:600; cursor:pointer; margin: 4px 4px 4px 0; color:#fff; }
    .b-ov { background:#b3261e; } .b-ot { background:#d9480f; } .b-im { background:#a86a00; } .b-cl { background:#2f6f8f; }
    canvas { background:#11171f; border-radius:6px; }
    .charts { display:grid; grid-template-columns: 1fr 1fr; gap:16px; }
    .charts .card:first-child { grid-column: 1 / span 2; }
    .contactor { font-weight:700; } .contactor.OPEN { color:#ff6b6b; } .contactor.CLOSED { color:#5ad47a; }
  </style>
</head>
<body>
<header>
  <h1>V_HIL &mdash; Virtual HIL BMS Validation</h1>
  <div id="banner" class="banner OK">BMS: OK</div>
  <div>Contactor: <span id="contactor" class="contactor CLOSED">CLOSED</span></div>
  <div>Active fault: <span id="fault">none</span></div>
  <div style="margin-left:auto; color:#8fa3b8">t = <span id="tick">0</span> s</div>
</header>
<main>
  <section>
    <div class="card"><h2>Fault injection (REST /fault/&lt;name&gt;)</h2>
      <button class="b-ov" onclick="inject('overvoltage')">Over-voltage (cell 2)</button>
      <button class="b-im" onclick="inject('imbalance')">Cell imbalance (cell 4)</button>
      <button class="b-ot" onclick="inject('overtemp')">Over-temperature</button>
      <button class="b-cl" onclick="inject('clear')">Clear fault</button>
    </div>
    <div class="card"><h2>Cell voltages (as received on CAN 0x100)</h2><div id="cells"></div></div>
    <div class="card"><h2>Pack</h2>
      <div class="kv"><span>Temperature</span><b><span id="temperature">-</span> &deg;C</b></div>
      <div class="kv"><span>State of charge</span><b><span id="soc">-</span> %</b></div>
      <div class="kv"><span>Limits</span><b>4.20 V / 60 &deg;C</b></div>
    </div>
  </section>
  <section class="charts">
    <div class="card"><h2>Cell voltages [V]</h2><canvas id="vChart" height="110"></canvas></div>
    <div class="card"><h2>Temperature [&deg;C]</h2><canvas id="tChart" height="120"></canvas></div>
    <div class="card"><h2>State of charge [%]</h2><canvas id="sChart" height="120"></canvas></div>
  </section>
</main>
<script>
const colors = ['#3fa7d6','#5ad47a','#f0a202','#c678dd'];
const mk = (id, datasets, extra={}) => new Chart(document.getElementById(id), {
  type:'line', data:{labels:[], datasets},
  options:{animation:false, responsive:true, plugins:{legend:{labels:{color:'#b8c4d0'}}},
    scales:{x:{ticks:{color:'#8fa3b8'}, grid:{color:'#1f2a36'}}, y:{ticks:{color:'#8fa3b8'}, grid:{color:'#1f2a36'}, ...extra}}}});
const vChart = mk('vChart', [0,1,2,3].map(i => ({label:'Cell '+(i+1), data:[], borderColor:colors[i], pointRadius:0, borderWidth:2}))
  .concat([{label:'Limit 4.2 V', data:[], borderColor:'#ff6b6b', borderDash:[6,4], pointRadius:0, borderWidth:1}]), {min:3.2, max:4.5});
const tChart = mk('tChart', [{label:'Pack temp', data:[], borderColor:'#f0a202', pointRadius:0, borderWidth:2},
  {label:'Limit 60 C', data:[], borderColor:'#ff6b6b', borderDash:[6,4], pointRadius:0, borderWidth:1}], {min:0, max:80});
const sChart = mk('sChart', [{label:'SOC', data:[], borderColor:'#5ad47a', pointRadius:0, borderWidth:2, fill:true, backgroundColor:'rgba(90,212,122,.15)'}], {min:0, max:100});
const MAX = 90; let lastTick = -1;
function push(ch, label, vals){ ch.data.labels.push(label); vals.forEach((v,i)=>ch.data.datasets[i].data.push(v));
  if (ch.data.labels.length > MAX){ ch.data.labels.shift(); ch.data.datasets.forEach(d=>d.data.shift()); } ch.update(); }
function inject(n){ fetch('/fault/'+n, {method:'POST'}); }
setInterval(async () => {
  const d = await (await fetch('/data')).json();
  const s = await (await fetch('/status')).json();
  if (s.tick === lastTick) return; lastTick = s.tick;
  document.getElementById('tick').textContent = s.tick;
  document.getElementById('temperature').textContent = d.temperature;
  document.getElementById('soc').textContent = d.soc;
  document.getElementById('fault').textContent = d.active_fault || 'none';
  const b = document.getElementById('banner'); b.className = 'banner ' + s.bms_status; b.textContent = 'BMS: ' + s.bms_status;
  const c = document.getElementById('contactor'); c.className = 'contactor ' + s.contactor; c.textContent = s.contactor;
  document.getElementById('cells').innerHTML = d.voltages.map((v,i) => {
    const pct = Math.max(0, Math.min(100, (v-3.0)/(4.5-3.0)*100));
    const cls = v > 4.2 ? 'hi' : (v < 3.4 ? 'lo' : '');
    return `<div class="cell"><label><span>Cell ${i+1}</span><span>${v.toFixed(2)} V</span></label><div class="bar"><div class="fill ${cls}" style="width:${pct}%"></div></div></div>`;
  }).join('');
  push(vChart, s.tick, [...d.voltages, 4.2]); push(tChart, s.tick, [d.temperature, 60]); push(sChart, s.tick, [d.soc]);
}, 500);
</script>
</body>
</html>
"""


def register(app):
    @app.route("/demo")
    def demo_page():
        return render_template_string(PAGE)
