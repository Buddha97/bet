# -*- coding: utf-8 -*-
"""Genera il sito (index) e la pagina 'Come funziona' dal payload."""

IMPLIED_15 = 66.7


def _itdate(iso):
    """2026-08-22 -> 22/08/26 (formato italiano). Se non riconosce, lascia com'e'."""
    try:
        y, m, d = iso[:10].split("-")
        return f"{d}/{m}/{y[2:]}"
    except Exception:
        return iso


TIER_LABEL = {"alta": "Confidenza alta", "media": "Confidenza media",
              "bassa": "Confidenza bassa"}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700'
         '&family=Inter:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">')

BASE_CSS = """
:root{
  --bg:#0E1116; --panel:#161A21; --panel2:#1B212B; --line:#2A3340;
  --paper:#E9E6DD; --muted:#828C9B;
  --mint:#7DD3A8; --amber:#E0B84C; --clay:#C1727A;
}
*{box-sizing:border-box}
body{margin:0;background:
  radial-gradient(1200px 600px at 70% -10%, #182131 0%, transparent 60%), var(--bg);
  color:var(--paper);font-family:Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased;line-height:1.5}
.mono{font-family:'Space Mono',monospace}
.muted{color:var(--muted)}
a{color:var(--amber);text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 80px}
header{display:flex;justify-content:space-between;align-items:flex-end;
  flex-wrap:wrap;gap:16px;border-bottom:1px solid var(--line);padding-bottom:22px}
.brand{font-family:'Barlow Condensed',sans-serif;font-weight:700;
  font-size:clamp(34px,6vw,58px);letter-spacing:.5px;line-height:.9;text-transform:uppercase}
.brand em{color:var(--amber);font-style:normal}
.meta-line{text-align:right;font-size:13px}
.meta-line .mono{color:var(--paper)}
.nav{margin:16px 0 0;font-family:'Barlow Condensed',sans-serif;letter-spacing:1.5px;
  text-transform:uppercase;font-size:14px}
.eyebrow{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;
  letter-spacing:2px;font-size:15px;color:var(--muted);font-weight:600;margin:0 0 16px}
footer{margin-top:56px;border-top:1px solid var(--line);padding-top:20px;
  font-size:11.5px;color:var(--muted);max-width:720px}
"""

SITE_CSS = BASE_CSS + """
.bank{margin:26px 0 8px;background:linear-gradient(180deg,#1a2230,#141a24);
  border:1px solid var(--line);border-radius:12px;padding:20px}
.bank-grid{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-end}
.field label{display:block;font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;
  letter-spacing:1.5px;font-size:12px;color:var(--muted);margin-bottom:6px}
.field input{background:#0c0f14;border:1px solid var(--line);color:var(--paper);
  font-family:'Space Mono',monospace;font-size:16px;padding:9px 12px;border-radius:8px;width:150px}
.field input:focus{outline:1px solid var(--amber)}
.bank-out{margin-left:auto;text-align:right;display:flex;gap:26px}
.bank-out .k{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;
  letter-spacing:1.5px;font-size:12px;color:var(--muted)}
.bank-out .v{font-family:'Space Mono',monospace;font-size:24px;font-weight:700;margin-top:4px}
.bank-out .v.pos{color:var(--mint)} .bank-out .v.neg{color:var(--clay)}
.bank-note{font-size:11.5px;color:var(--muted);margin-top:14px;
  border-top:1px solid var(--line);padding-top:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px}
.slip{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);
  border-radius:10px;padding:18px 18px 16px;position:relative;overflow:hidden}
.slip-top{display:flex;justify-content:space-between;font-size:12px}
.slip-top .date{color:var(--amber)} .slip-top .idx{color:var(--muted)}
.teams{font-family:'Barlow Condensed',sans-serif;font-weight:600;font-size:26px;line-height:1;
  margin:8px 0 0;text-transform:uppercase;display:flex;flex-wrap:wrap;align-items:baseline;gap:8px}
.teams em{font-style:normal;color:var(--muted);font-size:15px}
.perf{height:1px;margin:14px -18px;border-top:1px dashed var(--line)}
.pick-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}
.pick-label{font-weight:600;font-size:15.5px}
.chip{font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;padding:3px 8px;
  border-radius:20px;white-space:nowrap;font-weight:600}
.t-alta{background:rgba(125,211,168,.14);color:var(--mint);border:1px solid rgba(125,211,168,.35)}
.t-media{background:rgba(224,184,76,.14);color:var(--amber);border:1px solid rgba(224,184,76,.35)}
.t-bassa{background:rgba(193,114,122,.14);color:var(--clay);border:1px solid rgba(193,114,122,.35)}
.gauge{position:relative;height:12px;background:#0c0f14;border-radius:6px;border:1px solid var(--line);overflow:hidden}
.gauge-fill{height:100%;border-radius:6px 0 0 6px}
.gauge-fill.t-alta{background:var(--mint)} .gauge-fill.t-media{background:var(--amber)}
.gauge-fill.t-bassa{background:var(--clay)}
.gauge-mark{position:absolute;top:-3px;width:2px;height:18px;background:var(--paper);opacity:.75}
.gauge-legend{display:flex;justify-content:space-between;font-size:11px;margin-top:6px}
.gauge-legend .mono{font-weight:700}
.pick-meta{display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;margin-top:12px;color:var(--muted)}
.stake-box{margin-top:14px;border-top:1px solid var(--line);padding-top:12px;display:grid;gap:6px}
.stake-row{display:flex;justify-content:space-between;align-items:baseline}
.stake-k{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted)}
.stake-v{font-size:18px;font-weight:700}
.stake-v.ret{color:var(--mint)} .stake-v.ret.neg{color:var(--clay)}
.empty-big{color:var(--muted);font-size:15px;padding:30px 0}
.t-alta-txt{color:var(--mint)} .t-media-txt{color:var(--amber)} .t-bassa-txt{color:var(--clay)}
.combos{margin-top:44px}
.combo-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.combo{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;border-top:3px solid var(--amber)}
.combo-top{display:flex;justify-content:space-between;margin-bottom:10px;font-size:12px}
.combo-odds{color:var(--amber);font-weight:700}
.leg{display:grid;grid-template-columns:1fr auto;gap:4px 10px;padding:8px 0;border-bottom:1px dotted var(--line)}
.leg-match{grid-column:1/-1;font-size:11px} .leg-label{font-size:13.5px}
.combo-foot{font-size:11px;color:var(--muted);margin-top:10px}
.hist{margin-top:48px}
.hist-summary{font-size:13px;color:var(--muted);margin-bottom:14px}
.value{margin-top:8px;background:linear-gradient(180deg,#16221c,#131a17);
  border:1px solid #2b4437;border-radius:12px;padding:20px 22px}
.val-intro{font-size:13px;color:var(--muted);max-width:640px;margin:6px 0 16px}
.val-empty{font-size:14px;color:var(--muted);padding:8px 0}
.val-list{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:8px;overflow:hidden}
.vrow{display:grid;grid-template-columns:1fr auto auto auto;gap:14px;align-items:center;
  background:#141a17;padding:11px 14px;font-size:13.5px}
.vmatch{min-width:0}
.vplay{color:var(--paper)}
.vprob{font-weight:700}
.vodd{color:var(--amber)}
.vedge{color:var(--mint);font-weight:700}
@media(max-width:560px){.vrow{grid-template-columns:1fr auto;gap:6px 12px}}
.hist-summary b{color:var(--paper)}
.hrow{display:grid;grid-template-columns:74px 1fr auto 22px;gap:12px;align-items:center;
  padding:9px 0;border-bottom:1px solid var(--line);font-size:13px}
.hrow .hdate{font-family:'Space Mono',monospace;font-size:11px;color:var(--muted)}
.hrow .hplay{color:var(--muted);margin-left:4px}
.hrow .hodd{font-family:'Space Mono',monospace}
.hicon{font-weight:700;text-align:center;font-family:'Space Mono',monospace}
.hicon.won{color:var(--mint)} .hicon.lost{color:var(--clay)} .hicon.pending{color:var(--muted)}
"""


def _bar(s):
    lower = int(round(s["lower"] * 100)); p = int(round(s["p"] * 100))
    return f"""
      <div class="gauge" title="Prob. prudente {lower}% (grezza {p}%)">
        <div class="gauge-fill t-{s['tier']}" style="width:{lower}%"></div>
        <div class="gauge-mark" style="left:{IMPLIED_15}%"></div>
      </div>
      <div class="gauge-legend"><span class="mono">{lower}%</span>
        <span class="muted">soglia 1.5 = {IMPLIED_15:.0f}%</span></div>"""


def _pick(s):
    odd_txt = f'{s["odd"]:.2f}' if s.get("odd") else "\u2014"
    return f"""
      <div class="pick">
        <div class="pick-head"><span class="pick-label">Gioca {s['label']}</span>
          <span class="chip t-{s['tier']}">{TIER_LABEL[s['tier']]}</span></div>
        {_bar(s)}
        <div class="pick-meta mono"><span>campione {s['n']} gare</span>
          <span class="quota">quota {odd_txt}</span></div>
      </div>"""


def _match_card(m, idx):
    top = m["top"]
    odd = top["odd"] if top.get("odd") else 1.5
    return f"""
    <article class="slip" data-p="{top['lower']}" data-odd="{odd}">
      <div class="slip-top"><span class="date mono">{_itdate(m['date'])}</span>
        <span class="idx mono">#{idx:02d}</span></div>
      <h2 class="teams"><span>{m['home']}</span><em>vs</em><span>{m['away']}</span></h2>
      <div class="perf"></div>
      {_pick(top)}
      <div class="stake-box">
        <div class="stake-row"><span class="stake-k mono">punta consigliata</span>
          <span class="stake-v mono" data-stake>\u2014</span></div>
      </div>
    </article>"""


def _combo_card(c, i):
    legs = "".join(
        f'<div class="leg"><span class="leg-match mono muted">{l["match"]}</span>'
        f'<span class="leg-label">{l["label"]}</span>'
        f'<span class="mono">{int(round(l["lower"]*100))}%</span></div>' for l in c["legs"])
    return f"""
    <article class="combo">
      <div class="combo-top"><span class="mono muted">DOPPIA #{i}</span>
        <span class="combo-odds mono">quota equa ~{c['fair_odds']}</span></div>
      {legs}
      <div class="combo-foot mono">prob. combinata stimata {int(round(c['prob']*100))}% \u00b7 gambe da partite diverse</div>
    </article>"""


def _history_block(p):
    h = p.get("history") or {}
    rows = h.get("rows", [])
    if not rows:
        return ""
    settled = h.get("settled", 0); won = h.get("won", 0)
    rate = f"{round(100*won/settled)}%" if settled else "\u2014"
    summary = (f'<div class="hist-summary">Consigli conclusi: <b>{won}</b> vinti su '
               f'<b>{settled}</b> (<b>{rate}</b>). Si aggiorna dopo ogni giornata.</div>')
    icon = {"won": "\u2713", "lost": "\u2717", "pending": "\u00b7"}
    lab = {"won": "won", "lost": "lost", "pending": "pending"}
    trs = ""
    for r in rows:
        st = r.get("status", "pending")
        odd = f'{r["odd"]:.2f}' if r.get("odd") else "\u2014"
        trs += (f'<div class="hrow"><span class="hdate">{_itdate(r["date"])}</span>'
                f'<span class="hmatch"><b>{r["home"]} - {r["away"]}</b> '
                f'<span class="hplay">{r["label"]}</span></span>'
                f'<span class="hodd">{odd}</span>'
                f'<span class="hicon {lab[st]}">{icon[st]}</span></div>')
    return (f'<section class="hist"><h3 class="eyebrow">Storico consigli</h3>'
            f'{summary}<div class="hist-list">{trs}</div></section>')


def _value_block(p):
    picks = p.get("value_picks", [])
    band = p.get("value_band", (1.7, 3.0))
    head = f'<h3 class="eyebrow">Occasioni di valore \u00b7 quota {band[0]:.1f}\u2013{band[1]:.1f}</h3>'
    intro = ('<div class="val-intro">Giocate a quota pi\u00f9 alta dove la nostra stima statistica '
             'batte la quota del bookmaker. Sono rare e si perdono pi\u00f9 spesso delle "sicure": '
             'sono le uniche, per\u00f2, dove la matematica \u00e8 dalla tua parte.</div>')
    if not picks:
        return (f'<section class="value">{head}{intro}'
                '<div class="val-empty">Nessuna occasione di valore in questo turno. '
                '\u00c8 normale: il banco prezza bene, e le vere occasioni sono poche. '
                'Meglio non giocare che giocare senza valore.</div></section>')
    rows = ""
    for v in picks:
        edge = v["edge"] * 100
        rows += (f'<div class="vrow"><span class="vmatch"><b>{v["match"]}</b></span>'
                 f'<span class="vplay">{v["label"]}</span>'
                 f'<span class="vprob mono t-{v["tier"]}-txt">{int(round(v["lower"]*100))}%</span>'
                 f'<span class="vodd mono">quota {v["odd"]:.2f}</span>'
                 f'<span class="vedge mono">+{edge:.0f}% valore</span></div>')
    return f'<section class="value">{head}{intro}<div class="val-list">{rows}</div></section>'


def render(p):
    cards = "".join(_match_card(m, i + 1) for i, m in enumerate(p["matches"]))
    if not cards:
        cards = ('<p class="empty-big">Nessuna giocata sopra soglia per le prossime '
                 'gare. Ricontrolla dopo il prossimo aggiornamento.</p>')
    combos = "".join(_combo_card(c, i + 1) for i, c in enumerate(p["combos"]))
    combos_block = f"""
      <section class="combos"><h3 class="eyebrow">Multiple \u00b7 massimo 3 \u00b7 gambe da partite diverse</h3>
        <div class="combo-grid">{combos}</div></section>""" if combos else ""
    history_block = _history_block(p)
    value_block = _value_block(p)
    seasons = ", ".join(str(s) for s in p["seasons"])
    n_picks = len(p["matches"])
    return f"""<!DOCTYPE html><html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Schedina free money</title>
{FONTS}<style>{SITE_CSS}</style></head><body><div class="wrap">
  <header>
    <div>
      <div class="brand">Schedina<br><em>free money</em></div>
      <div class="nav"><a href="come-funziona.html">Come funziona &rarr;</a></div>
    </div>
    <div class="meta-line">
      <div class="muted">aggiornato</div><div class="mono">{p['generated']}</div>
      <div class="muted" style="margin-top:8px">base storica</div>
      <div class="mono">{p['n_matches_analyzed']} gare \u00b7 {seasons}</div>
    </div>
  </header>

  <section class="bank">
    <div class="bank-grid">
      <div class="field"><label>Budget mensile (\u20ac)</label>
        <input id="budget" type="number" min="0" step="10" placeholder="es. 100"></div>
      <input id="rounds" type="hidden" value="4">
      <div class="bank-out">
        <div><div class="k">Puntata / giornata</div><div class="v" id="tot-stake">\u2014</div></div>
      </div>
    </div>
    <div class="bank-note">Il budget viene distribuito in parti uguali sulle giocate consigliate,
      per darti un'idea di quanto puntare su ciascuna. Sono previsioni statistiche, non certezze:
      giocate solo importi che potete permettervi di perdere.</div>
  </section>

  {value_block}

  <h3 class="eyebrow" style="margin-top:44px">Singole \u00b7 il consiglio del sistema</h3>
  <div class="grid" id="grid">{cards}</div>

  {combos_block}

  {history_block}

  <footer>Strumento statistico a uso personale tra amici. I consigli nascono dallo storico delle
    partite, non da certezze: nel breve periodo si vince e si perde. 18+. Il gioco pu\u00f2 causare
    dipendenza. <a href="come-funziona.html">Come funziona</a></footer>
</div>
<script>
(function(){{
  var budget=document.getElementById('budget');
  var rounds=document.getElementById('rounds');
  var slips=Array.prototype.slice.call(document.querySelectorAll('.slip[data-p]'));
  try{{ if(localStorage.getItem('sfm_budget')) budget.value=localStorage.getItem('sfm_budget'); }}catch(e){{}}
  function euro(x){{ return '\u20ac'+(Math.round(x*100)/100).toFixed(2); }}
  function recompute(){{
    var B=parseFloat(budget.value)||0;
    var R=Math.max(1,parseInt(rounds.value)||1);
    var perRound=B/R, N=slips.length, totStake=0;
    slips.forEach(function(el){{
      var stake=N?perRound/N:0;
      totStake+=stake;
      el.querySelector('[data-stake]').textContent=B?euro(stake):'\u2014';
    }});
    document.getElementById('tot-stake').textContent=B?euro(totStake):'\u2014';
    try{{ localStorage.setItem('sfm_budget',budget.value); }}catch(e){{}}
  }}
  budget.addEventListener('input',recompute);
  recompute();
}})();
</script>
</body></html>"""


def render_howto(p):
    seasons = ", ".join(str(s) for s in p["seasons"])
    n = p["n_matches_analyzed"]
    stats = [
        (f"{n}", "partite reali analizzate"),
        (f"{len(p['seasons'])}", "stagioni di storico"),
        ("4", "mercati (corner, gol, cartellini, gol/gol)"),
        ("ogni giorno", "aggiornamento automatico"),
    ]
    stat_html = "".join(
        f'<div class="stat"><div class="stat-n mono">{v}</div>'
        f'<div class="stat-k">{k}</div></div>' for v, k in stats)
    css = BASE_CSS + """
.hero{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;font-weight:700;
  font-size:clamp(38px,7vw,72px);line-height:.92;margin:30px 0 10px}
.hero em{color:var(--amber);font-style:normal}
.lead{font-size:17px;color:var(--paper);max-width:620px;margin-bottom:34px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:0 0 44px}
.stat{background:var(--panel);padding:22px 18px}
.stat-n{font-size:30px;font-weight:700;color:var(--mint)}
.stat-k{font-size:12px;color:var(--muted);margin-top:6px;text-transform:uppercase;letter-spacing:1px}
.step{display:grid;grid-template-columns:56px 1fr;gap:18px;padding:26px 0;border-top:1px solid var(--line)}
.step-n{font-family:'Barlow Condensed',sans-serif;font-size:40px;font-weight:700;color:var(--amber);line-height:1}
.step h3{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;letter-spacing:1px;
  font-size:22px;margin:0 0 8px}
.step p{margin:0 0 8px;color:#cfd3da;font-size:15px}
.callout{background:rgba(224,184,76,.08);border-left:3px solid var(--amber);
  padding:16px 18px;border-radius:8px;margin:34px 0;font-size:14.5px;color:#e6e3db}
"""
    steps = [
        ("01", "Raccogliamo i dati veri",
         f"Ogni giorno il sistema scarica automaticamente le partite di Serie A "
         f"(stagioni {seasons}) da un servizio dati professionale: risultati, corner, "
         f"cartellini, gol \u2014 partita per partita. Ad oggi sono {n} partite in archivio, "
         f"e il numero cresce a ogni giornata di campionato."),
        ("02", "Misuriamo come gioca ogni squadra",
         "Per ogni squadra calcoliamo con che frequenza accadono certi eventi \u2014 quante "
         "volte si superano i 7,5 corner, quante volte escono almeno 2 gol, e cos\u00ec via \u2014 "
         "tenendo separate le gare in casa da quelle in trasferta, perch\u00e9 una squadra "
         "gioca in modo diverso nei due casi."),
        ("03", "Stimiamo le prossime partite, con prudenza",
         "Per ogni gara futura combiniamo i dati delle due squadre e stimiamo la probabilit\u00e0 "
         "di ciascun evento. Non usiamo la percentuale grezza: applichiamo una correzione "
         "statistica (il limite di Wilson) che abbassa la fiducia quando le partite alle "
         "spalle sono poche. Dieci partite non valgono come cento, e il sistema lo sa."),
        ("04", "Confrontiamo con la quota reale",
         "Una probabilit\u00e0 alta non basta: conta il prezzo. Il sito mostra la quota reale di "
         "Bet365 accanto a ogni giocata e segnala se c'\u00e8 davvero \u201cvalore\u201d \u2014 cio\u00e8 se la "
         "nostra stima batte quella implicita nella quota. Se non c'\u00e8 valore, te lo dice."),
        ("05", "Ti mostriamo solo le migliori",
         "Tra tutte le giocate possibili, il sito seleziona le pi\u00f9 solide della giornata, "
         "una per partita, variando i mercati. Un semaforo (verde/giallo) ti dice quanto "
         "fidarti di ciascuna."),
    ]
    steps_html = "".join(
        f'<div class="step"><div class="step-n">{n_}</div><div><h3>{t}</h3><p>{b}</p></div></div>'
        for n_, t, b in steps)
    return f"""<!DOCTYPE html><html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Come funziona \u00b7 Schedina free money</title>
{FONTS}<style>{css}</style></head><body><div class="wrap">
  <div class="nav"><a href="index.html">&larr; Torna alle giocate</a></div>
  <h1 class="hero">Come <em>funziona</em></h1>
  <p class="lead">Dietro ogni giocata non c'\u00e8 una sensazione, ma centinaia di partite reali
    macinate ogni giorno da un motore statistico. Ecco tutto quello che c'\u00e8 sotto il cofano \u2014
    spiegato senza trucchi.</p>
  <div class="stats">{stat_html}</div>
  {steps_html}
  <div class="callout"><strong>La verit\u00e0, detta chiara:</strong> nessuno strumento indovina la
    maggior parte delle scommesse \u2014 se esistesse, i bookmaker sarebbero gi\u00e0 falliti. Questo
    sistema non promette vincite: mostra dove i numeri sono pi\u00f9 solidi e dove la quota offre
    valore reale. \u00c8 un aiuto per ragionare, non una macchina da soldi. Giocate per divertirvi,
    con soldi che potete permettervi di perdere.</div>
  <footer>Creato tra amici, per ragionare meglio prima di una giocata. 18+. Il gioco pu\u00f2 causare
    dipendenza. <a href="index.html">Torna alle giocate</a></footer>
</div></body></html>"""
