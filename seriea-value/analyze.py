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
try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Rome")
except Exception:
    _TZ = None
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


def find_odd(bets, market, line, side):
    """Cerca nella lista quote Bet365 la quota della giocata (o None)."""
    def num(x):
        try:
            return float(x)
        except Exception:
            return None
    for bet in bets or []:
        name = (bet.get("name") or "").lower()
        vals = bet.get("values") or []
        if market == "btts" and "both teams" in name:
            want = "yes" if side == "yes" else "no"
            for v in vals:
                if str(v.get("value", "")).strip().lower() == want:
                    return num(v.get("odd"))
        elif market == "goals" and "over/under" in name and "goal" in name:
            want = f"{'over' if side == 'over' else 'under'} {line}"
            for v in vals:
                if str(v.get("value", "")).strip().lower() == want:
                    return num(v.get("odd"))
        elif market == "corners" and "corner" in name:
            want = f"{'over' if side == 'over' else 'under'} {line}"
            for v in vals:
                if str(v.get("value", "")).strip().lower() == want:
                    return num(v.get("odd"))
        elif market == "cards" and "card" in name:
            want = f"over {line}"
            for v in vals:
                if str(v.get("value", "")).strip().lower() == want:
                    return num(v.get("odd"))
    return None


def tier(s):
    if s["n"] >= 25 and s["lower"] >= config.MIN_PROB_SINGLE + 0.05:
        return "alta"
    if s["n"] >= config.MIN_SAMPLE and s["lower"] >= config.MIN_PROB_SINGLE:
        return "media"
    return "bassa"


# ---------- costruzione dati per il sito ---------------------------------
def grade_pick(h, f):
    """Confronta una giocata passata col risultato reale -> 'won' o 'lost'."""
    market, line, side = h["market"], h["line"], h["side"]
    if market == "corners":
        hit = f["corners"] > line if side == "over" else f["corners"] < line
    elif market == "goals":
        hit = f["goals"] > line if side == "over" else f["goals"] < line
    elif market == "cards":
        hit = f["cards"] > line
    elif market == "btts":
        hit = f["btts"] == (side == "yes")
    else:
        return "pending"
    return "won" if hit else "lost"


def update_history(payload_matches, feats):
    """Salva i consigli come 'pending' e giudica quelli ormai giocati."""
    hp = os.path.join(DATA_DIR, "history.json")
    history = json.load(open(hp)) if os.path.exists(hp) else {}

    # 1) giudico i pending le cui partite sono ora finite
    for fid, h in history.items():
        if h.get("status") == "pending" and fid in feats:
            h["status"] = grade_pick(h, feats[fid])

    # 2) registro/aggiorno i consigli attuali (solo se non gia' giudicati)
    for m in payload_matches:
        fid = m["fid"]; t = m["top"]
        if history.get(fid, {}).get("status") in ("won", "lost"):
            continue
        history[fid] = {"home": m["home"], "away": m["away"], "date": m["date"],
                        "label": t["label"], "market": t["market"], "line": t["line"],
                        "side": t["side"], "odd": t["odd"], "status": "pending"}

    json.dump(history, open(hp, "w"))
    # per il sito: ordino per data, piu' recente in cima
    rows = sorted(history.values(), key=lambda x: x["date"], reverse=True)
    settled = [r for r in rows if r["status"] in ("won", "lost")]
    won = sum(1 for r in settled if r["status"] == "won")
    return {"rows": rows[:40], "won": won, "settled": len(settled)}


def build_payload(fixtures, feats, odds):
    home_ids, away_ids = team_match_ids(feats)
    tracked = set(config.TEAMS.values())
    # finestra temporale: solo gare da oggi ai prossimi N giorni
    today = datetime.datetime.now(_TZ).date()
    horizon = today + datetime.timedelta(days=getattr(config, "UPCOMING_DAYS", 14))
    upcoming = []
    for arr in fixtures.values():
        for fx in arr:
            if fx["fixture"]["status"]["short"] != "NS":
                continue
            if fx["teams"]["home"]["id"] not in tracked and \
               fx["teams"]["away"]["id"] not in tracked:
                continue
            try:
                fxdate = datetime.date.fromisoformat(fx["fixture"]["date"][:10])
            except Exception:
                continue
            if fxdate < today or fxdate > horizon:
                continue
            upcoming.append(fx)
    # dedup + ordina per data
    seen = {}; 
    for fx in upcoming:
        seen[fx["fixture"]["id"]] = fx
    upcoming = sorted(seen.values(), key=lambda x: x["fixture"]["date"])

    matches = []
    singles_pool = []   # per costruire le doppie tra partite diverse
    per_match = []
    value_raw = []      # occasioni di valore (quota alta che batte la nostra stima)
    vmin = getattr(config, "VALUE_ODDS_MIN", 1.7)
    vmax = getattr(config, "VALUE_ODDS_MAX", 3.0)
    for fx in upcoming:
        sugg = suggestions_for_fixture(fx, feats, home_ids, away_ids)
        passing = [s for s in sugg if s["lower"] >= config.MIN_PROB_SINGLE]
        home = fx["teams"]["home"]["name"]; away = fx["teams"]["away"]["name"]
        fid = str(fx["fixture"]["id"])
        if passing:
            per_match.append({"home": home, "away": away, "fid": fid,
                              "date": fx["fixture"]["date"][:10], "options": passing})
        for s in sugg:
            if s["lower"] >= config.MIN_PROB_COMBO_LEG:
                singles_pool.append({"match": f"{home}-{away}", **s})
                break
        # caccia al valore: quota reale nella fascia + prob. prudente che la batte
        for s in sugg:
            ro = find_odd(odds.get(fid, []), s["market"], s["line"], s["side"])
            if ro and vmin <= ro <= vmax and s["lower"] * ro > 1.0:
                s2 = dict(s)
                s2["real_odd"] = ro
                s2["match"] = f"{home} - {away}"
                s2["date"] = fx["fixture"]["date"][:10]
                s2["edge"] = s["lower"] - 1.0 / ro   # margine sulla quota
                value_raw.append(s2)
    value_raw.sort(key=lambda x: x["edge"], reverse=True)

    # MIX: una giocata per partita, la piu' solida, ma diversificando i mercati
    # (una penalita' spinge verso mercati diversi: corner / gol / cartellini / btts).
    per_match.sort(key=lambda mm: mm["options"][0]["lower"], reverse=True)
    market_count = {}
    for mm in per_match:
        best, best_score = None, -1.0
        for s in mm["options"]:
            score = s["lower"] - 0.05 * market_count.get(s["market"], 0)
            if score > best_score:
                best_score, best = score, s
        if best is None:
            continue
        market_count[best["market"]] = market_count.get(best["market"], 0) + 1
        best["real_odd"] = find_odd(odds.get(mm["fid"], []), best["market"],
                                    best["line"], best["side"])
        matches.append({"home": mm["home"], "away": mm["away"], "fid": mm["fid"],
                        "date": mm["date"], "top": best})

    # tutte le gare imminenti, in ordine di DATA (la piu' vicina in cima)
    matches.sort(key=lambda m: m["date"])

    # doppie: prendi le 2 gambe piu' solide da partite DIVERSE (indipendenza)
    combos = []
    singles_pool.sort(key=lambda x: x["lower"], reverse=True)
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
        real = s.get("real_odd")
        # quota mostrata: reale Bet365 se c'e'; altrimenti indicativa = 1/prob.prudente
        # (coerente con la barra e col calcolo del ritorno, per non creare negativi finti)
        shown_odd = real if real else (round(1 / s["lower"], 2) if s["lower"] else None)
        return {"label": s["label"], "p": round(s["p"], 3),
                "lower": round(s["lower"], 3), "n": s["n"], "tier": tier(s),
                "odd": shown_odd, "odd_real": bool(real),
                "market": s["market"], "line": s["line"], "side": s["side"]}

    for m in matches:
        m["top"] = clean(m["top"])
    for c in combos:
        c["legs"] = [{"match": l["match"], **clean(l)} for l in c["legs"]]

    def clean_value(s):
        return {"match": s["match"], "label": s["label"],
                "lower": round(s["lower"], 3), "n": s["n"], "tier": tier(s),
                "odd": s["real_odd"], "edge": round(s["edge"], 3),
                "date": s["date"]}
    value_picks = [clean_value(s) for s in value_raw[:10]]

    shown = matches

    return {
        "generated": datetime.datetime.now(_TZ).strftime("%d/%m/%Y %H:%M"),
        "n_matches_analyzed": len(feats),
        "seasons": config.SEASONS,
        "value_band": (getattr(config, "VALUE_ODDS_MIN", 1.7),
                       getattr(config, "VALUE_ODDS_MAX", 3.0)),
        "matches": shown,
        "value_picks": value_picks,
        "combos": combos[:3],
    }


def main():
    fp = os.path.join(DATA_DIR, "fixtures.json")
    sp = os.path.join(DATA_DIR, "stats.json")
    op = os.path.join(DATA_DIR, "odds.json")
    if not os.path.exists(fp):
        sys.exit("Mancano i dati. Lancia prima:  python fetch.py")
    fixtures = json.load(open(fp))
    stats = json.load(open(sp)) if os.path.exists(sp) else {}
    odds = json.load(open(op)) if os.path.exists(op) else {}
    feats = build_features(fixtures, stats)
    payload = build_payload(fixtures, feats, odds)
    payload["history"] = update_history(payload["matches"], feats)
    from render import render, render_howto
    open(os.path.join(SITE_DIR, "index.html"), "w").write(render(payload))
    open(os.path.join(SITE_DIR, "come-funziona.html"), "w").write(render_howto(payload))
    print(f"Sito generato: {SITE_DIR}/index.html + come-funziona.html")
    print(f"Partite storiche analizzate: {payload['n_matches_analyzed']}")
    print(f"Storico: {payload['history']['settled']} giocate concluse.")
    print("Carica il contenuto di site/ sul tuo dominio.")


if __name__ == "__main__":
    main()
