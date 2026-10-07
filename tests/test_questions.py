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
