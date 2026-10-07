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
