# Schedina · Serie A value — guida rapida

Uno strumento che scarica lo storico Serie A, calcola le probabilità
**prudenti** di corner/gol/cartellini e genera un sito da mettere sul tuo
dominio, con la miglior giocata per ogni prossima partita e qualche doppia
a bassa varianza puntata su quota ~1.5.

**Non serve saper programmare.** Servono 5 comandi in tutto. Nessuna libreria
da installare: usa solo Python "di serie".

---

## 0) Una volta sola: prendi la chiave (nuova!)

1. Vai su api-football.com, registrati, apri la dashboard e **genera la chiave**.
   Se ne avevi già condivisa una, **rigenerala** (quella vecchia è da buttare).
2. Non incollarla mai in chat né dentro pagine pubblicate.

## 1) Installa Python (se non ce l'hai)

- Windows/Mac: scarica da python.org, installa, spunta *"Add Python to PATH"*.
- Verifica aprendo il Terminale (Mac) o il Prompt dei comandi (Windows) e
  scrivendo:  `python --version`  (deve rispondere con un numero 3.x).

## 2) Metti la chiave

Apri `config.py` e incolla la chiave dentro le virgolette di `API_KEY`.
(Va bene per iniziare. Più avanti la spostiamo in una variabile d'ambiente
così non resta scritta nel file — te lo spiego quando vuoi.)

## 3) Verifica gli id delle squadre

    python fetch.py teams

Ti stampa nome → id di tutte le squadre. Controlla che gli id in `config.py`
(sezione `TEAMS`) siano giusti e correggili se serve. *(1 richiesta)*

## 4) Scarica i dati

    python fetch.py

Scarica partite e statistiche delle tue squadre. La parte "cara" è 1 richiesta
per partita. Col piano gratuito (100/giorno) se finisci le richieste **non è un
problema**: rilancia lo stesso comando il giorno dopo e riprende da dove era.
Col piano da 19$ le fai tutte in un colpo.

Consiglio per iniziare piano: in `config.py` metti `SEASONS = [2025]` e 3-4
squadre, poi allarghi.

## 5) Genera il sito

    python analyze.py

Crea `site/index.html`. Aprilo con doppio clic per vederlo. Quando ti piace,
carica il file `site/index.html` sul tuo hosting/dominio (va bene qualsiasi
hosting statico: Netlify, GitHub Pages, Altervista, il tuo spazio web…).

Prima di ogni giornata di campionato: ripeti i passi **4** e **5** per
aggiornare le partite in arrivo.

---

---

## Metterlo online e farlo aggiornare DA SOLO (consigliato)

Obiettivo: un sito con un indirizzo web che tu e i tuoi amici aprite quando
volete, che si aggiorna ogni mattina senza il tuo computer acceso. Tutto
gratis con **GitHub Pages** (ospita il sito) + **GitHub Actions** (il
"robottino" che aggiorna). Una volta impostato, non tocchi più niente.

Si fa una volta sola, in circa 15 minuti:

1. **Crea un account** gratuito su github.com.
2. **Crea un repository** (in alto a destra: New repository). Dagli un nome,
   lascialo **Public**, crea.
3. **Carica i file** del progetto: nel repository clicca *Add file → Upload
   files*, trascina TUTTA la cartella del progetto (compresa la cartella
   nascosta `.github`), e conferma con *Commit changes*.
4. **Metti la chiave al sicuro**: nel repository vai su *Settings → Secrets and
   variables → Actions → New repository secret*. Nome: `APIFOOTBALL_KEY`.
   Valore: la tua chiave. Salva. (Così la chiave resta cifrata e NON finisce
   mai nel sito pubblico.)
5. **Accendi Pages**: *Settings → Pages*. In "Build and deployment", come
   *Source* scegli **GitHub Actions**.
6. **Primo avvio a mano**: vai su *Actions → Aggiorna schedina → Run workflow*.
   Parte, scarica, pubblica. Al termine, in *Settings → Pages* trovi
   **l'indirizzo del tuo sito** (tipo `https://tuonome.github.io/nome-repo`).
   Quello è il link da mandare all'amico.

Da qui in poi: ogni giorno alle 8:00 (ora italiana) il robottino si aggiorna
da solo. Vuoi forzarlo subito? *Actions → Run workflow*. Vuoi cambiare
squadre o stagioni? Modifichi `config.py` dal sito di GitHub e si riaggiorna.

> **Il primo giorno** il robottino riempie lo storico e potrebbe fermarsi al
> limite delle 100 richieste: è normale, riprende da solo il giorno dopo. Dopo
> che lo storico è pieno, ogni aggiornamento costa pochissime richieste.

*(In alternativa a GitHub Pages puoi usare qualsiasi hosting statico —
Netlify, Altervista, il tuo spazio web — ma dovresti aggiornarlo a mano o
configurare tu l'automazione. GitHub è l'unico che fa hosting **e**
automazione gratis in un colpo solo: per questo è consigliato.)*

---

## Domande frequenti

**Ogni quanto si aggiorna?**
Se usi GitHub (sopra): da solo, una volta al giorno, più il pulsante "Run
workflow" per forzarlo. Se lo usi solo sul tuo PC: quando lanci i due comandi.

**Le partite future da dove arrivano?**
Dallo stesso scarico dei dati. Quando si chiede il calendario di una squadra,
l'API restituisce **tutte** le partite della stagione, incluse quelle non
ancora giocate: quelle "da giocare" diventano le prossime gare nel sito.

**Si aggiornano da sole anche le partite future?**
Sì. Lo scarico ri-legge sempre la stagione in corso, quindi appena viene
fissata una nuova giornata (o cambia un orario/rinvio) il sito lo recepisce al
giro dopo, senza che tu faccia nulla.

**Durante la stagione i dati si arricchiscono?**
Sì, ed è automatico. Ogni aggiornamento controlla le partite appena finite e
ne scarica le statistiche (corner, cartellini), aggiungendole allo storico. Più
va avanti la stagione, più il campione cresce e le percentuali diventano
affidabili — proprio la cosa che rende utile lo strumento nel tempo.

---

## Come leggere il sito

- La **barra** di ogni giocata mostra la probabilità *prudente* (non quella
  grezza): tiene conto di quante partite ci sono dietro. Poche partite → barra
  più corta anche se la percentuale grezza è alta.
- La **tacca chiara** sulla barra è al 66,7% = la soglia della quota 1.5.
  Se la barra la supera con margine, la giocata ha senso a 1.5.
- **Confidenza alta/media/bassa**: dipende da campione + margine.
- **Quota equa**: è l'inverso della probabilità. Confrontala con la quota vera
  del bookmaker: c'è valore solo se il bookmaker offre *di più* della quota equa.

## Da sapere, sul serio

Nessun modello indovina 8-9 gare su 10 nel lungo periodo. Questo strumento
cerca i **pochi** casi solidi e ti dice quanto fidarti. È un gioco tra amici:
punta solo importi che puoi perdere senza problemi.

## File del progetto

- `config.py`  → l'unico file da modificare (chiave, squadre, stagioni, soglie)
- `fetch.py`   → scarica i dati (resumabile, rispetta il limite giornaliero)
- `analyze.py` → calcola le probabilità e genera il sito
- `render.py`  → l'aspetto grafico del sito
- `make_demo.py` → dati finti per una demo senza chiave (`python make_demo.py`)
- `data/`      → i dati scaricati (cache)
- `site/`      → il sito generato da caricare online
