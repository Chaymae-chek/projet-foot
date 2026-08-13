import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests

from api_client import (
    ResultatAppel,
    _appel_api,
    recuperer_fixtures,
    recuperer_statistiques_match,
    requete_economique_statistiques,
)


def test_resultat_appel_succes():
    resultat = ResultatAppel(
        succes=True,
        donnees={"response": []},
    )

    assert resultat.succes is True
    assert resultat.donnees == {"response": []}
    assert resultat.code_erreur is None


def test_resultat_appel_echec():
    resultat = ResultatAppel(
        succes=False,
        donnees=None,
        code_erreur="404",
    )

    assert resultat.succes is False
    assert resultat.donnees is None
    assert resultat.code_erreur == "404"


def test_appel_api_succes(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {
            "x-ratelimit-requests-remaining": "95"
        }

        def json(self):
            return {
                "response": [
                    {"id": 123}
                ]
            }

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("api_client.requests.get", fake_get)
    monkeypatch.setattr(
        "api_client.API_KEY",
        "fake-api-key"
    )

    resultat = _appel_api(
        "fixtures",
        {"league": 39, "season": 2024}
    )

    assert resultat.succes is True
    assert resultat.donnees == {
        "response": [{"id": 123}]
    }
    assert resultat.code_erreur is None


def test_appel_api_erreur_404(monkeypatch):
    class FakeResponse:
        status_code = 404
        headers = {}

        def json(self):
            return {}

    monkeypatch.setattr(
        "api_client.requests.get",
        lambda *args, **kwargs: FakeResponse()
    )

    monkeypatch.setattr(
        "api_client.API_KEY",
        "fake-api-key"
    )

    resultat = _appel_api(
        "fixtures",
        {"league": 39, "season": 2024}
    )

    assert resultat.succes is False
    assert resultat.donnees is None
    assert resultat.code_erreur == "404"


def test_appel_api_quota_depasse(monkeypatch):
    class FakeResponse:
        status_code = 429
        headers = {}

    monkeypatch.setattr(
        "api_client.requests.get",
        lambda *args, **kwargs: FakeResponse()
    )

    monkeypatch.setattr(
        "api_client.API_KEY",
        "fake-api-key"
    )

    resultat = _appel_api(
        "fixtures",
        {"league": 39, "season": 2024}
    )

    assert resultat.succes is False
    assert resultat.donnees is None
    assert resultat.code_erreur == "quota_depasse"


def test_appel_api_erreur_reseau(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException("Erreur réseau")

    monkeypatch.setattr(
        "api_client.requests.get",
        fake_get
    )

    monkeypatch.setattr(
        "api_client.API_KEY",
        "fake-api-key"
    )

    monkeypatch.setattr(
        "api_client.time.sleep",
        lambda *args: None
    )

    resultat = _appel_api(
        "fixtures",
        {"league": 39, "season": 2024}
    )

    assert resultat.succes is False
    assert resultat.donnees is None
    assert resultat.code_erreur == "max_tentatives_atteint"


def test_recuperer_fixtures(monkeypatch):
    donnees = {
        "response": [
            {
                "fixture": {
                    "id": 123,
                    "date": "2024-08-01T15:00:00+00:00",
                    "status": {"short": "FT"},
                },
                "league": {
                    "round": "Regular Season - 1",
                    "season": 2024,
                },
                "teams": {
                    "home": {"id": 1, "name": "Arsenal"},
                    "away": {"id": 2, "name": "Chelsea"},
                },
                "goals": {
                    "home": 2,
                    "away": 1,
                },
            }
        ]
    }

    monkeypatch.setattr(
        "api_client._appel_api",
        lambda endpoint, params: ResultatAppel(
            succes=True,
            donnees=donnees,
        )
    )

    resultat = recuperer_fixtures(
        league_id=39,
        saison=2024,
    )

    assert len(resultat) == 1
    assert resultat[0]["fixture_id"] == 123
    assert resultat[0]["equipe_domicile"] == "Arsenal"


def test_recuperer_fixtures_echec(monkeypatch):
    monkeypatch.setattr(
        "api_client._appel_api",
        lambda endpoint, params: ResultatAppel(
            succes=False,
            donnees=None,
            code_erreur="quota_depasse",
        )
    )

    resultat = recuperer_fixtures(
        league_id=39,
        saison=2024,
    )

    assert resultat == []


def test_recuperer_statistiques_match(monkeypatch):
    donnees = {
        "response": [
            {
                "team": {
                    "id": 1,
                    "name": "Arsenal",
                },
                "statistics": [
                    {
                        "type": "Ball Possession",
                        "value": "60%",
                    }
                ],
            }
        ]
    }

    monkeypatch.setattr(
        "api_client._appel_api",
        lambda endpoint, params: ResultatAppel(
            succes=True,
            donnees=donnees,
        )
    )

    resultat = recuperer_statistiques_match(123)

    assert len(resultat) == 1
    assert resultat[0]["equipe_id"] == 1
    assert resultat[0]["possession"] == 60.0


def test_recuperer_statistiques_match_echec(monkeypatch):
    monkeypatch.setattr(
        "api_client._appel_api",
        lambda endpoint, params: ResultatAppel(
            succes=False,
            donnees=None,
            code_erreur="404",
        )
    )

    resultat = recuperer_statistiques_match(123)

    assert resultat == []


def test_requete_economique_ignore_match_deja_en_base(monkeypatch):
    fixtures = [
        {
            "fixture_id": 1,
            "statut": "FT",
        },
        {
            "fixture_id": 2,
            "statut": "FT",
        },
        {
            "fixture_id": 3,
            "statut": "NS",
        },
    ]

    appels = []

    def fake_recuperer_stats(fixture_id):
        appels.append(fixture_id)
        return [
            {
                "equipe_id": 10,
                "equipe_nom": "Arsenal",
            }
        ]

    monkeypatch.setattr(
        "api_client.recuperer_statistiques_match",
        fake_recuperer_stats
    )

    monkeypatch.setattr(
        "api_client.time.sleep",
        lambda *args: None
    )

    resultat = requete_economique_statistiques(
        fixtures,
        fixture_ids_deja_en_base={1},
    )

    assert appels == [2]
    assert 1 not in resultat
    assert 2 in resultat
    assert 3 not in resultat


def test_requete_economique_avec_stats_vides(monkeypatch):
    fixtures = [
        {
            "fixture_id": 1,
            "statut": "FT",
        }
    ]

    monkeypatch.setattr(
        "api_client.recuperer_statistiques_match",
        lambda fixture_id: []
    )

    monkeypatch.setattr(
        "api_client.time.sleep",
        lambda *args: None
    )

    resultat = requete_economique_statistiques(
        fixtures,
        fixture_ids_deja_en_base=set(),
    )

    assert resultat == {}