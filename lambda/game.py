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
