import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parsers import (
    parser_fixture,
    parser_liste_fixtures,
    parser_statistiques_match,
    _nettoyer_valeur_stat,
)


def test_parser_fixture():
    fixture = {
        "fixture": {
            "id": 12345,
            "date": "2024-09-15T15:00:00+00:00",
            "status": {"short": "FT"},
        },
        "league": {
            "round": "Regular Season - 5",
            "season": 2024,
        },
        "teams": {
            "home": {"id": 1, "name": "Arsenal"},
            "away": {"id": 2, "name": "Chelsea"},
        },
        "goals": {
            "home": 3,
            "away": 1,
        },
    }

    resultat = parser_fixture(fixture)

    assert resultat["fixture_id"] == 12345
    assert resultat["statut"] == "FT"
    assert resultat["journee"] == "Regular Season - 5"
    assert resultat["saison"] == 2024
    assert resultat["equipe_domicile"] == "Arsenal"
    assert resultat["equipe_exterieur"] == "Chelsea"
    assert resultat["buts_domicile"] == 3
    assert resultat["buts_exterieur"] == 1


def test_parser_fixture_donnees_manquantes():
    resultat = parser_fixture({})

    assert resultat["fixture_id"] is None
    assert resultat["date"] is None
    assert resultat["statut"] is None
    assert resultat["equipe_domicile"] is None
    assert resultat["equipe_exterieur"] is None


def test_parser_liste_fixtures():
    reponse = {
        "response": [
            {
                "fixture": {
                    "id": 1,
                    "date": "2024-08-01T15:00:00+00:00",
                    "status": {"short": "FT"},
                },
                "league": {
                    "round": "Regular Season - 1",
                    "season": 2024,
                },
                "teams": {
                    "home": {"id": 10, "name": "Arsenal"},
                    "away": {"id": 20, "name": "Liverpool"},
                },
                "goals": {
                    "home": 2,
                    "away": 2,
                },
            },
            {
                "fixture": {
                    "id": 2,
                    "date": "2024-08-02T15:00:00+00:00",
                    "status": {"short": "FT"},
                },
                "league": {
                    "round": "Regular Season - 1",
                    "season": 2024,
                },
                "teams": {
                    "home": {"id": 30, "name": "Chelsea"},
                    "away": {"id": 40, "name": "Tottenham"},
                },
                "goals": {
                    "home": 1,
                    "away": 0,
                },
            },
        ]
    }

    resultat = parser_liste_fixtures(reponse)

    assert len(resultat) == 2
    assert resultat[0]["fixture_id"] == 1
    assert resultat[1]["fixture_id"] == 2


def test_parser_liste_fixtures_reponse_vide():
    assert parser_liste_fixtures({"response": []}) == []


def test_nettoyer_valeur_stat_pourcentage():
    assert _nettoyer_valeur_stat("58%") == 58.0


def test_nettoyer_valeur_stat_nombre():
    assert _nettoyer_valeur_stat(25) == 25


def test_nettoyer_valeur_stat_none():
    assert _nettoyer_valeur_stat(None) is None


def test_nettoyer_valeur_stat_pourcentage_invalide():
    assert _nettoyer_valeur_stat("abc%") is None


def test_parser_statistiques_match():
    reponse = {
        "response": [
            {
                "team": {
                    "id": 1,
                    "name": "Arsenal",
                },
                "statistics": [
                    {"type": "Ball Possession", "value": "62%"},
                    {"type": "Total Shots", "value": 15},
                    {"type": "Shots on Goal", "value": 7},
                    {"type": "Corner Kicks", "value": 6},
                    {"type": "Total passes", "value": 500},
                    {"type": "Passes accurate", "value": 430},
                    {"type": "Passes %", "value": "86%"},
                ],
            },
            {
                "team": {
                    "id": 2,
                    "name": "Chelsea",
                },
                "statistics": [
                    {"type": "Ball Possession", "value": "38%"},
                    {"type": "Total Shots", "value": 8},
                    {"type": "Corner Kicks", "value": 3},
                ],
            },
        ]
    }

    resultat = parser_statistiques_match(reponse)

    assert len(resultat) == 2

    arsenal = resultat[0]

    assert arsenal["equipe_id"] == 1
    assert arsenal["equipe_nom"] == "Arsenal"
    assert arsenal["possession"] == 62.0
    assert arsenal["tirs_total"] == 15
    assert arsenal["tirs_cadres"] == 7
    assert arsenal["corners"] == 6
    assert arsenal["passes_total"] == 500
    assert arsenal["passes_reussies"] == 430
    assert arsenal["precision_passes"] == 86.0


def test_parser_statistiques_match_reponse_vide():
    assert parser_statistiques_match({"response": []}) == []


def test_parser_statistiques_ignore_statistique_inconnue():
    reponse = {
        "response": [
            {
                "team": {
                    "id": 1,
                    "name": "Arsenal",
                },
                "statistics": [
                    {"type": "Statistique inconnue", "value": 999},
                    {"type": "Ball Possession", "value": "60%"},
                ],
            }
        ]
    }

    resultat = parser_statistiques_match(reponse)

    assert len(resultat) == 1
    assert resultat[0]["possession"] == 60.0
    assert "Statistique inconnue" not in resultat[0]