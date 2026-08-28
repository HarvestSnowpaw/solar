import urllib.request
import json
import datetime
import sys

# 1. Fetch Planetary K-Index from NOAA SWPC
kp = 2.0
try:
    url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        # Strip header row, parse latest numerical Kp
        rows = [r for r in data if len(r) > 1 and str(r[1]).replace(".", "", 1).isdigit()]
        if rows:
            kp = float(rows[-1][1])
except Exception as e:
    print(f"Kp fetch warning: {e}", file=sys.stderr)

# 2. Fetch 10.7cm Solar Flux Index (SFI) from NOAA SWPC
sfi = 145
try:
    url = "https://services.swpc.noaa.gov/products/10cm-flux-30-day.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        # Strip header row, parse latest numerical SFI
        rows = [r for r in data if len(r) > 1 and str(r[1]).replace(".", "", 1).isdigit()]
        if rows:
            sfi = round(float(rows[-1][1]))
except Exception as e:
    print(f"SFI fetch warning: {e}", file=sys.stderr)

# 3. Derive Indices & Status
a_val = round((kp ** 1.8) * 1.5)

if kp >= 5:
    geo_val = "Storm (G1+)"
    geo_color = "#b91c1c"
    k_color = "#b91c1c"
    k_sub = "Storm Level"
elif kp >= 4:
    geo_val = "Unsettled"
    geo_color = "#b45309"
    k_color = "#b45309"
    k_sub = "Unsettled"
elif kp >= 3:
    geo_val = "Active"
    geo_color = "#b45309"
    k_color = "#b45309"
    k_sub = "Active"
else:
    geo_val = "Quiet"
    geo_color = "#15803d"
    k_color = "#15803d"
    k_sub = "Calm Geomagnetic"

geo_sub = f"Kp = {kp:.1f}"

if sfi >= 130:
    sfi_sub = '<span style="color:#15803d">High Ionization</span>'
elif sfi >= 90:
    sfi_sub = '<span style="color:#b45309">Moderate</span>'
else:
    sfi_sub = '<span style="color:#b91c1c">Low</span>'

a_sub = "Low Absorption" if a_val < 10 else ("Moderate" if a_val < 20 else "High Absorption")

# 4. Propagation Calculation Model
def get_rating(band, is_day):
    if kp >= 5:
        return "poor"
    if band in ["80m", "40m"]:
        if is_day:
            return "poor" if kp >= 3 else "fair"
        else:
            return "good" if kp <= 3 else "fair"
    if band in ["30m", "20m"]:
        if kp >= 4:
            return "poor"
        return "good" if sfi >= 90 else "fair"
    if band in ["17m", "15m"]:
        if not is_day:
            return "poor"
        if sfi >= 120 and kp <= 3:
            return "good"
        return "fair" if sfi >= 90 else "poor"
    if band in ["12m", "10m"]:
        if not is_day:
            return "poor"
        if sfi >= 140 and kp <= 3:
            return "good"
        return "fair" if sfi >= 105 and kp <= 4 else "poor"
    return "fair"

bands = ["80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m"]
rows = []
for b in bands:
    d_rate = get_rating(b, True)
    n_rate = get_rating(b, False)
    row_html = (
        f'        <tr>'
        f'<td style="font-weight:600; color:var(--text-main);">{b}</td>'
        f'<td><span class="pill pill-{d_rate}">{d_rate.title()}</span></td>'
        f'<td><span class="pill pill-{n_rate}">{n_rate.title()}</span></td>'
        f'</tr>'
    )
    rows.append(row_html)

table_rows_str = "\n".join(rows)
now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")

# 5. Read template.html and generate index.html
with open("template.html", "r", encoding="utf-8") as f:
    template_content = f.read()

output_html = (
    template_content
    .replace("{{SFI_VAL}}", str(sfi))
    .replace("{{SFI_SUB}}", sfi_sub)
    .replace("{{K_VAL}}", f"{kp:.1f}")
    .replace("{{K_COLOR}}", k_color)
    .replace("{{K_SUB}}", k_sub)
    .replace("{{A_VAL}}", str(a_val))
    .replace("{{A_SUB}}", a_sub)
    .replace("{{GEO_VAL}}", geo_val)
    .replace("{{GEO_COLOR}}", geo_color)
    .replace("{{GEO_SUB}}", geo_sub)
    .replace("{{TABLE_ROWS}}", table_rows_str)
    .replace("{{LAST_UPDATED}}", now_str)
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(output_html)

print(f"Successfully generated index.html: SFI={sfi}, Kp={kp}, Ap={a_val}")
