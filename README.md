# Tabelline Challenge

Skill Alexa in italiano: una gara sulle tabelline da 1 a 4 giocatori.
"Alexa, apri tabelline challenge."

## Regole
- Ogni giocatore dice fino a che tabellina conosce (da 1 a 10): riceverà solo moltiplicazioni di quelle tabelline.
- A turno, 5 domande a testa. Giusta +1, sbagliata −1.
- Se sbagli, il giocatore successivo può rubare la domanda (se la conosce).
- Vince chi ha più punti; in caso di parità si fa uno spareggio.
- Comandi: "ripeti", "punteggio", "aiuto", "basta".

## Pubblicazione (Alexa-hosted, gratis)
1. Vai su https://developer.amazon.com/alexa/console/ask e accedi con lo stesso account Amazon del tuo Echo.
2. **Create Skill** → nome "Tabelline Challenge", lingua **Italian (IT)**, tipo **Other → Custom**, hosting **Alexa-hosted (Python)**, template **Start from Scratch**.
3. Scheda **Build → Interaction Model → JSON Editor**: incolla il contenuto di `skill-package/interactionModels/custom/it-IT.json`, poi **Save** e **Build skill**.
4. Scheda **Code**: nella cartella `lambda` sostituisci `lambda_function.py` e `requirements.txt` con quelli di questo progetto e crea `game.py`, `questions.py`, `speech.py` copiandone il contenuto. Poi **Deploy**.
5. Scheda **Test**: imposta "Skill testing is enabled in" su **Development** e prova "apri tabelline challenge".
6. La skill è subito disponibile sugli Echo collegati al tuo account (non serve pubblicarla).

## Sviluppo
```bash
python3 -m venv --without-pip .venv
curl -sSfL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```
(Se il tuo Python ha `ensurepip`, basta `python3 -m venv .venv`.)

La logica di gioco è in `lambda/game.py`, le frasi in `lambda/speech.py`, la generazione delle domande in `lambda/questions.py`, gli handler Alexa in `lambda/lambda_function.py`.
