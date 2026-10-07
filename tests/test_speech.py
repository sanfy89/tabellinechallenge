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
