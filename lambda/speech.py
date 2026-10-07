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
