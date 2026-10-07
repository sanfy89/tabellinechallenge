# Tabelline Challenge — Design

Skill Alexa (it-IT) per far esercitare i bambini sulle tabelline con un quiz a turni, da 1 a 4 giocatori.

## Obiettivo

Un gioco tipo quiz: Alexa fa una moltiplicazione al giocatore di turno, che guadagna o perde punti. Ogni giocatore riceve solo domande sulle tabelline che ha già studiato.

## Infrastruttura

- Skill **Alexa-hosted** (gratuita, nessun account AWS).
- Backend **Python** con **ASK SDK for Python** (`ask-sdk-core`).
- Nessun database: lo stato della partita vive nei **session attributes**. Se la sessione cade, la partita è persa.
- Locale: `it-IT`.
- Nome di invocazione: **"tabelline challenge"** ("Alexa, apri tabelline challenge").

## Flusso di gioco

### Configurazione
1. Apertura: "Benvenuti a Tabelline Challenge! Quanti giocatori siete? Da uno a quattro."
2. Per ogni giocatore N (1..numero giocatori): "Giocatore N, fino a che tabellina conosci?" Valore accettato: intero 1..10.
3. Poi inizia la partita.

I giocatori sono identificati solo come "Giocatore 1", "Giocatore 2", ecc. (niente nomi).

### Turni
- Ordine fisso: Giocatore 1, 2, …, N, poi di nuovo 1.
- **5 domande a testa** (partita = 5 × N domande regolari).
- Domanda: "Giocatore 2: quanto fa 7 per 6?"

### Punteggio
- Risposta giusta: **+1**.
- Risposta sbagliata: **−1**. Il punteggio può andare sotto zero.
- Nessuna risposta: Alexa ripete la domanda una volta (reprompt). Se arriva una risposta non numerica o un secondo silenzio, conta come **sbagliata**.

### Furto (domanda rubabile)
Quando il giocatore di turno sbaglia:
1. La domanda passa **una sola volta** al giocatore successivo nell'ordine dei turni.
2. Il furto avviene **solo se** la domanda rientra nel livello del ladro (vedi "Generazione domande": almeno un fattore ≤ livello del ladro). Altrimenti il furto salta.
3. Con un solo giocatore il furto non esiste.
4. Ladro giusto: +1. Ladro sbagliato: −1.
5. Dopo il furto (o se il furto salta) Alexa dice la soluzione ("7 per 6 fa 42") e il turno passa normalmente al giocatore successivo a quello che aveva la domanda originale. Il furto non conta come domanda del ladro.

### Riepilogo
Alla fine di ogni giro completo (tutti i giocatori hanno avuto una domanda) Alexa legge i punteggi.

### Fine partita
- Dopo 5 × N domande regolari: classifica e vincitore.
- **Spareggio**: se più giocatori sono a pari punti in testa, ognuno di loro riceve una domanda (senza furto, stesse regole +1/−1). Si ripete finché resta un solo giocatore in testa.
- Con un solo giocatore: si annuncia solo il punteggio finale.
- La sessione termina dopo l'annuncio.

### Comandi sempre disponibili
- **"ripeti"**: ripete la domanda o la richiesta corrente.
- **"punteggio"**: legge i punteggi attuali, poi ripete la domanda corrente.
- **"aiuto"**: spiega le regole in breve, poi ripete la domanda o la richiesta corrente.
- **"basta" / "stop"**: legge la classifica attuale ed esce.

## Generazione domande

Per un giocatore con livello L (1..10):
- Fattore "conosciuto" `a`: intero in [2, L]; se L = 1, allora `a = 1`.
- Altro fattore `b`: intero in [2, 10].
- L'ordine con cui vengono detti è casuale (si può sentire "a per b" o "b per a").
- Nella stessa partita non si ripete la stessa coppia (non ordinata) allo stesso giocatore, finché ce ne sono di nuove disponibili. Esaurite quelle, le ripetizioni sono ammesse.

Una domanda `x × y` **rientra nel livello** L di un giocatore se `min(x, y) ≤ L`, oppure se L = 1 e uno dei fattori è 1.

Esempio: L = 8 → 9 × 8 sì, 9 × 9 no.

## Gestione errori

- Numero giocatori fuori da 1..4: "Potete essere da uno a quattro giocatori. Quanti siete?"
- Livello fuori da 1..10: "Dimmi un numero da uno a dieci."
- Frase non capita (FallbackIntent o numero assente) in fase di configurazione: si ripete la richiesta senza penalità.
- Frase non capita durante una domanda: "Non ho capito, dimmi solo il numero." e si ripete la domanda. La seconda volta consecutiva conta come risposta sbagliata.

## Interaction model (it-IT)

- `NumeroIntent`: slot `numero` (AMAZON.NUMBER). Esempi: "{numero}", "fa {numero}", "è {numero}", "siamo {numero}", "fino al {numero}", "la tabellina del {numero}".
- `RipetiIntent`: "ripeti", "puoi ripetere", "non ho sentito".
- `PunteggioIntent`: "punteggio", "quanti punti abbiamo", "classifica".
- Built-in: `AMAZON.HelpIntent`, `AMAZON.StopIntent`, `AMAZON.CancelIntent`, `AMAZON.FallbackIntent`, `AMAZON.NavigateHomeIntent`.

## Architettura del codice

```
lambda/
  lambda_function.py   # handler ASK: traducono intent → chiamate a game, stato ↔ session attributes
  game.py              # logica pura: stato, fasi, turni, punti, furto, spareggio, fine
  questions.py         # generazione domande e controllo "rientra nel livello"
  speech.py            # testi in italiano, complimenti variati, riepiloghi
  requirements.txt
skill-package/
  skill.json
  interactionModels/custom/it-IT.json
tests/
  test_game.py
  test_questions.py
README.md              # istruzioni di setup su Alexa Developer Console
```

- `game.py` non importa nulla di ASK. Lo stato è un dizionario serializzabile in JSON (per i session attributes). Espone funzioni come `nuova_partita()`, `imposta_giocatori(stato, n)`, `imposta_livello(stato, livello)`, `rispondi(stato, numero)` che restituiscono il nuovo stato e un "evento" (cosa è successo) che `speech.py` trasforma in testo.
- Fasi: `NUM_GIOCATORI` → `LIVELLI` → `DOMANDA` ⇄ `FURTO` → (`SPAREGGIO`) → `FINE`.
- Il generatore casuale è iniettabile in `questions.py` per test deterministici.

## Test

- **pytest** su `game.py` e `questions.py`:
  - domande sempre entro il livello del giocatore (incluso L = 1)
  - +1 / −1, punteggi negativi
  - furto: passa al successivo, salta se fuori livello, assente con un solo giocatore, nessun furto in spareggio
  - rotazione dei turni dopo il furto
  - riepilogo a fine giro
  - fine partita dopo 5 × N domande, spareggio tra due e tra tre giocatori
  - risposta non capita due volte = sbagliata
- **Manuale**: simulatore della Alexa Developer Console, partite da 1 e da 3 giocatori.

## Fuori scopo

- Nomi dei giocatori, memoria tra sessioni, statistiche sugli errori.
- Schermo (APL), suoni, musica.
- Lingue diverse dall'italiano.
