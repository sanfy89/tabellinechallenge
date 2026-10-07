# Tabelline Challenge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skill Alexa (it-IT, Alexa-hosted, Python) per una gara a turni sulle tabelline da 1 a 4 giocatori.

**Architecture:** Logica di gioco pura in `game.py` (stato = dizionario JSON-serializzabile, le funzioni mutano lo stato e restituiscono una lista di "eventi"). `questions.py` genera le domande, `speech.py` trasforma eventi + stato in frasi italiane, `lambda_function.py` contiene handler ASK sottili che salvano lo stato nei session attributes.

**Tech Stack:** Python 3.12, ask-sdk-core 1.19, pytest.

## Global Constraints

- Locale `it-IT`; nome di invocazione `tabelline challenge`.
- Giocatori 1..4, identificati come "giocatore N". Livello 1..10 per giocatore.
- Domanda per livello L: un fattore in [2, L] (se L = 1 il fattore è 1), l'altro in [2, 10]; ordine casuale; niente ripetizioni della stessa coppia allo stesso giocatore finché ce ne sono di nuove.
- `rientra_nel_livello(x, y, L)` ⇔ `min(x, y) <= L`.
- Giusta +1, sbagliata −1, punti negativi ammessi.
- Furto: una volta, al giocatore successivo, solo se la domanda rientra nel suo livello; niente furto con 1 giocatore o in spareggio.
- 5 domande a testa; riepilogo a ogni giro completo (solo con più di un giocatore, non dopo l'ultima domanda); spareggio tra i pari in testa finché ne resta uno.
- Non capito durante una domanda: la prima volta si ripete, la seconda consecutiva conta come sbagliata. In configurazione mai penalità.
- Nessun database, nessun nome, nessuna APL.
- I comandi vengono eseguiti dalla root del progetto `/mnt/c/Users/sanfi/Documents/Dev/TabellineCeci` con il venv `.venv` (già creato, contiene pytest e ask-sdk-core).

## File Structure

```
.gitignore
pytest.ini                         # pythonpath = lambda
requirements-dev.txt               # pytest, ask-sdk-core
lambda/
  questions.py                     # generazione domande
  game.py                          # regole e stato
  speech.py                        # testi
  lambda_function.py               # handler ASK
  requirements.txt                 # ask-sdk-core
skill-package/interactionModels/custom/it-IT.json
tests/
  test_questions.py
  test_game.py
  test_speech.py
  test_lambda_function.py          # partita end-to-end tramite lambda_handler
README.md
```

---

### Task 1: Setup e generazione domande

**Files:**
- Create: `.gitignore`, `pytest.ini`, `requirements-dev.txt`, `lambda/questions.py`
- Test: `tests/test_questions.py`

**Interfaces:**
- Produces: `rientra_nel_livello(x: int, y: int, livello: int) -> bool`; `genera_domanda(livello: int, gia_fatte: list[list[int]], rng) -> list[int]` (restituisce `[x, y]`; `gia_fatte` contiene coppie ordinate `[min, max]`).

- [ ] **Step 1: File di setup**

`.gitignore`:
```
.venv/
__pycache__/
.pytest_cache/
```

`pytest.ini`:
```ini
[pytest]
pythonpath = lambda
testpaths = tests
```

`requirements-dev.txt`:
```
pytest
ask-sdk-core>=1.19.0
```

- [ ] **Step 2: Test che falliscono** — `tests/test_questions.py`

```python
import random

import pytest

from questions import genera_domanda, rientra_nel_livello


@pytest.mark.parametrize("x, y, livello, atteso", [
    (9, 8, 8, True),
    (8, 9, 8, True),
    (9, 9, 8, False),
    (1, 7, 1, True),
    (2, 7, 1, False),
    (10, 10, 10, True),
])
def test_rientra_nel_livello(x, y, livello, atteso):
    assert rientra_nel_livello(x, y, livello) is atteso


@pytest.mark.parametrize("livello", range(1, 11))
def test_domande_sempre_nel_livello(livello):
    rng = random.Random(livello)
    for _ in range(200):
        x, y = genera_domanda(livello, [], rng)
        assert rientra_nel_livello(x, y, livello)
        assert max(x, y) <= 10
        if livello == 1:
            assert 1 in (x, y)
        else:
            assert min(x, y) >= 2


def test_niente_ripetizioni_finche_possibile():
    rng = random.Random(0)
    fatte = []
    # livello 2: coppie possibili (2,2)..(2,10) = 9
    for _ in range(9):
        d = genera_domanda(2, fatte, rng)
        assert sorted(d) not in fatte
        fatte.append(sorted(d))
    d = genera_domanda(2, fatte, rng)
    assert sorted(d) in fatte


def test_ordine_dei_fattori_casuale():
    rng = random.Random(1)
    visti = {tuple(genera_domanda(2, [], rng)) for _ in range(300)}
    assert (2, 9) in visti and (9, 2) in visti
```

- [ ] **Step 3: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_questions.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'questions'`

- [ ] **Step 4: Implementazione** — `lambda/questions.py`

```python
"""Generazione delle moltiplicazioni in base al livello del giocatore."""
import random

MIN_FATTORE = 2
MAX_FATTORE = 10


def rientra_nel_livello(x, y, livello):
    """Vero se la moltiplicazione usa una tabellina che il giocatore conosce."""
    return min(x, y) <= livello


def genera_domanda(livello, gia_fatte, rng=random):
    """Restituisce [x, y], evitando le coppie in gia_fatte finché possibile."""
    noti = range(MIN_FATTORE, livello + 1) if livello >= MIN_FATTORE else [1]
    candidate = sorted({
        tuple(sorted((a, b)))
        for a in noti
        for b in range(MIN_FATTORE, MAX_FATTORE + 1)
    })
    nuove = [c for c in candidate if list(c) not in gia_fatte]
    x, y = rng.choice(nuove or candidate)
    if rng.random() < 0.5:
        x, y = y, x
    return [x, y]
```

- [ ] **Step 5: Verifica che passi**

Run: `.venv/bin/pytest tests/test_questions.py -q`
Expected: tutti PASS

- [ ] **Step 6: Commit**

```bash
git add .gitignore pytest.ini requirements-dev.txt lambda/questions.py tests/test_questions.py
git commit -m "Aggiunge generazione delle domande per livello"
```

---

### Task 2: game.py — configurazione partita

**Files:**
- Create: `lambda/game.py`
- Test: `tests/test_game.py`

**Interfaces:**
- Consumes: `genera_domanda`, `rientra_nel_livello` da `questions`.
- Produces:
  - costanti di fase `NUM_GIOCATORI, LIVELLI, DOMANDA, FURTO, FINE`; `MAX_GIOCATORI = 4`, `MAX_LIVELLO = 10`, `DOMANDE_A_TESTA = 5`
  - `nuova_partita() -> dict` con chiavi `fase, giocatori, livello_da_chiedere, turno, ladro, domanda, domande_fatte, non_capito, spareggio, pos_spareggio`; ogni giocatore è `{"livello": int|None, "punti": int, "fatte": list}`
  - `chi_risponde(stato) -> int`
  - `gestisci_numero(stato, numero: int|None, rng) -> list[dict]` (muta `stato`, restituisce eventi `{"tipo": ...}`)
  - tipi di evento in questo task: `non_capito`, `giocatori_non_validi`, `giocatori_impostati` (`numero`), `livello_non_valido`, `inizio`

- [ ] **Step 1: Test che falliscono** — `tests/test_game.py`

```python
import random

import game


def tipi(eventi):
    return [e["tipo"] for e in eventi]


def configura(livelli, seed=0):
    rng = random.Random(seed)
    stato = game.nuova_partita()
    game.gestisci_numero(stato, len(livelli), rng)
    eventi = []
    for livello in livelli:
        eventi = game.gestisci_numero(stato, livello, rng)
    return stato, rng, eventi


def test_nuova_partita_chiede_numero_giocatori():
    assert game.nuova_partita()["fase"] == game.NUM_GIOCATORI


def test_numero_giocatori_non_valido():
    stato = game.nuova_partita()
    for n in (0, 5):
        assert tipi(game.gestisci_numero(stato, n)) == ["giocatori_non_validi"]
        assert stato["fase"] == game.NUM_GIOCATORI


def test_numero_giocatori_non_capito():
    stato = game.nuova_partita()
    assert tipi(game.gestisci_numero(stato, None)) == ["non_capito"]
    assert stato["fase"] == game.NUM_GIOCATORI


def test_imposta_giocatori_e_passa_ai_livelli():
    stato = game.nuova_partita()
    eventi = game.gestisci_numero(stato, 3)
    assert eventi == [{"tipo": "giocatori_impostati", "numero": 3}]
    assert stato["fase"] == game.LIVELLI
    assert len(stato["giocatori"]) == 3
    assert stato["livello_da_chiedere"] == 0


def test_livello_non_valido():
    stato = game.nuova_partita()
    game.gestisci_numero(stato, 2)
    for livello in (0, 11):
        assert tipi(game.gestisci_numero(stato, livello)) == ["livello_non_valido"]
    assert tipi(game.gestisci_numero(stato, None)) == ["non_capito"]
    assert stato["livello_da_chiedere"] == 0


def test_dopo_i_livelli_inizia_la_partita():
    stato, _, eventi = configura([8, 5])
    assert tipi(eventi) == ["inizio"]
    assert [g["livello"] for g in stato["giocatori"]] == [8, 5]
    assert stato["fase"] == game.DOMANDA
    assert stato["turno"] == 0
    assert game.chi_risponde(stato) == 0
    x, y = stato["domanda"]
    assert min(x, y) <= 8
```

- [ ] **Step 2: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_game.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'game'`

- [ ] **Step 3: Implementazione** — `lambda/game.py`

```python
"""Regole di Tabelline Challenge. Nessuna dipendenza da Alexa.

Lo stato è un dizionario serializzabile in JSON. Le funzioni pubbliche lo
modificano sul posto e restituiscono una lista di eventi per speech.py.
"""
import random

from questions import genera_domanda, rientra_nel_livello

NUM_GIOCATORI = "NUM_GIOCATORI"
LIVELLI = "LIVELLI"
DOMANDA = "DOMANDA"
FURTO = "FURTO"
FINE = "FINE"

MAX_GIOCATORI = 4
MAX_LIVELLO = 10
DOMANDE_A_TESTA = 5


def nuova_partita():
    return {
        "fase": NUM_GIOCATORI,
        "giocatori": [],
        "livello_da_chiedere": 0,
        "turno": 0,
        "ladro": None,
        "domanda": None,
        "domande_fatte": 0,
        "non_capito": 0,
        "spareggio": None,
        "pos_spareggio": 0,
    }


def chi_risponde(stato):
    return stato["ladro"] if stato["fase"] == FURTO else stato["turno"]


def gestisci_numero(stato, numero, rng=random):
    """Gestisce un numero detto dall'utente (None = non capito)."""
    eventi = []
    fase = stato["fase"]
    if fase == NUM_GIOCATORI:
        _imposta_giocatori(stato, numero, eventi)
    elif fase == LIVELLI:
        _imposta_livello(stato, numero, eventi, rng)
    return eventi


def _imposta_giocatori(stato, numero, eventi):
    if numero is None:
        eventi.append({"tipo": "non_capito"})
        return
    if not 1 <= numero <= MAX_GIOCATORI:
        eventi.append({"tipo": "giocatori_non_validi"})
        return
    stato["giocatori"] = [
        {"livello": None, "punti": 0, "fatte": []} for _ in range(numero)
    ]
    stato["livello_da_chiedere"] = 0
    stato["fase"] = LIVELLI
    eventi.append({"tipo": "giocatori_impostati", "numero": numero})


def _imposta_livello(stato, numero, eventi, rng):
    if numero is None:
        eventi.append({"tipo": "non_capito"})
        return
    if not 1 <= numero <= MAX_LIVELLO:
        eventi.append({"tipo": "livello_non_valido"})
        return
    i = stato["livello_da_chiedere"]
    stato["giocatori"][i]["livello"] = numero
    stato["livello_da_chiedere"] = i + 1
    if i + 1 == len(stato["giocatori"]):
        stato["turno"] = 0
        eventi.append({"tipo": "inizio"})
        _nuova_domanda(stato, rng)


def _nuova_domanda(stato, rng):
    giocatore = stato["giocatori"][stato["turno"]]
    domanda = genera_domanda(giocatore["livello"], giocatore["fatte"], rng)
    giocatore["fatte"].append(sorted(domanda))
    stato["domanda"] = domanda
    stato["ladro"] = None
    stato["non_capito"] = 0
    stato["fase"] = DOMANDA
```

(`rientra_nel_livello` viene usato nel Task 3.)

- [ ] **Step 4: Verifica che passi**

Run: `.venv/bin/pytest tests/test_game.py -q`
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add lambda/game.py tests/test_game.py
git commit -m "Aggiunge configurazione della partita"
```

---

### Task 3: game.py — risposte, punti, furto, non capito

**Files:**
- Modify: `lambda/game.py` (`gestisci_numero` + nuove funzioni)
- Test: `tests/test_game.py` (aggiunte)

**Interfaces:**
- Consumes: Task 2.
- Produces: nuovi eventi `giusta` (`giocatore`), `sbagliata` (`giocatore`), `soluzione` (`x`, `y`); fase `FURTO` con `stato["ladro"]`. `_avanza(stato, eventi, rng)` in questo task passa solo al turno successivo (fine partita nel Task 4).

- [ ] **Step 1: Test che falliscono** — aggiungere in fondo a `tests/test_game.py`

```python
def risultato(stato):
    x, y = stato["domanda"]
    return x * y


def test_risposta_giusta_un_punto_e_turno_successivo():
    stato, rng, _ = configura([10, 10])
    eventi = game.gestisci_numero(stato, risultato(stato), rng)
    assert eventi == [{"tipo": "giusta", "giocatore": 0}]
    assert stato["giocatori"][0]["punti"] == 1
    assert stato["turno"] == 1
    assert stato["fase"] == game.DOMANDA


def test_risposta_sbagliata_meno_un_punto_e_furto():
    stato, rng, _ = configura([10, 10])
    eventi = game.gestisci_numero(stato, risultato(stato) + 1, rng)
    assert eventi == [{"tipo": "sbagliata", "giocatore": 0}]
    assert stato["giocatori"][0]["punti"] == -1
    assert stato["fase"] == game.FURTO
    assert stato["ladro"] == 1
    assert game.chi_risponde(stato) == 1


def test_furto_riuscito():
    stato, rng, _ = configura([10, 10, 10])
    game.gestisci_numero(stato, risultato(stato) + 1, rng)
    eventi = game.gestisci_numero(stato, risultato(stato), rng)
    assert eventi == [{"tipo": "giusta", "giocatore": 1}]
    assert stato["giocatori"][1]["punti"] == 1
    # il turno passa al giocatore dopo il proprietario della domanda
    assert stato["turno"] == 1
    assert stato["fase"] == game.DOMANDA
    assert stato["domande_fatte"] == 1


def test_furto_fallito_dice_la_soluzione():
    stato, rng, _ = configura([10, 10])
    x, y = stato["domanda"]
    game.gestisci_numero(stato, x * y + 1, rng)
    eventi = game.gestisci_numero(stato, x * y + 1, rng)
    assert eventi[0] == {"tipo": "sbagliata", "giocatore": 1}
    assert eventi[1] == {"tipo": "soluzione", "x": x, "y": y}
    assert stato["giocatori"][1]["punti"] == -1
    assert stato["turno"] == 1


def test_furto_saltato_se_fuori_livello():
    stato, rng, _ = configura([8, 5])
    stato["domanda"] = [9, 8]
    eventi = game.gestisci_numero(stato, 1, rng)
    assert tipi(eventi) == ["sbagliata", "soluzione"]
    assert stato["fase"] == game.DOMANDA
    assert stato["turno"] == 1
    assert stato["giocatori"][1]["punti"] == 0


def test_furto_dall_ultimo_giocatore_va_al_primo():
    stato, rng, _ = configura([10, 10])
    game.gestisci_numero(stato, risultato(stato), rng)  # giocatore 1 giusto
    game.gestisci_numero(stato, risultato(stato) + 1, rng)  # giocatore 2 sbaglia
    assert stato["fase"] == game.FURTO
    assert stato["ladro"] == 0


def test_niente_furto_con_un_giocatore():
    stato, rng, _ = configura([10])
    eventi = game.gestisci_numero(stato, risultato(stato) + 1, rng)
    assert tipi(eventi) == ["sbagliata", "soluzione"]
    assert stato["fase"] == game.DOMANDA


def test_non_capito_prima_volta_senza_penalita():
    stato, rng, _ = configura([10, 10])
    domanda = stato["domanda"]
    assert tipi(game.gestisci_numero(stato, None, rng)) == ["non_capito"]
    assert stato["domanda"] == domanda
    assert stato["giocatori"][0]["punti"] == 0


def test_non_capito_due_volte_conta_sbagliata():
    stato, rng, _ = configura([10, 10])
    game.gestisci_numero(stato, None, rng)
    eventi = game.gestisci_numero(stato, None, rng)
    assert tipi(eventi) == ["sbagliata"]
    assert stato["fase"] == game.FURTO


def test_non_capito_si_azzera_per_il_ladro():
    stato, rng, _ = configura([10, 10])
    game.gestisci_numero(stato, None, rng)
    game.gestisci_numero(stato, None, rng)  # sbagliata, furto
    assert tipi(game.gestisci_numero(stato, None, rng)) == ["non_capito"]
```

- [ ] **Step 2: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_game.py -q`
Expected: FAIL sui nuovi test (es. `assert [] == [{'tipo': 'giusta', ...}]`)

- [ ] **Step 3: Implementazione** — in `lambda/game.py`

Sostituire `gestisci_numero` con:

```python
def gestisci_numero(stato, numero, rng=random):
    """Gestisce un numero detto dall'utente (None = non capito)."""
    eventi = []
    fase = stato["fase"]
    if fase == NUM_GIOCATORI:
        _imposta_giocatori(stato, numero, eventi)
    elif fase == LIVELLI:
        _imposta_livello(stato, numero, eventi, rng)
    elif fase in (DOMANDA, FURTO):
        _rispondi(stato, numero, eventi, rng)
    return eventi
```

Aggiungere in fondo:

```python
def _rispondi(stato, numero, eventi, rng):
    if numero is None and stato["non_capito"] == 0:
        stato["non_capito"] = 1
        eventi.append({"tipo": "non_capito"})
        return
    x, y = stato["domanda"]
    chi = chi_risponde(stato)
    giusta = numero == x * y
    stato["giocatori"][chi]["punti"] += 1 if giusta else -1
    eventi.append({"tipo": "giusta" if giusta else "sbagliata", "giocatore": chi})
    if not giusta and stato["fase"] == DOMANDA:
        ladro = _ladro_possibile(stato)
        if ladro is not None:
            stato["fase"] = FURTO
            stato["ladro"] = ladro
            stato["non_capito"] = 0
            return
    if not giusta:
        eventi.append({"tipo": "soluzione", "x": x, "y": y})
    _avanza(stato, eventi, rng)


def _ladro_possibile(stato):
    n = len(stato["giocatori"])
    if n == 1 or stato["spareggio"] is not None:
        return None
    ladro = (stato["turno"] + 1) % n
    x, y = stato["domanda"]
    if rientra_nel_livello(x, y, stato["giocatori"][ladro]["livello"]):
        return ladro
    return None


def _avanza(stato, eventi, rng):
    n = len(stato["giocatori"])
    stato["domande_fatte"] += 1
    stato["turno"] = (stato["turno"] + 1) % n
    _nuova_domanda(stato, rng)
```

- [ ] **Step 4: Verifica che passi**

Run: `.venv/bin/pytest tests/test_game.py -q`
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add lambda/game.py tests/test_game.py
git commit -m "Aggiunge risposte, punteggio e furto"
```

---

### Task 4: game.py — riepilogo, fine partita, spareggio

**Files:**
- Modify: `lambda/game.py` (`_avanza` + `_fine_turni`)
- Test: `tests/test_game.py` (aggiunte)

**Interfaces:**
- Consumes: Task 3.
- Produces: eventi `riepilogo`, `spareggio` (`giocatori: list[int]`), `fine` (`vincitore: int`); fase `FINE` (con `domanda = None`); `stato["spareggio"]` = lista indici o `None`.

- [ ] **Step 1: Test che falliscono** — aggiungere in fondo a `tests/test_game.py`

```python
def gioca(stato, rng, indovina):
    """Risponde finché la partita non finisce o cambia fase di spareggio.

    indovina(giocatore) -> bool decide se il giocatore risponde giusto.
    Restituisce tutti gli eventi prodotti.
    """
    tutti = []
    for _ in range(500):
        if stato["fase"] == game.FINE:
            break
        chi = game.chi_risponde(stato)
        numero = risultato(stato) if indovina(chi) else risultato(stato) + 1
        tutti += game.gestisci_numero(stato, numero, rng)
    return tutti


def test_riepilogo_a_fine_giro():
    stato, rng, _ = configura([10, 10])
    assert tipi(game.gestisci_numero(stato, risultato(stato), rng)) == ["giusta"]
    eventi = game.gestisci_numero(stato, risultato(stato), rng)
    assert tipi(eventi) == ["giusta", "riepilogo"]


def test_niente_riepilogo_con_un_giocatore():
    stato, rng, _ = configura([10])
    eventi = gioca(stato, rng, lambda chi: True)
    assert "riepilogo" not in tipi(eventi)


def test_partita_da_solo_finisce_dopo_cinque_domande():
    stato, rng, _ = configura([10])
    eventi = gioca(stato, rng, lambda chi: True)
    assert tipi(eventi).count("giusta") == 5
    assert eventi[-1] == {"tipo": "fine", "vincitore": 0}
    assert stato["fase"] == game.FINE
    assert stato["domanda"] is None


def test_vincitore_con_due_giocatori():
    stato, rng, _ = configura([10, 10])
    eventi = gioca(stato, rng, lambda chi: chi == 0)
    assert eventi[-1] == {"tipo": "fine", "vincitore": 0}
    assert stato["domande_fatte"] == 10
    assert "spareggio" not in tipi(eventi)


def test_spareggio_tra_pari_senza_furto():
    stato, rng, _ = configura([10, 10, 10])
    for _ in range(15):
        eventi = game.gestisci_numero(stato, risultato(stato), rng)
    assert eventi[-1] == {"tipo": "spareggio", "giocatori": [0, 1, 2]}
    assert stato["fase"] == game.DOMANDA
    assert stato["turno"] == 0
    # nello spareggio chi sbaglia non subisce furti
    eventi = game.gestisci_numero(stato, risultato(stato) + 1, rng)
    assert tipi(eventi) == ["sbagliata", "soluzione"]
    assert stato["turno"] == 1


def test_spareggio_si_ripete_finche_resta_uno():
    stato, rng, _ = configura([10, 10, 10])
    for _ in range(15):
        game.gestisci_numero(stato, risultato(stato), rng)
    # spareggio 1: giocatori 1 e 2 giusti, giocatore 3 sbaglia
    game.gestisci_numero(stato, risultato(stato), rng)
    game.gestisci_numero(stato, risultato(stato), rng)
    eventi = game.gestisci_numero(stato, risultato(stato) + 1, rng)
    assert eventi[-1] == {"tipo": "spareggio", "giocatori": [0, 1]}
    # spareggio 2: vince il giocatore 2
    game.gestisci_numero(stato, risultato(stato) + 1, rng)
    eventi = game.gestisci_numero(stato, risultato(stato), rng)
    assert eventi[-1] == {"tipo": "fine", "vincitore": 1}
    assert stato["fase"] == game.FINE


def test_fine_ignora_altri_numeri():
    stato, rng, _ = configura([10])
    gioca(stato, rng, lambda chi: True)
    assert game.gestisci_numero(stato, 42, rng) == []
```

- [ ] **Step 2: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_game.py -q`
Expected: FAIL sui nuovi test (manca `riepilogo`/`fine`)

- [ ] **Step 3: Implementazione** — in `lambda/game.py` sostituire `_avanza` con:

```python
def _avanza(stato, eventi, rng):
    n = len(stato["giocatori"])
    if stato["spareggio"] is None:
        stato["domande_fatte"] += 1
        if stato["domande_fatte"] == DOMANDE_A_TESTA * n:
            _fine_turni(stato, eventi, rng)
            return
        if n > 1 and stato["domande_fatte"] % n == 0:
            eventi.append({"tipo": "riepilogo"})
        stato["turno"] = (stato["turno"] + 1) % n
    else:
        stato["pos_spareggio"] += 1
        if stato["pos_spareggio"] == len(stato["spareggio"]):
            _fine_turni(stato, eventi, rng)
            return
        stato["turno"] = stato["spareggio"][stato["pos_spareggio"]]
    _nuova_domanda(stato, rng)


def _fine_turni(stato, eventi, rng):
    """Fine dei turni regolari o di un giro di spareggio."""
    gruppo = stato["spareggio"] or list(range(len(stato["giocatori"])))
    massimo = max(stato["giocatori"][i]["punti"] for i in gruppo)
    primi = [i for i in gruppo if stato["giocatori"][i]["punti"] == massimo]
    if len(primi) == 1:
        stato["fase"] = FINE
        stato["domanda"] = None
        eventi.append({"tipo": "fine", "vincitore": primi[0]})
        return
    stato["spareggio"] = primi
    stato["pos_spareggio"] = 0
    stato["turno"] = primi[0]
    eventi.append({"tipo": "spareggio", "giocatori": primi})
    _nuova_domanda(stato, rng)
```

- [ ] **Step 4: Verifica che passi**

Run: `.venv/bin/pytest -q`
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add lambda/game.py tests/test_game.py
git commit -m "Aggiunge riepilogo, fine partita e spareggio"
```

---

### Task 5: speech.py — testi in italiano

**Files:**
- Create: `lambda/speech.py`
- Test: `tests/test_speech.py`

**Interfaces:**
- Consumes: costanti di fase da `game`; tutti i tipi di evento dei Task 2–4.
- Produces: costanti `BENVENUTO`, `ARRIVEDERCI`, `AIUTO`, `COMPLIMENTI`; `punti_testo(p: int) -> str`; `richiesta(stato) -> str` (`""` in fase FINE); `punteggi(stato) -> str`; `classifica(stato, vincitore: int|None = None) -> str`; `componi(eventi, stato, rng) -> tuple[str, str]` = (testo da dire, reprompt; reprompt `""` se la partita è finita).

- [ ] **Step 1: Test che falliscono** — `tests/test_speech.py`

```python
import random

import game
import speech


def stato_con(livelli, punti=None):
    stato = game.nuova_partita()
    game.gestisci_numero(stato, len(livelli), random.Random(0))
    for livello in livelli:
        game.gestisci_numero(stato, livello, random.Random(0))
    for i, p in enumerate(punti or []):
        stato["giocatori"][i]["punti"] = p
    return stato


def test_punti_testo():
    assert speech.punti_testo(1) == "un punto"
    assert speech.punti_testo(-1) == "meno un punto"
    assert speech.punti_testo(0) == "0 punti"
    assert speech.punti_testo(4) == "4 punti"
    assert speech.punti_testo(-3) == "meno 3 punti"


def test_richiesta_per_fase():
    stato = game.nuova_partita()
    assert speech.richiesta(stato) == "Quanti giocatori siete? Da uno a quattro."
    game.gestisci_numero(stato, 2)
    assert speech.richiesta(stato) == "Giocatore 1, fino a che tabellina conosci?"
    stato = stato_con([10, 10])
    stato["domanda"] = [7, 6]
    assert speech.richiesta(stato) == "Giocatore 1: quanto fa 7 per 6?"
    stato["fase"], stato["ladro"] = game.FURTO, 1
    assert speech.richiesta(stato) == "Giocatore 2, vuoi rubare? Quanto fa 7 per 6?"
    stato["fase"] = game.FINE
    assert speech.richiesta(stato) == ""


def test_richiesta_giocatore_singolo():
    stato = stato_con([10])
    stato["domanda"] = [3, 4]
    assert speech.richiesta(stato) == "Quanto fa 3 per 4?"


def test_punteggi():
    assert speech.punteggi(game.nuova_partita()) == "La partita non è ancora iniziata."
    stato = stato_con([10, 10], punti=[3, -1])
    assert speech.punteggi(stato) == "Punteggi: giocatore 1, 3 punti; giocatore 2, meno un punto."
    assert speech.punteggi(stato_con([10], punti=[2])) == "Hai 2 punti."


def test_classifica_mette_il_vincitore_primo():
    stato = stato_con([10, 10, 10], punti=[2, 4, 4])
    assert speech.classifica(stato, vincitore=2) == (
        "Primo posto: giocatore 3 con 4 punti. "
        "Secondo posto: giocatore 2 con 4 punti. "
        "Terzo posto: giocatore 1 con 2 punti."
    )


def test_componi_risposta_sbagliata_e_furto():
    stato = stato_con([10, 10])
    stato["domanda"] = [7, 6]
    stato["fase"], stato["ladro"] = game.FURTO, 1
    testo, reprompt = speech.componi([{"tipo": "sbagliata", "giocatore": 0}], stato)
    assert testo == "Sbagliato! Il giocatore 1 perde un punto. Giocatore 2, vuoi rubare? Quanto fa 7 per 6?"
    assert reprompt == "Giocatore 2, vuoi rubare? Quanto fa 7 per 6?"


def test_componi_giusta_usa_un_complimento():
    stato = stato_con([10, 10])
    testo, _ = speech.componi([{"tipo": "giusta", "giocatore": 0}], stato, random.Random(0))
    assert any(testo.startswith(c) for c in speech.COMPLIMENTI)
    assert "Un punto al giocatore 1." in testo


def test_componi_fine_senza_reprompt():
    stato = stato_con([10, 10], punti=[5, 3])
    stato["fase"] = game.FINE
    testo, reprompt = speech.componi([{"tipo": "fine", "vincitore": 0}], stato)
    assert testo.startswith("Partita finita! Vince il giocatore 1!")
    assert testo.endswith(speech.ARRIVEDERCI)
    assert reprompt == ""


def test_componi_tutti_gli_eventi_senza_errori():
    stato = stato_con([10, 10, 10])
    eventi = [
        {"tipo": "non_capito"},
        {"tipo": "giocatori_non_validi"},
        {"tipo": "livello_non_valido"},
        {"tipo": "giocatori_impostati", "numero": 1},
        {"tipo": "giocatori_impostati", "numero": 3},
        {"tipo": "inizio"},
        {"tipo": "soluzione", "x": 7, "y": 8},
        {"tipo": "riepilogo"},
        {"tipo": "spareggio", "giocatori": [0, 1, 2]},
    ]
    testo, _ = speech.componi(eventi, stato)
    assert "7 per 8 fa 56." in testo
    assert "Spareggio tra giocatore 1, giocatore 2 e giocatore 3." in testo
```

- [ ] **Step 2: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_speech.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'speech'`

- [ ] **Step 3: Implementazione** — `lambda/speech.py`

```python
"""Testi in italiano: trasforma eventi e stato di gioco in frasi per Alexa."""
import random

import game

BENVENUTO = "Benvenuti a Tabelline Challenge!"
ARRIVEDERCI = "Alla prossima sfida!"
AIUTO = (
    "Tabelline Challenge è una gara sulle tabelline, da uno a quattro giocatori. "
    "A turno rispondete alle moltiplicazioni: risposta giusta un punto, sbagliata meno un punto. "
    "Se sbagli, il giocatore dopo di te può rubare la domanda. "
    "Puoi dire ripeti, punteggio oppure basta."
)
COMPLIMENTI = ["Giusto!", "Esatto!", "Perfetto!", "Ottimo!", "Fantastico!", "Grande!"]
POSIZIONI = ["Primo", "Secondo", "Terzo", "Quarto"]


def punti_testo(p):
    base = "un punto" if abs(p) == 1 else f"{abs(p)} punti"
    return f"meno {base}" if p < 0 else base


def _solo(stato):
    return len(stato["giocatori"]) == 1


def _elenco(parole):
    if len(parole) == 1:
        return parole[0]
    return ", ".join(parole[:-1]) + " e " + parole[-1]


def richiesta(stato):
    """La domanda o richiesta in attesa di risposta ("" a partita finita)."""
    fase = stato["fase"]
    if fase == game.NUM_GIOCATORI:
        return "Quanti giocatori siete? Da uno a quattro."
    if fase == game.LIVELLI:
        if _solo(stato):
            return "Fino a che tabellina conosci?"
        return f"Giocatore {stato['livello_da_chiedere'] + 1}, fino a che tabellina conosci?"
    if fase in (game.DOMANDA, game.FURTO):
        x, y = stato["domanda"]
        domanda = f"quanto fa {x} per {y}?"
        if fase == game.FURTO:
            return f"Giocatore {stato['ladro'] + 1}, vuoi rubare? {domanda.capitalize()}"
        if _solo(stato):
            return domanda.capitalize()
        return f"Giocatore {stato['turno'] + 1}: {domanda}"
    return ""


def punteggi(stato):
    giocatori = stato["giocatori"]
    if not giocatori:
        return "La partita non è ancora iniziata."
    if _solo(stato):
        return f"Hai {punti_testo(giocatori[0]['punti'])}."
    parti = [
        f"giocatore {i + 1}, {punti_testo(g['punti'])}"
        for i, g in enumerate(giocatori)
    ]
    return "Punteggi: " + "; ".join(parti) + "."


def classifica(stato, vincitore=None):
    giocatori = stato["giocatori"]
    if _solo(stato):
        return f"Hai fatto {punti_testo(giocatori[0]['punti'])}."
    ordine = sorted(
        range(len(giocatori)),
        key=lambda i: (i != vincitore, -giocatori[i]["punti"]),
    )
    return " ".join(
        f"{POSIZIONI[pos]} posto: giocatore {i + 1} con {punti_testo(giocatori[i]['punti'])}."
        for pos, i in enumerate(ordine)
    )


def _frase(evento, stato, rng):
    tipo = evento["tipo"]
    solo = _solo(stato)
    if tipo == "non_capito":
        if stato["fase"] in (game.DOMANDA, game.FURTO):
            return "Non ho capito, dimmi solo il numero."
        return "Non ho capito."
    if tipo == "giocatori_non_validi":
        return "Potete essere da uno a quattro giocatori."
    if tipo == "livello_non_valido":
        return "Dimmi un numero da uno a dieci."
    if tipo == "giocatori_impostati":
        if evento["numero"] == 1:
            return "Perfetto, giochi da solo!"
        return f"Perfetto, siete {evento['numero']} giocatori!"
    if tipo == "inizio":
        if solo:
            return f"Si comincia! {game.DOMANDE_A_TESTA} domande per te."
        return f"Si comincia! {game.DOMANDE_A_TESTA} domande a testa."
    if tipo == "giusta":
        complimento = rng.choice(COMPLIMENTI)
        if solo:
            return f"{complimento} Un punto in più."
        return f"{complimento} Un punto al giocatore {evento['giocatore'] + 1}."
    if tipo == "sbagliata":
        if solo:
            return "Sbagliato, perdi un punto."
        return f"Sbagliato! Il giocatore {evento['giocatore'] + 1} perde un punto."
    if tipo == "soluzione":
        x, y = evento["x"], evento["y"]
        return f"{x} per {y} fa {x * y}."
    if tipo == "riepilogo":
        return punteggi(stato)
    if tipo == "spareggio":
        nomi = _elenco([f"giocatore {i + 1}" for i in evento["giocatori"]])
        return f"Parità! Spareggio tra {nomi}."
    if tipo == "fine":
        vincitore = evento["vincitore"]
        annuncio = "Partita finita!"
        if not solo:
            annuncio += f" Vince il giocatore {vincitore + 1}!"
        return f"{annuncio} {classifica(stato, vincitore)} {ARRIVEDERCI}"
    raise ValueError(f"Evento sconosciuto: {tipo}")


def componi(eventi, stato, rng=random):
    """Restituisce (testo da dire, reprompt)."""
    frasi = [_frase(e, stato, rng) for e in eventi]
    domanda = richiesta(stato)
    if domanda:
        frasi.append(domanda)
    return " ".join(frasi), domanda
```

- [ ] **Step 4: Verifica che passi**

Run: `.venv/bin/pytest -q`
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add lambda/speech.py tests/test_speech.py
git commit -m "Aggiunge i testi in italiano"
```

---

### Task 6: Handler Alexa e interaction model

**Files:**
- Create: `lambda/lambda_function.py`, `lambda/requirements.txt`, `skill-package/interactionModels/custom/it-IT.json`
- Test: `tests/test_lambda_function.py`

**Interfaces:**
- Consumes: `game.nuova_partita`, `game.gestisci_numero`, `game.DOMANDA`, `game.FURTO`; `speech.richiesta/componi/punteggi/classifica/BENVENUTO/AIUTO/ARRIVEDERCI`.
- Produces: `lambda_handler(event, context)` (entry point Alexa-hosted). Intent: `NumeroIntent` (slot `numero`), `RipetiIntent`, `PunteggioIntent`, built-in Help/Stop/Cancel/Fallback/NavigateHome.

- [ ] **Step 1: Test che falliscono** — `tests/test_lambda_function.py`

```python
import json
import pathlib
import re

import lambda_function

MODELLO = pathlib.Path(__file__).parent.parent / "skill-package/interactionModels/custom/it-IT.json"


def evento(tipo, intent=None, numero=None, attributi=None):
    richiesta = {
        "type": tipo,
        "requestId": "req",
        "locale": "it-IT",
        "timestamp": "2026-10-07T10:00:00Z",
    }
    if intent:
        slots = {}
        if numero is not None:
            slots["numero"] = {"name": "numero", "value": str(numero), "confirmationStatus": "NONE"}
        richiesta["intent"] = {"name": intent, "confirmationStatus": "NONE", "slots": slots}
    return {
        "version": "1.0",
        "session": {
            "new": attributi is None,
            "sessionId": "sess",
            "application": {"applicationId": "app"},
            "user": {"userId": "user"},
            "attributes": attributi or {},
        },
        "context": {
            "System": {
                "application": {"applicationId": "app"},
                "user": {"userId": "user"},
                "device": {"deviceId": "dev", "supportedInterfaces": {}},
                "apiEndpoint": "https://api.eu.amazonalexa.com",
            }
        },
        "request": richiesta,
    }


class Sessione:
    def __init__(self):
        self.attributi = None

    def invia(self, tipo, intent=None, numero=None):
        risposta = lambda_function.lambda_handler(evento(tipo, intent, numero, self.attributi), None)
        self.attributi = risposta.get("sessionAttributes") or {}
        r = risposta["response"]
        testo = re.sub(r"</?speak>", "", r["outputSpeech"]["ssml"])
        return testo, r.get("shouldEndSession")

    def intent(self, nome, numero=None):
        return self.invia("IntentRequest", nome, numero)

    def stato(self):
        return self.attributi["stato"]


def test_partita_completa_da_solo():
    s = Sessione()
    testo, fine = s.invia("LaunchRequest")
    assert testo.startswith("Benvenuti a Tabelline Challenge!")
    assert fine is False
    s.intent("NumeroIntent", 1)
    testo, _ = s.intent("NumeroIntent", 10)
    assert "Si comincia!" in testo
    for _ in range(5):
        x, y = s.stato()["domanda"]
        testo, fine = s.intent("NumeroIntent", x * y)
    assert "Partita finita!" in testo
    assert "Hai fatto 5 punti." in testo
    assert fine is True


def test_numero_non_capito_e_fallback():
    s = Sessione()
    s.invia("LaunchRequest")
    testo, fine = s.intent("NumeroIntent", "?")
    assert testo.startswith("Non ho capito.")
    assert fine is False
    testo, _ = s.intent("AMAZON.FallbackIntent")
    assert testo.startswith("Non ho capito.")


def test_ripeti_punteggio_aiuto():
    s = Sessione()
    s.invia("LaunchRequest")
    s.intent("NumeroIntent", 2)
    s.intent("NumeroIntent", 5)
    s.intent("NumeroIntent", 5)
    x, y = s.stato()["domanda"]
    domanda = f"Giocatore 1: quanto fa {x} per {y}?"
    assert s.intent("RipetiIntent")[0] == domanda
    assert s.intent("PunteggioIntent")[0] == (
        f"Punteggi: giocatore 1, 0 punti; giocatore 2, 0 punti. {domanda}"
    )
    testo, fine = s.intent("AMAZON.HelpIntent")
    assert testo.endswith(domanda)
    assert fine is False


def test_stop_legge_la_classifica():
    s = Sessione()
    s.invia("LaunchRequest")
    s.intent("NumeroIntent", 2)
    s.intent("NumeroIntent", 5)
    s.intent("NumeroIntent", 5)
    testo, fine = s.intent("AMAZON.StopIntent")
    assert testo.startswith("Primo posto:")
    assert testo.endswith("Alla prossima sfida!")
    assert fine is True


def test_stop_prima_di_iniziare():
    s = Sessione()
    s.invia("LaunchRequest")
    testo, fine = s.intent("AMAZON.CancelIntent")
    assert testo == "Alla prossima sfida!"
    assert fine is True


def test_interaction_model():
    modello = json.loads(MODELLO.read_text(encoding="utf-8"))["interactionModel"]["languageModel"]
    assert modello["invocationName"] == "tabelline challenge"
    nomi = {i["name"] for i in modello["intents"]}
    assert {
        "NumeroIntent", "RipetiIntent", "PunteggioIntent",
        "AMAZON.HelpIntent", "AMAZON.StopIntent", "AMAZON.CancelIntent",
        "AMAZON.FallbackIntent", "AMAZON.NavigateHomeIntent",
    } <= nomi
    esempi = [s.lower() for i in modello["intents"] for s in i["samples"]]
    assert len(esempi) == len(set(esempi)), "esempi duplicati tra intent"
```

- [ ] **Step 2: Verifica che fallisca**

Run: `.venv/bin/pytest tests/test_lambda_function.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'lambda_function'`

- [ ] **Step 3: Implementazione**

`lambda/requirements.txt`:
```
ask-sdk-core>=1.19.0
```

`lambda/lambda_function.py`:
```python
"""Handler Alexa di Tabelline Challenge.

Lo stato della partita vive nei session attributes sotto la chiave "stato".
"""
import logging

from ask_sdk_core.dispatch_components import AbstractExceptionHandler, AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import get_slot_value, is_intent_name, is_request_type

import game
import speech

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _carica(handler_input):
    attributi = handler_input.attributes_manager.session_attributes
    return attributi.get("stato") or game.nuova_partita()


def _rispondi(handler_input, stato, testo, reprompt):
    handler_input.attributes_manager.session_attributes["stato"] = stato
    builder = handler_input.response_builder.speak(testo)
    if reprompt:
        builder.ask(reprompt)
    else:
        builder.set_should_end_session(True)
    return builder.response


def _numero(handler_input):
    try:
        return int(get_slot_value(handler_input, "numero"))
    except (TypeError, ValueError):
        return None


class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        stato = game.nuova_partita()
        domanda = speech.richiesta(stato)
        return _rispondi(handler_input, stato, f"{speech.BENVENUTO} {domanda}", domanda)


class NumeroHandler(AbstractRequestHandler):
    """Risposte numeriche; il Fallback conta come numero non capito."""

    def can_handle(self, handler_input):
        return (is_intent_name("NumeroIntent")(handler_input)
                or is_intent_name("AMAZON.FallbackIntent")(handler_input))

    def handle(self, handler_input):
        stato = _carica(handler_input)
        numero = _numero(handler_input) if is_intent_name("NumeroIntent")(handler_input) else None
        eventi = game.gestisci_numero(stato, numero)
        testo, reprompt = speech.componi(eventi, stato)
        return _rispondi(handler_input, stato, testo, reprompt)


class RipetiHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("RipetiIntent")(handler_input)

    def handle(self, handler_input):
        stato = _carica(handler_input)
        domanda = speech.richiesta(stato)
        return _rispondi(handler_input, stato, domanda, domanda)


class PunteggioHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("PunteggioIntent")(handler_input)

    def handle(self, handler_input):
        stato = _carica(handler_input)
        domanda = speech.richiesta(stato)
        return _rispondi(handler_input, stato, f"{speech.punteggi(stato)} {domanda}", domanda)


class AiutoHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        stato = _carica(handler_input)
        domanda = speech.richiesta(stato)
        return _rispondi(handler_input, stato, f"{speech.AIUTO} {domanda}", domanda)


class StopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return any(
            is_intent_name(nome)(handler_input)
            for nome in ("AMAZON.StopIntent", "AMAZON.CancelIntent", "AMAZON.NavigateHomeIntent")
        )

    def handle(self, handler_input):
        stato = _carica(handler_input)
        testo = speech.ARRIVEDERCI
        if stato["fase"] in (game.DOMANDA, game.FURTO):
            testo = f"{speech.classifica(stato)} {testo}"
        return _rispondi(handler_input, stato, testo, "")


class SessionEndedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class ErroreHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        testo = "Scusa, qualcosa è andato storto. Riprova."
        return handler_input.response_builder.speak(testo).ask(testo).response


sb = SkillBuilder()
sb.add_request_handler(LaunchHandler())
sb.add_request_handler(NumeroHandler())
sb.add_request_handler(RipetiHandler())
sb.add_request_handler(PunteggioHandler())
sb.add_request_handler(AiutoHandler())
sb.add_request_handler(StopHandler())
sb.add_request_handler(SessionEndedHandler())
sb.add_exception_handler(ErroreHandler())

lambda_handler = sb.lambda_handler()
```

`skill-package/interactionModels/custom/it-IT.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "tabelline challenge",
      "intents": [
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.HelpIntent", "samples": ["aiuto", "come si gioca", "quali sono le regole"] },
        { "name": "AMAZON.StopIntent", "samples": ["basta", "smettiamo", "fine partita"] },
        { "name": "AMAZON.NavigateHomeIntent", "samples": [] },
        { "name": "AMAZON.FallbackIntent", "samples": [] },
        {
          "name": "NumeroIntent",
          "slots": [{ "name": "numero", "type": "AMAZON.NUMBER" }],
          "samples": [
            "{numero}",
            "fa {numero}",
            "è {numero}",
            "il risultato è {numero}",
            "siamo {numero}",
            "siamo in {numero}",
            "giochiamo in {numero}",
            "fino al {numero}",
            "fino alla {numero}",
            "fino alla tabellina del {numero}",
            "la tabellina del {numero}",
            "conosco fino al {numero}",
            "conosco fino alla tabellina del {numero}"
          ]
        },
        {
          "name": "RipetiIntent",
          "slots": [],
          "samples": ["ripeti", "puoi ripetere", "ripeti la domanda", "non ho sentito"]
        },
        {
          "name": "PunteggioIntent",
          "slots": [],
          "samples": ["punteggio", "punteggi", "classifica", "quanti punti abbiamo", "quanti punti ho"]
        }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 4: Verifica che passi**

Run: `.venv/bin/pytest -q`
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add lambda/lambda_function.py lambda/requirements.txt skill-package tests/test_lambda_function.py
git commit -m "Aggiunge handler Alexa e interaction model it-IT"
```

---

### Task 7: README e allineamento spec

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-10-07-tabelline-challenge-design.md` (regola del silenzio)

- [ ] **Step 1: Correggere la spec.** La piattaforma Alexa chiude la sessione se dopo il reprompt c'è ancora silenzio, quindi "secondo silenzio = sbagliata" non è realizzabile. In "Punteggio" sostituire la riga "Nessuna risposta: …" con:

```markdown
- Nessuna risposta: Alexa ripete la domanda una volta (reprompt). Se il silenzio continua, Alexa chiude la sessione (limite della piattaforma) e la partita è persa.
- Risposta non capita: vedi "Gestione errori".
```

- [ ] **Step 2: Scrivere `README.md`**

```markdown
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
```

- [ ] **Step 3: Verifica finale**

Run: `.venv/bin/pytest -q`
Expected: tutti PASS

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/specs/2026-10-07-tabelline-challenge-design.md
git commit -m "Aggiunge README e allinea la spec sul silenzio"
```
