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
