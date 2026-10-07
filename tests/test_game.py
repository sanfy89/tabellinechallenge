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
