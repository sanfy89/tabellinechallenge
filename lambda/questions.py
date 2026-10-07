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
