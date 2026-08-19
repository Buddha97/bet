# -*- coding: utf-8 -*-
"""Genera l'HTML statico del sito a partire dal payload di analyze.py."""
import json

IMPLIED_15 = 66.7  # percentuale implicita di una quota 1.5, per il marker

TIER_LABEL = {"alta": "Confidenza alta", "media": "Confidenza media",
              "bassa": "Confidenza bassa"}


def _bar(s):
    """Barra di prudenza: pieno = limite inferiore; tacca = soglia quota 1.5."""
    lower = int(round(s["lower"] * 100))
    p = int(round(s["p"] * 100))
    return f"""
      <div class="gauge" title="Prob. prudente {lower}% (grezza {p}%)">
        <div class="gauge-fill t-{s['tier']}" style="width:{lower}%"></div>
        <div class="gauge-mark" style="left:{IMPLIED_15}%"></div>
      </div>
      <div class="gauge-legend">
        <span class="mono">{lower}%</span>
        <span class="muted">soglia 1.5 = {IMPLIED_15:.0f}%</span>
      </div>"""


def _pick(s):
    edge = s["edge"] * 100
    edge_s = f"+{edge:.1f}" if edge >= 0 else f"{edge:.1f}"
    return f"""
      <div class="pick">
        <div class="pick-head">
          <span class="pick-label">{s['label']}</span>
          <span class="chip t-{s['tier']}">{TIER_LABEL[s['tier']]}</span>
        </div>
        {_bar(s)}
        <div class="pick-meta mono">
          <span>campione {s['n']} gare</span>
          <span>quota equa ~{s['fair_odds']}</span>
          <span class="edge">margine {edge_s} pt</span>
        </div>
      </div>"""


def _match_card(m, idx):
    if not m["top"]:
        body = '<p class="empty">Nessuna scommessa supera le soglie di prudenza per questa gara.</p>'
        extra = ""
    else:
        body = _pick(m["top"])
        others = m["singles"][1:]
        rows = "".join(
            f'<li><span>{s["label"]}</span>'
            f'<span class="mono t-{s["tier"]}-txt">{int(round(s["lower"]*100))}%</span>'
            f'<span class="mono muted">n={s["n"]}</span></li>' for s in others)
        extra = f"""
          <details>
            <summary>Altre giocate solide ({len(others)})</summary>
            <ul class="others">{rows}</ul>
          </details>""" if others else ""
    return f"""
    <article class="slip">
      <div class="slip-top">
        <span class="date mono">{m['date']}</span>
        <span class="idx mono">#{idx:02d}</span>
      </div>
      <h2 class="teams"><span>{m['home']}</span><em>vs</em><span>{m['away']}</span></h2>
      <div class="perf"></div>
      {body}
      {extra}
    </article>"""


def _combo_card(c, i):
    legs = "".join(
        f'<div class="leg"><span class="leg-match mono muted">{l["match"]}</span>'
        f'<span class="leg-label">{l["label"]}</span>'
        f'<span class="mono">{int(round(l["lower"]*100))}%</span></div>'
        for l in c["legs"])
    return f"""
    <article class="combo">
      <div class="combo-top"><span class="mono muted">DOPPIA #{i}</span>
        <span class="combo-odds mono">quota equa ~{c['fair_odds']}</span></div>
      {legs}
      <div class="combo-foot mono">prob. combinata stimata {int(round(c['prob']*100))}% · gambe da partite diverse</div>
    </article>"""


def render(p):
    cards = "".join(_match_card(m, i+1) for i, m in enumerate(p["matches"]))
    combos = "".join(_combo_card(c, i+1) for i, c in enumerate(p["combos"]))
    combos_block = f"""
      <section class="combos">
        <h3 class="eyebrow">Doppie a bassa varianza · obiettivo quota ~1.5</h3>
        <div class="combo-grid">{combos}</div>
      </section>""" if combos else ""
    seasons = ", ".join(str(s) for s in p["seasons"])

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Schedina · Serie A value</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0E1116; --panel:#161A21; --panel2:#1B212B; --line:#2A3340;
  --paper:#E9E6DD; --muted:#828C9B;
  --mint:#7DD3A8; --amber:#E0B84C; --clay:#C1727A;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:
  radial-gradient(1200px 600px at 70% -10%, #182131 0%, transparent 60%),
  var(--bg);
  color:var(--paper);font-family:Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;line-height:1.5}}
.mono{{font-family:'Space Mono',monospace}}
.muted{{color:var(--muted)}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 80px}}

/* header */
header{{display:flex;justify-content:space-between;align-items:flex-end;
  flex-wrap:wrap;gap:16px;border-bottom:1px solid var(--line);padding-bottom:22px}}
.brand{{font-family:'Barlow Condensed',sans-serif;font-weight:700;
  font-size:clamp(34px,6vw,58px);letter-spacing:.5px;line-height:.9;
  text-transform:uppercase}}
.brand em{{color:var(--amber);font-style:normal}}
.meta-line{{text-align:right;font-size:13px}}
.meta-line .mono{{color:var(--paper)}}

.eyebrow{{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;
  letter-spacing:2px;font-size:15px;color:var(--muted);font-weight:600;
  margin:0 0 16px}}

/* grid of slips */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
  gap:18px}}
.slip{{background:linear-gradient(180deg,var(--panel),var(--panel2));
  border:1px solid var(--line);border-radius:10px;padding:18px 18px 16px;
  position:relative;overflow:hidden}}
.slip-top{{display:flex;justify-content:space-between;font-size:12px}}
.slip-top .date{{color:var(--amber)}}
.slip-top .idx{{color:var(--muted)}}
.teams{{font-family:'Barlow Condensed',sans-serif;font-weight:600;
  font-size:26px;line-height:1;margin:8px 0 0;text-transform:uppercase;
  display:flex;flex-wrap:wrap;align-items:baseline;gap:8px}}
.teams em{{font-style:normal;color:var(--muted);font-size:15px}}
.perf{{height:1px;margin:14px -18px;border-top:1px dashed var(--line)}}

.pick-head{{display:flex;justify-content:space-between;align-items:center;
  gap:10px;margin-bottom:12px}}
.pick-label{{font-weight:600;font-size:15.5px}}
.chip{{font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;
  padding:3px 8px;border-radius:20px;white-space:nowrap;font-weight:600}}
.t-alta{{background:rgba(125,211,168,.14);color:var(--mint);
  border:1px solid rgba(125,211,168,.35)}}
.t-media{{background:rgba(224,184,76,.14);color:var(--amber);
  border:1px solid rgba(224,184,76,.35)}}
.t-bassa{{background:rgba(193,114,122,.14);color:var(--clay);
  border:1px solid rgba(193,114,122,.35)}}

/* gauge */
.gauge{{position:relative;height:12px;background:#0c0f14;border-radius:6px;
  border:1px solid var(--line);overflow:hidden}}
.gauge-fill{{height:100%;border-radius:6px 0 0 6px}}
.gauge-fill.t-alta{{background:var(--mint)}}
.gauge-fill.t-media{{background:var(--amber)}}
.gauge-fill.t-bassa{{background:var(--clay)}}
.gauge-mark{{position:absolute;top:-3px;width:2px;height:18px;
  background:var(--paper);opacity:.75}}
.gauge-legend{{display:flex;justify-content:space-between;font-size:11px;
  margin-top:6px}}
.gauge-legend .mono{{font-weight:700}}

.pick-meta{{display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;
  margin-top:12px;color:var(--muted)}}
.pick-meta .edge{{color:var(--paper)}}

details{{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}}
summary{{cursor:pointer;font-size:12.5px;color:var(--muted);
  font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;
  text-transform:uppercase}}
.others{{list-style:none;padding:0;margin:10px 0 0}}
.others li{{display:flex;justify-content:space-between;gap:8px;
  font-size:12.5px;padding:5px 0;border-bottom:1px dotted var(--line)}}
.others li span:first-child{{flex:1}}
.t-alta-txt{{color:var(--mint)}} .t-media-txt{{color:var(--amber)}}
.t-bassa-txt{{color:var(--clay)}}
.empty{{color:var(--muted);font-size:13.5px;margin:6px 0 0}}

/* combos */
.combos{{margin-top:44px}}
.combo-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
  gap:16px}}
.combo{{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:16px;border-top:3px solid var(--amber)}}
.combo-top{{display:flex;justify-content:space-between;margin-bottom:10px;
  font-size:12px}}
.combo-odds{{color:var(--amber);font-weight:700}}
.leg{{display:grid;grid-template-columns:1fr auto;gap:4px 10px;
  padding:8px 0;border-bottom:1px dotted var(--line)}}
.leg-match{{grid-column:1/-1;font-size:11px}}
.leg-label{{font-size:13.5px}}
.combo-foot{{font-size:11px;color:var(--muted);margin-top:10px}}

footer{{margin-top:56px;border-top:1px solid var(--line);padding-top:20px;
  font-size:11.5px;color:var(--muted);max-width:680px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">Sche<em>dina</em><br>Serie A · value</div>
    <div class="meta-line">
      <div class="muted">aggiornato</div>
      <div class="mono">{p['generated']}</div>
      <div class="muted" style="margin-top:8px">base storica</div>
      <div class="mono">{p['n_matches_analyzed']} gare · {seasons}</div>
    </div>
  </header>

  {combos_block}

  <h3 class="eyebrow" style="margin-top:44px">Prossime gare · miglior giocata singola</h3>
  <div class="grid">{cards}</div>

  <footer>
    Strumento statistico a uso personale tra amici. Le quote "eque" sono l'inverso della
    probabilità stimata: confrontale sempre con quelle reali del bookmaker prima di puntare —
    il valore esiste solo quando la quota offerta è più alta di quella equa.
    18+. Il gioco può causare dipendenza.
  </footer>
</div>
</body>
</html>"""
