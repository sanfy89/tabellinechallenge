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
    elif fase in (DOMANDA, FURTO):
        _rispondi(stato, numero, eventi, rng)
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
