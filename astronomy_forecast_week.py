# astronomy_forecast.py
# Extended version: includes weather forecast, expanded visible objects (planets, Messier & NGC), and PDF report generation

from skyfield.api import load, Topos, utc, Star
from skyfield.almanac import moon_phase, risings_and_settings, find_discrete
from datetime import datetime, timedelta
import math, json
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ========== CONFIGURATION ============
OPENWEATHERMAP_API_KEY = '94b5332efe0e089c411f03630dac8e33'  # replace with your key
WEATHER_LAT_PARAM = 'lat'
WEATHER_LON_PARAM = 'lon'
WEATHER_EXCLUDE = 'minutely,daily,alerts'

# A small catalog of deep-sky objects: add more as needed or load from file
DEEP_SKY_CATALOG = [
    {'name': 'M1', 'ra_h': 5.575, 'dec_deg': 22.014, 'mag': 8.4},    # Crab Nebula
    {'name': 'M3', 'ra_h': 13.703, 'dec_deg': 28.383, 'mag': 6.2},   # Globular Cluster
    {'name': 'M4', 'ra_h': 16.392, 'dec_deg': -26.525, 'mag': 5.6},  # Globular Cluster
    {'name': 'M5', 'ra_h': 15.309, 'dec_deg': 2.081, 'mag': 5.6},    # Globular Cluster
    {'name': 'M6', 'ra_h': 17.667, 'dec_deg': -32.217, 'mag': 4.2},  # Butterfly Cluster
    {'name': 'M7', 'ra_h': 17.897, 'dec_deg': -34.8, 'mag': 3.3},    # Ptolemy's Cluster
    {'name': 'M8', 'ra_h': 18.05, 'dec_deg': -24.383, 'mag': 6.0},   # Lagoon Nebula
    {'name': 'M13', 'ra_h': 16.7, 'dec_deg': 36.467, 'mag': 5.8},    # Hercules Cluster
    {'name': 'M16', 'ra_h': 18.313, 'dec_deg': -13.783, 'mag': 6.0}, # Eagle Nebula
    {'name': 'M17', 'ra_h': 18.367, 'dec_deg': -16.183, 'mag': 6.0}, # Omega Nebula
    {'name': 'M20', 'ra_h': 18.267, 'dec_deg': -23.017, 'mag': 6.3}, # Trifid Nebula
    {'name': 'M27', 'ra_h': 19.983, 'dec_deg': 22.717, 'mag': 7.4},  # Dumbbell Nebula
    {'name': 'M31', 'ra_h': 0.712, 'dec_deg': 41.269, 'mag': 3.4},   # Andromeda Galaxy
    {'name': 'M42', 'ra_h': 5.591, 'dec_deg': -5.391, 'mag': 4.0},   # Orion Nebula
    {'name': 'M45', 'ra_h': 3.792, 'dec_deg': 24.117, 'mag': 1.6},   # Pleiades
    {'name': 'M51', 'ra_h': 13.5, 'dec_deg': 47.2, 'mag': 8.4},      # Whirlpool Galaxy
    {'name': 'M57', 'ra_h': 18.887, 'dec_deg': 33.033, 'mag': 8.8},  # Ring Nebula
    {'name': 'M63', 'ra_h': 13.25, 'dec_deg': 42.033, 'mag': 8.6},   # Sunflower Galaxy
    {'name': 'M81', 'ra_h': 9.933, 'dec_deg': 69.067, 'mag': 6.9},   # Bode's Galaxy
    {'name': 'M82', 'ra_h': 9.933, 'dec_deg': 69.683, 'mag': 8.4},   # Cigar Galaxy
    {'name': 'M104', 'ra_h': 12.7, 'dec_deg': -11.617, 'mag': 8.0},  # Sombrero Galaxy
    {'name': 'NGC7000', 'ra_h': 20.972, 'dec_deg': 44.333, 'mag': 4.0},  # North America Nebula
]



# def get_weather_forecast(lat, lon):
#     url = 'https://api.openweathermap.org/data/2.5/onecall'
#     params = {
#         'appid': OPENWEATHERMAP_API_KEY,
#         'lat': lat,
#         'lon': lon,
#         'exclude': 'minutely,daily,alerts',
#         'units': 'metric'
#     }
#     resp = requests.get(url, params=params)
#     data = resp.json()
#     print(json.dumps(data, indent=2))  # Add this line to inspect the response
#     hourly = []
#     for hour in data.get('hourly', [])[:24]:
#         hourly.append({
#             'time_utc': datetime.utcfromtimestamp(hour['dt']).isoformat() + 'Z',
#             'temp_c': hour['temp'],
#             'clouds_pct': hour['clouds'],
#             'wind_mps': hour['wind_speed'],
#             'humidity_pct': hour['humidity']
#         })
#     return hourly



def astronomy_forecast(aperture_in_inches, bortle_scale, latitude, longitude):
    """
    Extended astronomy forecast including:
      • Limiting magnitude
      • Visible objects (planets + deep-sky)
      • Moon phase
      • Moonrise/moonset events
      • Weather forecast
    """
def astronomy_forecast(aperture_in_inches, bortle_scale, latitude, longitude, date):
    # Load ephemeris and timescale
    ts = load.timescale()
    eph = load('de421.bsp')

    # Observer location
    topos = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
    observer = eph['earth'] + topos

    # Time window: from the specified date to the next day
    t0 = ts.utc(date.year, date.month, date.day)
    t1 = ts.utc(date.year, date.month, date.day + 1)

    # 4. Limiting magnitude calculation
    aperture_mm = aperture_in_inches * 25.4
    limiting_mag = 7.5 + 5 * math.log10(aperture_mm) - (bortle_scale * 0.2)

    # 5. Moon phase
    mp_angle = moon_phase(eph, t0)

    # 6. Visible planets
    planet_keys = {
        'mercury': 'mercury barycenter',
        'venus': 'venus barycenter',
        'mars': 'mars barycenter',
        'jupiter': 'jupiter barycenter',
        'saturn': 'saturn barycenter'
    }
    visible = []
    for name, key in planet_keys.items():
        planet = eph[key]
        astrom = observer.at(t0).observe(planet).apparent()
        alt, az, dist = astrom.altaz()
        if alt.degrees > 15:
            visible.append({'name': name.capitalize(), 'type': 'Planet', 'alt_deg': round(alt.degrees,1)})

    # 7. Visible deep-sky objects
    for obj in DEEP_SKY_CATALOG:
        # create a Star object from RA/Dec
        star = Star(ra_hours=obj['ra_h'], dec_degrees=obj['dec_deg'])
        astrom = observer.at(t0).observe(star).apparent()
        alt, az, dist = astrom.altaz()
        # include object if above horizon and within limiting magnitude
        if alt.degrees > 15 and obj['mag'] <= limiting_mag:
            visible.append({'name': obj['name'], 'type': 'DeepSky', 'alt_deg': round(alt.degrees,1)})

    # 8. Moonrise/moonset
    f_moon = risings_and_settings(eph, eph['moon'], topos)
    times, events = find_discrete(t0, t1, f_moon)
    moon_events = []
    for ti, ev in zip(times, events):
        moon_events.append({'event': 'Rise' if ev else 'Set', 'time_utc': ti.utc_iso()})

    # 9. Weather forecast
    # weather = get_weather_forecast(latitude, longitude)

    # 10. Compile results
    result = {
        'limiting_magnitude': round(limiting_mag, 2),
        'visible_objects': visible,
        'moon_phase_deg': round(mp_angle.degrees, 1),
        'moon_events': moon_events,
        # 'weather_hourly': weather
    }
    return result


def generate_pdf(reports, filename='stargazing_report1.pdf'):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 40

    for report_data in reports:
        c.setFont('Helvetica-Bold', 16)
        c.drawString(40, y, 'Stargazing Forecast Report')
        y -= 30
        c.setFont('Helvetica', 12)
        c.drawString(40, y, f"Date: {report_data['date'].strftime('%Y-%m-%d')}")
        y -= 20

        # Limiting magnitude
        c.drawString(40, y, f"Limiting Magnitude: {report_data['limiting_magnitude']}")
        y -= 20

        # Moon phase
        c.drawString(40, y, f"Moon Phase Angle: {report_data['moon_phase_deg']}°")
        y -= 20

        # Visible objects
        c.setFont('Helvetica-Bold', 14)
        c.drawString(40, y, 'Visible Objects:')
        y -= 20
        c.setFont('Helvetica', 12)
        for obj in report_data['visible_objects']:
            line = f"- {obj['name']} ({obj['type']}), Altitude: {obj.get('alt_deg','N/A')}°"
            c.drawString(50, y, line)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 40

        # Moon events
        c.setFont('Helvetica-Bold', 14)
        c.drawString(40, y, 'Moon Events:')
        y -= 20
        c.setFont('Helvetica', 12)
        for ev in report_data['moon_events']:
            line = f"- {ev['event']} at {ev['time_utc']}"
            c.drawString(50, y, line)
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 40

        # # Weather forecast
        # c.setFont('Helvetica-Bold', 14)
        # c.drawString(40, y, 'Hourly Weather:')
        # y -= 20
        # c.setFont('Helvetica', 12)
        # for w in report_data['weather_hourly']:
        #     line = f"- {w['time_utc']}: Temp {w['temp_c']}°C, Clouds {w['clouds_pct']}%, Wind {w['wind_mps']} m/s"
        #     c.drawString(50, y, line)
        #     y -= 15
        #     if y < 100:
        #         c.showPage()
        #         y = height - 40

        # Add a page break between days
        c.showPage()
        y = height - 40

    c.save()
    return filename


# Test run
if __name__ == '__main__':
    from datetime import datetime, timedelta

    # Pune example
    aperture = 10
    bortle = 4
    latitude = 18.516726
    longitude = 73.856255

    reports = []
    for i in range(7):
        date = datetime.utcnow().date() + timedelta(days=i)
        data = astronomy_forecast(aperture, bortle, latitude, longitude, date)
        data['date'] = date
        reports.append(data)

    pdf_file = generate_pdf(reports)
    print(f"Generated report PDF: {pdf_file}")
