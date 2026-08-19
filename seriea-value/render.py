# -*- coding: utf-8 -*-
"""Genera l'HTML statico del sito a partire dal payload di analyze.py."""
import json

IMPLIED_15 = 66.7  # percentuale implicita di una quota 1.5, per il marker

TIER_LABEL = {"alta": "Confidenza alta", "media": "Confidenza media",
              "bassa": "Confidenza bassa"}


def _bar(s):
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
    top = m["top"]
    return f"""
    <article class="slip" data-p="{top['lower']}" data-edge="{max(top['edge'],0.0001):.4f}">
      <div class="slip-top">
        <span class="date mono">{m['date']}</span>
        <span class="idx mono">#{idx:02d}</span>
      </div>
      <h2 class="teams"><span>{m['home']}</span><em>vs</em><span>{m['away']}</span></h2>
      <div class="perf"></div>
      {_pick(top)}
      <div class="stake-box">
        <div class="stake-row"><span class="stake-k mono">punta</span>
          <span class="stake-v mono" data-stake>—</span></div>
        <div class="stake-row"><span class="stake-k mono">ritorno atteso</span>
          <span class="stake-v mono ret" data-return>—</span></div>
      </div>
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
    cards = "".join(_match_card(m, i + 1) for i, m in enumerate(p["matches"]))
    if not cards:
        cards = ('<p class="empty-big">Nessuna giocata a confidenza alta per le '
                 'prossime gare. Ricontrolla dopo il prossimo aggiornamento.</p>')
    combos = "".join(_combo_card(c, i + 1) for i, c in enumerate(p["combos"]))
    combos_block = f"""
      <section class="combos">
        <h3 class="eyebrow">Doppie a bassa varianza · obiettivo quota ~1.5</h3>
        <div class="combo-grid">{combos}</div>
      </section>""" if combos else ""
    seasons = ", ".join(str(s) for s in p["seasons"])
    n_picks = len(p["matches"])

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Schedina free money</title>
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

/* ---- pannello budget (la cassa) ---- */
.bank{{margin:26px 0 8px;background:linear-gradient(180deg,#1a2230,#141a24);
  border:1px solid var(--line);border-radius:12px;padding:20px}}
.bank-grid{{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-end}}
.field label{{display:block;font-family:'Barlow Condensed',sans-serif;
  text-transform:uppercase;letter-spacing:1.5px;font-size:12px;
  color:var(--muted);margin-bottom:6px}}
.field input,.field select{{background:#0c0f14;border:1px solid var(--line);
  color:var(--paper);font-family:'Space Mono',monospace;font-size:16px;
  padding:9px 12px;border-radius:8px;width:150px}}
.field input:focus,.field select:focus{{outline:1px solid var(--amber)}}
.bank-out{{margin-left:auto;text-align:right;display:flex;gap:26px}}
.bank-out .k{{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;
  letter-spacing:1.5px;font-size:12px;color:var(--muted)}}
.bank-out .v{{font-family:'Space Mono',monospace;font-size:24px;font-weight:700;
  margin-top:4px}}
.bank-out .v.pos{{color:var(--mint)}} .bank-out .v.neg{{color:var(--clay)}}
.bank-note{{font-size:11.5px;color:var(--muted);margin-top:14px;
  border-top:1px solid var(--line);padding-top:12px}}

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

/* casella importo, stile schedina */
.stake-box{{margin-top:14px;border-top:1px solid var(--line);padding-top:12px;
  display:grid;gap:6px}}
.stake-row{{display:flex;justify-content:space-between;align-items:baseline}}
.stake-k{{font-size:11px;text-transform:uppercase;letter-spacing:1px;
  color:var(--muted)}}
.stake-v{{font-size:18px;font-weight:700}}
.stake-v.ret{{color:var(--mint)}}
.stake-v.ret.neg{{color:var(--clay)}}

.empty-big{{color:var(--muted);font-size:15px;padding:30px 0}}

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
  font-size:11.5px;color:var(--muted);max-width:720px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">Schedina<br><em>free money</em></div>
    <div class="meta-line">
      <div class="muted">aggiornato</div>
      <div class="mono">{p['generated']}</div>
      <div class="muted" style="margin-top:8px">base storica</div>
      <div class="mono">{p['n_matches_analyzed']} gare · {seasons}</div>
    </div>
  </header>

  <section class="bank">
    <div class="bank-grid">
      <div class="field">
        <label>Budget mensile (€)</label>
        <input id="budget" type="number" min="0" step="10" placeholder="es. 100">
      </div>
      <input id="rounds" type="hidden" value="4">
      <input id="method" type="hidden" value="flat">
      <div class="bank-out">
        <div><div class="k">Puntata / giornata</div>
          <div class="v" id="tot-stake">—</div></div>
        <div><div class="k">Guadagno atteso / mese</div>
          <div class="v" id="tot-month">—</div></div>
      </div>
    </div>
    <div class="bank-note" id="bank-note">
      Inserisci un budget per vedere quanto puntare su ogni giocata e il ritorno
      atteso. Le stime usano le probabilità storiche prudenti e una quota 1.5;
      il risultato reale varia partita per partita.
    </div>
  </section>

  {combos_block}

  <h3 class="eyebrow" style="margin-top:44px">Prossime gare · {n_picks} migliori a confidenza alta</h3>
  <div class="grid" id="grid">{cards}</div>

  <footer>
    Strumento statistico a uso personale tra amici. Le quote "eque" sono l'inverso
    della probabilità stimata: confrontale con quelle reali del bookmaker prima di
    puntare — il valore esiste solo se la quota offerta è più alta di quella equa.
    Il "guadagno atteso" è una media statistica, non una promessa: nel breve periodo
    si vince e si perde. 18+. Il gioco può causare dipendenza.
  </footer>
</div>

<script>
(function(){{
  var TARGET = {p['target_odds']};
  var budget = document.getElementById('budget');
  var rounds = document.getElementById('rounds');
  var method = document.getElementById('method');
  var slips  = Array.prototype.slice.call(document.querySelectorAll('.slip[data-p]'));

  // memoria nel browser (solo il budget; metodo e giornate sono fissi)
  try {{
    if(localStorage.getItem('sfm_budget')) budget.value = localStorage.getItem('sfm_budget');
  }} catch(e){{}}

  function euro(x){{ return '€' + (Math.round(x*100)/100).toFixed(2); }}

  function recompute(){{
    var B = parseFloat(budget.value) || 0;
    var R = Math.max(1, parseInt(rounds.value) || 1);
    var perRound = B / R;               // budget da giocare in una giornata
    var m = method.value;
    var N = slips.length;

    // pesi per la ripartizione
    var weights = slips.map(function(el){{
      if(m === 'prop') return Math.max(0.0001, parseFloat(el.dataset.edge));
      return 1; // flat
    }});
    var wsum = weights.reduce(function(a,b){{return a+b;}}, 0) || 1;

    var totStake = 0, totRet = 0;
    slips.forEach(function(el, i){{
      var pi = parseFloat(el.dataset.p);
      var stake;
      if(m === 'pct') stake = perRound * 0.05;          // 5% fisso a giocata
      else stake = perRound * (weights[i] / wsum);       // flat o proporzionale
      var ret = stake * (TARGET * pi - 1);               // ritorno atteso (media)
      totStake += stake; totRet += ret;
      el.querySelector('[data-stake]').textContent = B ? euro(stake) : '—';
      var rEl = el.querySelector('[data-return]');
      rEl.textContent = B ? (ret>=0?'+':'') + euro(ret) : '—';
      rEl.classList.toggle('neg', ret < 0);
    }});

    var sEl = document.getElementById('tot-stake');
    var mEl = document.getElementById('tot-month');
    sEl.textContent = B ? euro(totStake) : '—';
    var monthly = totRet * R;
    mEl.textContent = B ? (monthly>=0?'+':'') + euro(monthly) : '—';
    mEl.className = 'v ' + (B ? (monthly>=0?'pos':'neg') : '');

    var note = document.getElementById('bank-note');

    try {{
      localStorage.setItem('sfm_budget', budget.value);
    }} catch(e){{}}
  }}

  [budget, rounds, method].forEach(function(el){{
    el.addEventListener('input', recompute);
    el.addEventListener('change', recompute);
  }});
  recompute();
}})();
</script>
</body>
</html>"""
