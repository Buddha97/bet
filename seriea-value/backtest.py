#!/usr/bin/env python3
"""
BACKTEST ONESTO (out-of-sample).

Ripercorre una stagione passata (TEST) e, per ogni partita, calcola cosa il
sistema AVREBBE consigliato usando SOLO i dati di una stagione precedente
(TRAIN) - mai i dati della partita stessa. Poi confronta col risultato reale
e con la quota reale Bet365, e produce:
  - site/backtest.html   (pagina con tabella + tassi di successo per mercato)
  - data/market_stats.json (quali mercati vincono di piu')

Uso:  python backtest.py
"""
import os, sys, json, datetime
import config, analyze

DATA_DIR = analyze.DATA_DIR
SITE_DIR = analyze.SITE_DIR

TRAIN_SEASON = getattr(config, "BACKTEST_TRAIN_SEASON", 2024)
TEST_SEASON = getattr(config, "BACKTEST_TEST_SEASON", 2025)


def _fetch_odds_for(fids):
    """Scarica (e mette in cache) le quote Bet365 storiche per le partite del test."""
    path = os.path.join(DATA_DIR, "backtest_odds.json")
    odds = json.load(open(path)) if os.path.exists(path) else {}
    try:
        import fetch
    except Exception:
        return odds
    book = getattr(config, "BET365_ID", 8)
    todo = [f for f in fids if f not in odds]
    print(f"Quote storiche da scaricare: {len(todo)} partite (in cache: {len(odds)}).")
    for fid in todo:
        try:
            d = fetch.api_get("/odds", {"fixture": fid, "bookmaker": book})
        except SystemExit:
            break  # limite giornaliero: riprende al prossimo giro
        resp = d.get("response", [])
        bets = resp[0]["bookmakers"][0]["bets"] if resp and resp[0].get("bookmakers") else []
        odds[fid] = bets
        json.dump(odds, open(path, "w"))
    return odds


def run():
    fp = os.path.join(DATA_DIR, "fixtures.json")
    sp = os.path.join(DATA_DIR, "stats.json")
    if not os.path.exists(fp):
        sys.exit("Mancano i dati. Lancia prima il normale aggiornamento.")
    fixtures = json.load(open(fp))
    stats = json.load(open(sp)) if os.path.exists(sp) else {}

    # feats completi (per giudicare i risultati reali del TEST)
    feats_all = analyze.build_features(fixtures, stats)

    # pool di ALLENAMENTO: solo le partite della stagione TRAIN
    train_fixtures = {k: v for k, v in fixtures.items() if k.endswith(f"_{TRAIN_SEASON}")}
    feats_train = analyze.build_features(train_fixtures, stats)
    home_ids, away_ids = analyze.team_match_ids(feats_train)

    # partite del TEST (finite) delle squadre seguite
    tracked = set(config.TEAMS.values())
    test_matches = {}
    for k, arr in fixtures.items():
        if not k.endswith(f"_{TEST_SEASON}"):
            continue
        for fx in arr:
            if fx["fixture"]["status"]["short"] != "FT":
                continue
            if fx["teams"]["home"]["id"] not in tracked and \
               fx["teams"]["away"]["id"] not in tracked:
                continue
            test_matches[str(fx["fixture"]["id"])] = fx

    odds = _fetch_odds_for(list(test_matches.keys()))

    rows = []
    per_market = {}   # market -> [win, tot]
    for fid, fx in test_matches.items():
        if fid not in feats_all:      # niente statistiche reali: non giudicabile
            continue
        sugg = analyze.suggestions_for_fixture(fx, feats_train, home_ids, away_ids)
        passing = [s for s in sugg if s["lower"] >= config.MIN_PROB_SINGLE]
        if not passing:
            continue
        pick = passing[0]             # la piu' solida (come farebbe il sistema)
        outcome = analyze.grade_pick(pick, feats_all[fid])   # 'won'/'lost'
        ro = analyze.find_odd(odds.get(fid, []), pick["market"], pick["line"], pick["side"])
        rows.append({
            "date": fx["fixture"]["date"][:10],
            "home": fx["teams"]["home"]["name"], "away": fx["teams"]["away"]["name"],
            "label": pick["label"], "market": pick["market"],
            "lower": round(pick["lower"], 3), "odd": ro, "status": outcome,
        })
        w, t = per_market.get(pick["market"], (0, 0))
        per_market[pick["market"]] = (w + (1 if outcome == "won" else 0), t + 1)

    rows.sort(key=lambda r: r["date"], reverse=True)
    won = sum(1 for r in rows if r["status"] == "won")
    tot = len(rows)

    # statistiche per mercato (e salvataggio per l'eventuale uso in home)
    MK = {"corners": "Corner", "goals": "Gol", "cards": "Cartellini", "btts": "Gol/Gol"}
    market_rows = []
    market_stats = {}
    for mk, (w, t) in sorted(per_market.items(), key=lambda x: -(x[1][0] / x[1][1] if x[1][1] else 0)):
        rate = w / t if t else 0
        market_rows.append({"market": MK.get(mk, mk), "won": w, "tot": t,
                            "rate": round(100 * rate)})
        market_stats[mk] = {"won": w, "n": t, "rate": round(rate, 3)}
    json.dump(market_stats, open(os.path.join(DATA_DIR, "market_stats.json"), "w"))

    # quota media reale sui vinti (indicativa del rendimento)
    payload = {
        "generated": datetime.datetime.now(analyze._TZ).strftime("%d/%m/%Y %H:%M"),
        "train": TRAIN_SEASON, "test": TEST_SEASON,
        "won": won, "tot": tot,
        "rate": round(100 * won / tot) if tot else 0,
        "market_rows": market_rows,
        "rows": rows[:400],
    }
    from render import render_backtest
    html = render_backtest(payload)
    site_pw = os.environ.get("SITE_PASSWORD", "").strip()
    if site_pw:
        from render import gate
        html = gate(html, site_pw)
    open(os.path.join(SITE_DIR, "backtest.html"), "w").write(html)
    print(f"Backtest: {won}/{tot} vinte ({payload['rate']}%). "
          f"Pagina: {SITE_DIR}/backtest.html")


if __name__ == "__main__":
    run()
