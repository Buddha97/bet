# =============================================================
#  CONFIGURAZIONE  —  modifica solo questo file
# =============================================================
#  Qui decidi: quali squadre, quali stagioni, e quanto vuoi
#  essere prudente nei suggerimenti. Non serve toccare altro.
# =============================================================

# La tua chiave API-Football. NON metterla qui se pubblichi il codice:
# lasciala in una variabile d'ambiente (vedi README). Per i test locali
# puoi incollarla qui temporaneamente.
API_KEY = "INCOLLA_QUI_LA_TUA_CHIAVE"

# Serie A su API-Football ha id = 135. Non cambiare, salvo tu voglia un altro campionato.
LEAGUE_ID = 135

# Quanti giorni in avanti guardare per le "prossime gare".
#  14 = circa la prossima giornata o due. Alza per vederne di piu'.
UPCOMING_DAYS = 14

# Bookmaker per le quote reali. Bet365 = 8 su API-Football.
BET365_ID = 8

# Limite di richieste al giorno del tuo piano.
#  Piano gratuito = 100. Se passi al piano a pagamento, alzalo (es. 7500).
DAILY_LIMIT = 7500      # piano PRO

# Pausa tra una richiesta e l'altra, in secondi.
#  Il piano gratuito ammette ~10 richieste/minuto: 7s e' prudente.
#  Col piano a pagamento puoi abbassarla (es. 1).
REQUEST_PACING_SECONDS = 2   # PRO consente piu' richieste al minuto

# Stagioni da scaricare (anno d'inizio del campionato).
# Piano gratuito: parti con 1-2 stagioni per non finire le richieste.
SEASONS = [2024, 2025, 2026]

# Le squadre che ti interessano, con il loro id API-Football.
# ATTENZIONE: verifica gli id col comando  ->  python fetch.py teams
# (gli id qui sotto sono quelli tipici ma vanno confermati).
TEAMS = {
    "Roma":          497,
    "Inter":         505,
    "Napoli":        492,
    "Lecce":         867,
    "Milan":         489,
    "Atalanta":      499,
    "Juventus":      496,
    "Cagliari":      490,
    "Lazio":         487,
    "Udinese":       494,
    "Como":          895,
    "Torino":        503,
    "Sassuolo":      488,
    "Bologna":       500,
    "Parma":         523,
    "Frosinone":     512,
    "Venezia":       517,
    "Genoa":         495,
    "Monza":         1579,
    "Fiorentina":    502,
}

# --- Soglie di prudenza -------------------------------------
# Una quota 1.5 = probabilita' implicita del 66.7%. Per suggerire
# una singola a 1.5 pretendiamo che la probabilita' STORICA PRUDENTE
# (limite inferiore, vedi analyze.py) superi questa soglia:
MIN_PROB_SINGLE = 0.68     # ~68%: soglia con margine reale sopra il 66.7% della quota 1.5

# Per una doppia combinata che fa ~1.5, ogni gamba deve essere quasi certa:
MIN_PROB_COMBO_LEG = 0.75   # gamba di doppia: solida ma non estrema

# Campione minimo di partite sotto cui NON ci fidiamo di una percentuale:
MIN_SAMPLE = 12

# Mercati da valutare. Le soglie (linee) sono quelle piu' comuni.
# Corner protagonista: mostra la linea corner piu' ALTA che resti almeno a
# questa probabilita' (piu' alta = previsione piu' informativa ma piu' rischiosa).
CORNER_HEADLINE_MINPROB = 0.68   # allineata alla soglia: la linea corner scelta resta solida

# --- Caccia al valore -------------------------------------
# Cerca giocate a quota piu' alta dove la nostra probabilita' prudente
# batte la probabilita' implicita nella quota reale (Bet365).
VALUE_ODDS_MIN = 1.7    # fascia di quota da esplorare: minimo
VALUE_ODDS_MAX = 3.0    # massimo

CORNER_LINES = [7.5, 8.5, 9.5, 10.5]   # calci d'angolo TOTALI di partita
GOAL_LINES   = [1.5, 2.5, 3.5]         # gol totali di partita
CARD_LINES   = [3.5, 4.5]              # cartellini (gialli+rossi) totali
