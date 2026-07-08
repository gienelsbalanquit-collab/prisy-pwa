#!/usr/bin/env python3
"""
Update Prisynchracy Command Center dashboard dates to be fully dynamic.
Run once — after this the dashboard auto-computes Mon/Wed/Fri of the current week.
"""
import re

HTML_PATH = '/Users/gienel/Downloads/Claude Work Monitor/Prisynchracy PWA/index.html'
JSON_PATH = '/Users/gienel/Downloads/Claude Work Monitor/Prisynchracy PWA/linkedin_prospects.json'

# ─── Update index.html ───────────────────────────────────────────────────────

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Insert computeWindow() + const W before the state declarations
compute_fn = """\n// ── AUTO-COMPUTE OUTREACH WINDOW (Mon/Wed/Fri of current week) ──────────────
function computeWindow() {
  const now = new Date();
  const dow = now.getDay(); // 0=Sun,1=Mon,...,6=Sat
  const diff = dow === 0 ? 1 : (1 - dow);  // days to Monday
  const mon = new Date(now); mon.setDate(now.getDate() + diff);
  const wed = new Date(mon); wed.setDate(mon.getDate() + 2);
  const fri = new Date(mon); fri.setDate(mon.getDate() + 4);
  const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const fmt  = d => DAYS[d.getDay()] + ' · ' + MONTHS[d.getMonth()] + ' ' + d.getDate();
  const fmtS = d => MONTHS[d.getMonth()] + ' ' + d.getDate();
  return {
    d1: fmt(mon),  d1s: fmtS(mon),
    d2: fmt(wed),  d2s: fmtS(wed),
    d3: fmt(fri),  d3s: fmtS(fri),
    range: MONTHS[mon.getMonth()] + ' ' + mon.getDate() + '\\u2013' + fri.getDate()
  };
}
const W = computeWindow();
"""

if 'computeWindow' not in html:
    html = html.replace("let state = JSON.parse", compute_fn + "let state = JSON.parse", 1)

# 2. Section header — add ID so JS can update it
html = html.replace(
    '<span class="section-title">Top 10 · May 3–7</span>',
    '<span class="section-title" id="windowTitle">Top 10</span>'
)

# 3. D1 Mission header — add ID
html = html.replace(
    '>🔥 D1 Mission — Sat May 3<',
    ' id="d1MissionLabel">🔥 D1 Mission<'
)

# 4. Settings panel dates — add IDs
html = html.replace(
    'style="color:var(--green)">Sat · May 3</span>',
    'style="color:var(--green)" id="settingsD1">–</span>'
)
html = html.replace(
    'style="color:var(--amber)">Mon · May 5</span>',
    'style="color:var(--amber)" id="settingsD2">–</span>'
)
html = html.replace(
    'style="color:var(--red)">Wed · May 7</span>',
    'style="color:var(--red)" id="settingsD3">–</span>'
)

# 5. nextDMLabel — use W dynamic dates
html = html.replace(
    "const nextDMLabel = !st.d2 ? 'D2 · Mon May 5' : 'D3 · Wed May 7';",
    "const nextDMLabel = !st.d2 ? `D2 · ${W.d2}` : `D3 · ${W.d3}`;"
)

# 6. Day pill dates inside template literal
html = html.replace('>D1<div class="day-pill-date">May 3</div></div>',
                    '>D1<div class="day-pill-date">${W.d1s}</div></div>')
html = html.replace('>D2<div class="day-pill-date">May 5</div></div>',
                    '>D2<div class="day-pill-date">${W.d2s}</div></div>')
html = html.replace('>D3<div class="day-pill-date">May 7</div></div>',
                    '>D3<div class="day-pill-date">${W.d3s}</div></div>')

# 7. Template section labels
html = html.replace('D2 · Insight DM · Mon May 5', 'D2 · Insight DM · ${W.d2}')
html = html.replace('D3 · ASK · Wed May 7',         'D3 · ASK · ${W.d3}')

# 8. All inline prospect plan d1/d2/d3 date strings  → dynamic W references
html = re.sub(r'd1:\{date:"[^"]*"', 'd1:{date:W.d1', html)
html = re.sub(r'd2:\{date:"[^"]*"', 'd2:{date:W.d2', html)
html = re.sub(r'd3:\{date:"[^"]*"', 'd3:{date:W.d3', html)

# 9. Inject date-label initialisation into DOMContentLoaded
init_snippet = """\n  // ── Set dynamic date labels ──
  (function(){
    const _W = computeWindow();
    const _set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
    _set('windowTitle',   'Top 10 · ' + _W.range);
    _set('d1MissionLabel','🔥 D1 Mission — ' + _W.d1);
    _set('settingsD1', _W.d1);
    _set('settingsD2', _W.d2);
    _set('settingsD3', _W.d3);
  })();\n"""

# Inject just before the dateBadge line in DOMContentLoaded
ANCHOR = "document.getElementById('dateBadge').textContent"
if ANCHOR in html and '// ── Set dynamic date labels' not in html:
    html = html.replace(ANCHOR, init_snippet + "  " + ANCHOR, 1)

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ index.html updated")

# ─── Update linkedin_prospects.json ──────────────────────────────────────────
import json
from datetime import date, timedelta

today = date.today()
dow = today.weekday()  # 0=Mon,...,6=Sun
mon = today - timedelta(days=dow)   # Monday of this week
wed = mon + timedelta(days=2)
fri = mon + timedelta(days=4)

DAYS   = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def fmt(d):
    return DAYS[d.weekday()] + ' · ' + MONTHS[d.month-1] + ' ' + str(d.day)

d1_str = fmt(mon)
d2_str = fmt(wed)
d3_str = fmt(fri)
range_str = MONTHS[mon.month-1] + ' ' + str(mon.day) + '–' + str(fri.day)

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['updated'] = str(today)
data['window']['start'] = d1_str
data['window']['end']   = d3_str

for p in data['prospects']:
    p['plan']['day_1']['date'] = d1_str
    p['plan']['day_2']['date'] = d2_str
    p['plan']['day_3']['date'] = d3_str

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ linkedin_prospects.json updated  (D1={d1_str}, D2={d2_str}, D3={d3_str})")
print(f"   Window: {range_str}")
