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


def gioca(stato, rng, indovina):
    """Risponde finché la partita non finisce.

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
