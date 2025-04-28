import json
import math
from datetime import datetime, timedelta
from skyfield.api import load, Topos, Star
from skyfield.almanac import moon_phase, risings_and_settings, find_discrete

# === Deep-sky catalog as in your original code ===
DEEP_SKY_CATALOG = [
    {'name': 'M1', 'ra_h': 5.575, 'dec_deg': 22.014, 'mag': 8.4},
    {'name': 'M31', 'ra_h': 0.712, 'dec_deg': 41.269, 'mag': 3.4},
    {'name': 'M42', 'ra_h': 5.591, 'dec_deg': -5.391, 'mag': 4.0},
    {'name': 'M45', 'ra_h': 3.792, 'dec_deg': 24.117, 'mag': 1.6},
    {'name': 'M13', 'ra_h': 16.7, 'dec_deg': 36.467, 'mag': 5.8},
    {'name': 'NGC7000', 'ra_h': 20.972, 'dec_deg': 44.333, 'mag': 4.0},
]

def astronomy_forecast_ui(aperture, bortle, latitude, longitude, observation_date):
    try:
        date = datetime.strptime(observation_date, '%Y-%m-%d')
        ts = load.timescale()
        eph = load('de421.bsp')
        topos = Topos(latitude_degrees=latitude, longitude_degrees=longitude)
        observer = eph['earth'] + topos

        t0 = ts.utc(date.year, date.month, date.day)
        t1 = ts.utc(date.year, date.month, date.day + 1)

        aperture_mm = aperture * 25.4
        limiting_mag = 7.5 + 5 * math.log10(aperture_mm) - (bortle * 0.2)

        moon_angle = moon_phase(eph, t0).degrees

        planet_keys = {
            'mercury': 'mercury barycenter',
            'venus': 'venus barycenter',
            'mars': 'mars barycenter',
            'jupiter': 'jupiter barycenter',
            'saturn': 'saturn barycenter'
        }

        visible_objects = []

        for name, key in planet_keys.items():
            planet = eph[key]
            astrom = observer.at(t0).observe(planet).apparent()
            alt, _, _ = astrom.altaz()
            if alt.degrees > 15:
                visible_objects.append({
                    'name': name.capitalize(),
                    'type': 'Planet',
                    'altitude_deg': round(alt.degrees, 1)
                })

        for obj in DEEP_SKY_CATALOG:
            star = Star(ra_hours=obj['ra_h'], dec_degrees=obj['dec_deg'])
            astrom = observer.at(t0).observe(star).apparent()
            alt, _, _ = astrom.altaz()
            if alt.degrees > 15 and obj['mag'] <= limiting_mag:
                visible_objects.append({
                    'name': obj['name'],
                    'type': 'DeepSky',
                    'altitude_deg': round(alt.degrees, 1)
                })

        f_moon = risings_and_settings(eph, eph['moon'], topos)
        times, events = find_discrete(t0, t1, f_moon)
        moon_events = [{'event': 'Rise' if ev else 'Set', 'time_utc': ti.utc_iso()} for ti, ev in zip(times, events)]

        result = {
            "Aperture": aperture,
            "Bortle Scale": bortle,
            "Latitude": latitude,
            "Longitude": longitude,
            "Observation Date": date.strftime('%d %B %Y'),
            "Limiting Magnitude": round(limiting_mag, 2),
            "Moon Phase Angle (degrees)": round(moon_angle, 1),
            "Moon Events": moon_events,
            "Visible Objects": visible_objects
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
