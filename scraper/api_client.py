"""
Client API-Football (api-sports.io) — collecte fixtures + statistiques de match.

Version 2 : interroge maintenant PostgreSQL AVANT de demander des stats,
pour ne jamais re-consommer de quota sur un match déjà en base.

Plan gratuit : 100 requêtes/jour, toutes les endpoints inclus.
"""

from __future__ import annotations

import os
import json
import time
import logging
from dataclasses import dataclass

import requests
import psycopg   # psycopg v3 (installé via `pip install psycopg[binary]`)

from parsers import parser_liste_fixtures, parser_statistiques_match

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = os.environ.get("API_FOOTBALL_KEY")

DELAI_ENTRE_REQUETES = 1.0
MAX_TENTATIVES = 3

# Connexion à la même base que charger_json_vers_db.py
#
# DB_HOST est configurable via variable d'environnement :
#   - en local (hors Docker) : "localhost" (valeur par défaut)
#   - dans docker-compose : "postgres" (le nom du service, résolu
#     automatiquement par le réseau Docker interne)
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": 5432,
    "dbname": "football_db",
    "user": "football",
    "password": "football_pwd",
}


@dataclass
class ResultatAppel:
    succes: bool
    donnees: dict | None
    code_erreur: str | None = None


def _headers() -> dict:
    if not API_KEY:
        raise RuntimeError(
            "Variable d'environnement API_FOOTBALL_KEY manquante. "
            "Définis-la avant de lancer le client : $env:API_FOOTBALL_KEY='ta_cle'"
        )
    return {"x-apisports-key": API_KEY}


def _appel_api(endpoint: str, params: dict) -> ResultatAppel:
    url = f"{BASE_URL}/{endpoint}"

    for tentative in range(1, MAX_TENTATIVES + 1):
        try:
            reponse = requests.get(url, headers=_headers(), params=params, timeout=15)

            if reponse.status_code == 200:
                donnees = reponse.json()
                restant = reponse.headers.get("x-ratelimit-requests-remaining")
                if restant is not None:
                    logger.info("Quota restant aujourd'hui : %s requêtes", restant)
                return ResultatAppel(succes=True, donnees=donnees)

            if reponse.status_code == 429:
                logger.error("Quota journalier API-Football dépassé (429). Arrêt pour aujourd'hui.")
                return ResultatAppel(succes=False, donnees=None, code_erreur="quota_depasse")

            logger.error("Échec HTTP %s pour %s", reponse.status_code, endpoint)
            return ResultatAppel(succes=False, donnees=None, code_erreur=str(reponse.status_code))

        except requests.RequestException as exc:
            logger.warning("Tentative %s/%s échouée : %s", tentative, MAX_TENTATIVES, exc)
            time.sleep(DELAI_ENTRE_REQUETES * 2)

    return ResultatAppel(succes=False, donnees=None, code_erreur="max_tentatives_atteint")


def recuperer_fixtures(league_id: int, saison: int, journee: str | None = None) -> list[dict]:
    params = {"league": league_id, "season": saison}
    if journee:
        params["round"] = journee

    resultat = _appel_api("fixtures", params)
    if not resultat.succes:
        logger.error("Impossible de récupérer les fixtures (%s)", resultat.code_erreur)
        return []

    fixtures = parser_liste_fixtures(resultat.donnees)
    logger.info("%s match(s) récupéré(s)", len(fixtures))
    return fixtures


def recuperer_statistiques_match(fixture_id: int) -> list[dict]:
    resultat = _appel_api("fixtures/statistics", {"fixture": fixture_id})
    if not resultat.succes:
        logger.error("Stats indisponibles pour le match %s (%s)", fixture_id, resultat.code_erreur)
        return []

    return parser_statistiques_match(resultat.donnees)


# ============================================================
# NOUVEAU : consulte la base pour savoir quels matchs ont déjà
# leurs stats, au lieu de repartir d'un set() vide à chaque fois.
# ============================================================
def recuperer_fixture_ids_avec_stats_en_base() -> set[int]:
    """
    Retourne l'ensemble des fixture_id déjà marqués stats_recuperees = TRUE
    en base. Si la connexion échoue (base pas démarrée, etc.), on log
    une erreur claire et on retourne un set vide plutôt que de planter --
    dans ce cas le script se comporte comme avant (sans mémoire).
    """
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT fixture_id FROM matchs WHERE stats_recuperees = TRUE;")
                ids = {ligne[0] for ligne in cur.fetchall()}
        logger.info("%s match(s) déjà en base avec leurs stats — ils seront ignorés", len(ids))
        return ids
    except Exception as exc:
        logger.error(
            "Impossible de consulter la base (%s) -- vérifie que 'docker compose up -d' "
            "a bien été lancé dans le dossier db/. Le script continue SANS mémoire pour cette fois.",
            exc,
        )
        return set()


def requete_economique_statistiques(fixtures: list[dict], fixture_ids_deja_en_base: set[int]) -> dict[int, list[dict]]:
    stats_par_match = {}

    matchs_a_traiter = [
        f for f in fixtures
        if f["statut"] == "FT" and f["fixture_id"] not in fixture_ids_deja_en_base
    ]
    logger.info("%s match(s) à traiter sur %s au total (déjà en base : %s)",
                len(matchs_a_traiter), len(fixtures), len(fixture_ids_deja_en_base))

    for fixture in matchs_a_traiter:
        stats = recuperer_statistiques_match(fixture["fixture_id"])
        if stats:
            stats_par_match[fixture["fixture_id"]] = stats
        time.sleep(DELAI_ENTRE_REQUETES)

    return stats_par_match


if __name__ == "__main__":
    PREMIER_LEAGUE_ID = 39
    SAISON = 2024

    fixtures = recuperer_fixtures(PREMIER_LEAGUE_ID, SAISON)

    # AVANT : fixture_ids_deja_en_base = set()  (toujours vide -> re-scrapait tout)
    # MAINTENANT : vraie requête SQL sur la base
    fixture_ids_deja_en_base = recuperer_fixture_ids_avec_stats_en_base()

    stats = requete_economique_statistiques(fixtures, fixture_ids_deja_en_base)
    logger.info("Statistiques récupérées pour %s nouveau(x) match(s)", len(stats))

    with open("stats_recuperees.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in stats.items()}, f, ensure_ascii=False, indent=2)

    with open("fixtures_recuperes.json", "w", encoding="utf-8") as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=2)

    print(f"Sauvegardé : {len(stats)} NOUVEAUX matchs avec stats, {len(fixtures)} fixtures au total")
    print("Prochaine étape : lance charger_json_vers_db.py (depuis le dossier db/) pour les insérer.")