#!/usr/bin/env python3
"""Crea dati FINTI nel formato API-Football per una demo (nessuna rete)."""
import os, json, random, datetime
import config

random.seed(7)
DATA = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA, exist_ok=True)

# profili di gioco per squadra: (corner medi, dev), (gol medi), prob_btts, cartellini medi
PROFILES = {
    505: dict(corn=11.5, goal=2.9, btts=.62, card=4.2),  # Inter offensiva
    489: dict(corn=10.2, goal=2.7, btts=.58, card=4.6),
    496: dict(corn=9.0,  goal=2.3, btts=.48, card=4.8),   # Juve difensiva
    492: dict(corn=11.0, goal=2.8, btts=.60, card=4.0),
    497: dict(corn=10.5, goal=2.6, btts=.55, card=5.2),   # Roma cartellini
    487: dict(corn=9.8,  goal=2.5, btts=.53, card=4.9),
    499: dict(corn=12.3, goal=3.2, btts=.66, card=3.8),   # Atalanta iper-offensiva
    502: dict(corn=10.0, goal=2.6, btts=.57, card=4.4),
}
NAMES = {v: k for k, v in config.TEAMS.items()}
fid_counter = 900000
fixtures, stats = {}, {}


def pois(mean):
    # approssimazione: somma di due half-normal per varianza realistica
    return max(0, int(round(random.gauss(mean, mean**0.5))))


def make_match(hid, aid, season, dt, status):
    global fid_counter
    fid_counter += 1
    fid = fid_counter
    ph, pa = PROFILES[hid], PROFILES[aid]
    if status == "FT":
        ch = pois(ph["corn"] * .55); ca = pois(pa["corn"] * .5)
        gh = pois(ph["goal"] * .6);  ga = pois(pa["goal"] * .45)
        yh = pois((ph["card"]+pa["card"])/2 * .55); ya = pois((ph["card"]+pa["card"])/2 * .5)
    else:
        ch = ca = gh = ga = yh = ya = None
    fx = {
        "fixture": {"id": fid, "date": dt.isoformat()+"+00:00",
                    "status": {"short": status}},
        "teams": {"home": {"id": hid, "name": NAMES[hid]},
                  "away": {"id": aid, "name": NAMES[aid]}},
        "goals": {"home": gh, "away": ga},
    }
    key = f"{hid}_{season}"
    fixtures.setdefault(key, []).append(fx)
    # duplico anche nel key della trasferta (come fa l'API per team=)
    fixtures.setdefault(f"{aid}_{season}", []).append(fx)
    if status == "FT":
        stats[str(fid)] = [
            {"team": {"id": hid}, "statistics": [
                {"type": "Corner Kicks", "value": ch},
                {"type": "Yellow Cards", "value": yh},
                {"type": "Red Cards", "value": 0}]},
            {"team": {"id": aid}, "statistics": [
                {"type": "Corner Kicks", "value": ca},
                {"type": "Yellow Cards", "value": ya},
                {"type": "Red Cards", "value": 0}]},
        ]
    return fx


teams = list(PROFILES.keys())
# stagioni passate: tante partite finite
for season in (2023, 2024, 2025):
    base = datetime.datetime(season, 9, 1)
    for _ in range(90):
        h, a = random.sample(teams, 2)
        base += datetime.timedelta(days=1)
        make_match(h, a, season, base, "FT")

# prossimo turno: partite NON iniziate
nxt = datetime.datetime(2026, 8, 23)
for h, a in [(499, 496), (505, 502), (497, 489), (492, 487)]:
    make_match(h, a, 2025, nxt, "NS")
    nxt += datetime.timedelta(days=1)

json.dump(fixtures, open(os.path.join(DATA, "fixtures.json"), "w"))
json.dump(stats, open(os.path.join(DATA, "stats.json"), "w"))
print(f"Demo pronta: {sum(len(v) for v in fixtures.values())} righe partita, "
      f"{len(stats)} con statistiche.")
