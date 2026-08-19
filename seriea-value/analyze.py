#!/usr/bin/env python3
"""
Legge i dati in data/, calcola per ogni prossima partita quali scommesse
hanno una probabilita' storica PRUDENTE abbastanza alta da avere senso a
quota ~1.5, e genera il sito in site/index.html.

Prudenza: non usiamo la percentuale grezza ma il LIMITE INFERIORE di Wilson,
che penalizza i campioni piccoli (10 partite non valgono come 100).

Uso:  python analyze.py
"""
import os, sys, json, math, datetime
import config

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SITE_DIR = os.path.join(os.path.dirname(__file__), "site")
os.makedirs(SITE_DIR, exist_ok=True)

IMPLIED_15 = 1 / 1.5           # 0.667 : prob. implicita di una quota 1.5
Z = 1.28                        # ~90% un lato: prudente senza paralizzare


# ---------- statistica ---------------------------------------------------
def wilson_lower(k, n, z=Z):
    """Limite inferiore di Wilson per una proporzione k/n."""
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    center = p + z*z/(2*n)
    margin = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, (center - margin) / d)


# ---------- estrazione feature da una partita ----------------------------
def _stat_value(stats_for_fixture, team_id, wanted):
    """Somma un tipo di statistica (es. 'Corner Kicks') per una squadra."""
    for block in stats_for_fixture:
        if block.get("team", {}).get("id") == team_id:
            for s in block.get("statistics", []):
                if s.get("type") == wanted:
                    v = s.get("value")
                    return int(v) if isinstance(v, (int, float)) else 0
    return 0


def build_features(fixtures, stats):
    """Per ogni partita finita: corner totali, gol totali, btts, cartellini."""
    feats = {}
    for arr in fixtures.values():
        for fx in arr:
            if fx["fixture"]["status"]["short"] != "FT":
                continue
            fid = str(fx["fixture"]["id"])
            if fid in feats or fid not in stats:
                continue
            hid = fx["teams"]["home"]["id"]; aid = fx["teams"]["away"]["id"]
            s = stats[fid]
            corners = (_stat_value(s, hid, "Corner Kicks")
                       + _stat_value(s, aid, "Corner Kicks"))
            cards = 0
            for tid in (hid, aid):
                cards += (_stat_value(s, tid, "Yellow Cards")
                          + _stat_value(s, tid, "Red Cards"))
            gh = fx["goals"]["home"] or 0
            ga = fx["goals"]["away"] or 0
            feats[fid] = {
                "home_id": hid, "away_id": aid,
                "corners": corners, "goals": gh + ga,
                "cards": cards, "btts": (gh > 0 and ga > 0),
            }
    return feats


def team_match_ids(feats):
    """Per ogni squadra: id delle partite in casa e in trasferta."""
    home, away = {}, {}
    for fid, f in feats.items():
        home.setdefault(f["home_id"], []).append(fid)
        away.setdefault(f["away_id"], []).append(fid)
    return home, away


# ---------- valutazione di un mercato per una partita futura -------------
def evaluate_pool(fids, feats, metric, line, side):
    """Su un pool di partite, prob. che 'metric' sia over/under 'line'."""
    k = n = 0
    for fid in fids:
        v = feats[fid][metric]
        n += 1
        hit = (v > line) if side == "over" else (v < line)
        if hit:
            k += 1
    if n == 0:
        return None
    return {"p": k/n, "lower": wilson_lower(k, n), "n": n, "k": k}


def evaluate_btts(fids, feats, want_yes):
    k = n = 0
    for fid in fids:
        n += 1
        if feats[fid]["btts"] == want_yes:
            k += 1
    if n == 0:
        return None
    return {"p": k/n, "lower": wilson_lower(k, n), "n": n, "k": k}


def suggestions_for_fixture(fx, feats, home_ids, away_ids):
    """Tutte le scommesse valutate per una partita futura, ordinate."""
    hid = fx["teams"]["home"]["id"]; aid = fx["teams"]["away"]["id"]
    # pool = partite in casa dell'una + in trasferta dell'altra (contesto simile)
    pool = home_ids.get(hid, []) + away_ids.get(aid, [])
    out = []

    def add(label, metric, line, side):
        r = evaluate_pool(pool, feats, metric, line, side)
        if r and r["n"] >= config.MIN_SAMPLE:
            out.append({**r, "label": label, "market": metric,
                        "line": line, "side": side})

    for L in config.CORNER_LINES:
        add(f"Corner totali OVER {L}", "corners", L, "over")
        add(f"Corner totali UNDER {L}", "corners", L, "under")
    for L in config.GOAL_LINES:
        add(f"Gol totali OVER {L}", "goals", L, "over")
        add(f"Gol totali UNDER {L}", "goals", L, "under")
    for L in config.CARD_LINES:
        add(f"Cartellini OVER {L}", "cards", L, "over")
    for yes in (True, False):
        r = evaluate_btts(pool, feats, yes)
        if r and r["n"] >= config.MIN_SAMPLE:
            out.append({**r, "label": "Gol/Gol (BTTS) " + ("SI" if yes else "NO"),
                        "market": "btts", "line": None,
                        "side": "yes" if yes else "no"})

    out.sort(key=lambda x: x["lower"], reverse=True)
    return out


def tier(s):
    if s["n"] >= 25 and s["lower"] >= config.MIN_PROB_SINGLE + 0.05:
        return "alta"
    if s["n"] >= config.MIN_SAMPLE and s["lower"] >= config.MIN_PROB_SINGLE:
        return "media"
    return "bassa"


# ---------- costruzione dati per il sito ---------------------------------
def build_payload(fixtures, feats):
    home_ids, away_ids = team_match_ids(feats)
    tracked = set(config.TEAMS.values())
    upcoming = []
    for arr in fixtures.values():
        for fx in arr:
            if fx["fixture"]["status"]["short"] != "NS":
                continue
            if fx["teams"]["home"]["id"] not in tracked and \
               fx["teams"]["away"]["id"] not in tracked:
                continue
            upcoming.append(fx)
    # dedup + ordina per data
    seen = {}; 
    for fx in upcoming:
        seen[fx["fixture"]["id"]] = fx
    upcoming = sorted(seen.values(), key=lambda x: x["fixture"]["date"])

    matches = []
    singles_pool = []   # per costruire le doppie tra partite diverse
    for fx in upcoming:
        sugg = suggestions_for_fixture(fx, feats, home_ids, away_ids)
        singles = [s for s in sugg if s["lower"] >= config.MIN_PROB_SINGLE]
        combo_legs = [s for s in sugg if s["lower"] >= config.MIN_PROB_COMBO_LEG]
        m = {
            "home": fx["teams"]["home"]["name"],
            "away": fx["teams"]["away"]["name"],
            "date": fx["fixture"]["date"][:10],
            "top": sugg[0] if sugg else None,
            "singles": singles[:4],
            "all": sugg[:8],
        }
        for leg in combo_legs[:1]:
            singles_pool.append({"match": f'{m["home"]}-{m["away"]}', **leg})
        matches.append(m)

    # doppie: prendi le 2 gambe piu' solide da partite DIVERSE (indipendenza)
    combos = []
    singles_pool.sort(key=lambda x: x["lower"], reverse=True)
    used = set()
    for i in range(len(singles_pool)):
        for j in range(i+1, len(singles_pool)):
            a, b = singles_pool[i], singles_pool[j]
            if a["match"] == b["match"]:
                continue
            fair = 1/(a["p"]*b["p"]) if a["p"]*b["p"] > 0 else 99
            combos.append({"legs": [a, b], "fair_odds": round(fair, 2),
                           "prob": round(a["p"]*b["p"], 3)})
        if len(combos) >= 3:
            break

    def clean(s):
        return {"label": s["label"], "p": round(s["p"], 3),
                "lower": round(s["lower"], 3), "n": s["n"],
                "tier": tier(s), "fair_odds": round(1/s["p"], 2) if s["p"] else 99,
                "edge": round(s["lower"] - IMPLIED_15, 3)}

    for m in matches:
        m["top"] = clean(m["top"]) if m["top"] else None
        m["singles"] = [clean(s) for s in m["singles"]]
        m["all"] = [clean(s) for s in m["all"]]
    for c in combos:
        c["legs"] = [{"match": l["match"], **clean(l)} for l in c["legs"]]

    return {
        "generated": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "n_matches_analyzed": len(feats),
        "seasons": config.SEASONS,
        "matches": matches,
        "combos": combos[:3],
    }


def main():
    fp = os.path.join(DATA_DIR, "fixtures.json")
    sp = os.path.join(DATA_DIR, "stats.json")
    if not os.path.exists(fp):
        sys.exit("Mancano i dati. Lancia prima:  python fetch.py")
    fixtures = json.load(open(fp))
    stats = json.load(open(sp)) if os.path.exists(sp) else {}
    feats = build_features(fixtures, stats)
    payload = build_payload(fixtures, feats)
    from render import render
    html = render(payload)
    out = os.path.join(SITE_DIR, "index.html")
    open(out, "w").write(html)
    print(f"Sito generato: {out}")
    print(f"Partite storiche analizzate: {payload['n_matches_analyzed']}")
    print("Carica il contenuto di site/ sul tuo dominio.")


if __name__ == "__main__":
    main()
