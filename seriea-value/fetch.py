#!/usr/bin/env python3
"""
Scarica da API-Football le partite e le statistiche (corner, cartellini)
delle squadre scelte, e le salva in data/. E' RESUMABILE: se il limite
giornaliero finisce, rilancialo domani e riprende da dove si era fermato.

Uso:
    python fetch.py teams     # elenca gli id squadra (verifica config.py)
    python fetch.py           # scarica partite + statistiche
"""
import os, sys, json, time, datetime
import urllib.request, urllib.error
import config

API_HOST = "https://v3.football.api-sports.io"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COUNTER_FILE = os.path.join(DATA_DIR, "_requests_today.json")

os.makedirs(DATA_DIR, exist_ok=True)


def _key():
    k = os.environ.get("APIFOOTBALL_KEY") or config.API_KEY
    if not k or k == "INCOLLA_QUI_LA_TUA_CHIAVE":
        sys.exit("ERRORE: nessuna chiave. Impostala in config.py o nella "
                 "variabile d'ambiente APIFOOTBALL_KEY.")
    return k.strip()


def _load_counter():
    today = datetime.date.today().isoformat()
    try:
        c = json.load(open(COUNTER_FILE))
        if c.get("date") == today:
            return c
    except Exception:
        pass
    return {"date": today, "count": 0}


def _save_counter(c):
    json.dump(c, open(COUNTER_FILE, "w"))


def api_get(path, params, daily_limit=None):
    """Una chiamata all'API, contando le richieste della giornata.
    Rispetta il ritmo del piano e gestisce il limite-al-minuto (429)."""
    if daily_limit is None:
        daily_limit = getattr(config, "DAILY_LIMIT", 100)
    pacing = getattr(config, "REQUEST_PACING_SECONDS", 7)
    c = _load_counter()
    if c["count"] >= daily_limit:
        # Non e' un errore: e' una pausa. Usciamo "bene" (codice 0) cosi'
        # l'automazione prosegue e genera comunque il sito coi dati gia' presi.
        print(f"\nLimite giornaliero ({daily_limit}) raggiunto. "
              f"Domani riprende da dove era.")
        raise SystemExit(0)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{API_HOST}{path}?{qs}"
    req = urllib.request.Request(url, headers={"x-apisports-key": _key()})
    data = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:  # troppe richieste al minuto: aspetto e riprovo
                print("  limite-al-minuto raggiunto: attendo 65s e riprovo...")
                time.sleep(65)
                continue
            sys.exit(f"Errore API {e.code}: {e.reason}")
    if data is None:
        print("  troppi tentativi falliti, mi fermo qui (riprende dopo).")
        raise SystemExit(0)
    c["count"] += 1
    _save_counter(c)
    if data.get("errors"):
        print("  avviso API:", data["errors"])
    time.sleep(pacing)  # ritmo prudente per non sforare il limite al minuto
    return data


def cmd_teams():
    """Elenca gli id delle squadre di Serie A per l'ultima stagione."""
    season = config.SEASONS[-1]
    d = api_get("/teams", {"league": config.LEAGUE_ID, "season": season})
    print(f"\nSquadre Serie A {season} (nome  ->  id):\n")
    for item in sorted(d.get("response", []),
                       key=lambda x: x["team"]["name"]):
        print(f"  {item['team']['name']:<22} {item['team']['id']}")
    print("\nCopia gli id giusti dentro config.py -> TEAMS")


def cmd_fetch():
    fixtures_path = os.path.join(DATA_DIR, "fixtures.json")
    stats_path = os.path.join(DATA_DIR, "stats.json")
    fixtures = json.load(open(fixtures_path)) if os.path.exists(fixtures_path) else {}
    stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}

    current_season = max(config.SEASONS)  # la stagione "viva"

    # 1) partite di ogni squadra, per stagione (poche richieste).
    #    Le stagioni PASSATE non cambiano piu' -> se in cache, si saltano.
    #    La stagione IN CORSO si ri-scarica sempre: cosi' entrano i nuovi
    #    risultati e le nuove giornate messe a calendario.
    for name, tid in config.TEAMS.items():
        for season in config.SEASONS:
            key = f"{tid}_{season}"
            if key in fixtures and season != current_season:
                continue
            print(f"Partite: {name} {season} ...")
            d = api_get("/fixtures", {"league": config.LEAGUE_ID,
                                      "season": season, "team": tid})
            fixtures[key] = d.get("response", [])
            json.dump(fixtures, open(fixtures_path, "w"))

    # 2) statistiche per ogni partita (1 richiesta a partita = la parte cara)
    to_do = {}
    for arr in fixtures.values():
        for fx in arr:
            fid = str(fx["fixture"]["id"])
            if fid in stats:
                continue
            if fx["fixture"]["status"]["short"] != "FT":  # solo partite finite
                continue
            to_do[fid] = fx
    print(f"\nStatistiche da scaricare: {len(to_do)} partite "
          f"(1 richiesta ciascuna).")
    for fid, fx in to_do.items():
        h = fx["teams"]["home"]["name"]; a = fx["teams"]["away"]["name"]
        print(f"  stats {h} - {a}")
        d = api_get("/fixtures/statistics", {"fixture": fid})
        stats[fid] = d.get("response", [])
        json.dump(stats, open(stats_path, "w"))
    print("\nStatistiche fatte.")

    # 3) quote Bet365 per le partite FUTURE (endpoint odds, 1 richiesta a gara).
    #    Le quote cambiano nel tempo: le ri-scarichiamo a ogni giro (poche gare).
    odds_path = os.path.join(DATA_DIR, "odds.json")
    odds = json.load(open(odds_path)) if os.path.exists(odds_path) else {}
    bookmaker = getattr(config, "BET365_ID", 8)
    ns = {}
    for arr in fixtures.values():
        for fx in arr:
            if fx["fixture"]["status"]["short"] == "NS":
                ns[str(fx["fixture"]["id"])] = fx
    print(f"Quote Bet365 da scaricare: {len(ns)} partite future.")
    for fid, fx in ns.items():
        h = fx["teams"]["home"]["name"]; a = fx["teams"]["away"]["name"]
        print(f"  quote {h} - {a}")
        d = api_get("/odds", {"fixture": fid, "bookmaker": bookmaker})
        resp = d.get("response", [])
        bets = []
        if resp:
            bms = resp[0].get("bookmakers", [])
            if bms:
                bets = bms[0].get("bets", [])
        odds[fid] = bets
        json.dump(odds, open(odds_path, "w"))
    print("\nFatto. Dati in data/. Ora lancia:  python analyze.py")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "teams":
        cmd_teams()
    else:
        cmd_fetch()
