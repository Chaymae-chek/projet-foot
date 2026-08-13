"""
Charge les fichiers JSON déjà récupérés (fixtures_recuperes.json,
stats_recuperees.json) dans la base PostgreSQL.

Ce script NE FAIT AUCUN appel à l'API — il travaille uniquement sur
les fichiers déjà sur ton disque, donc tu peux le relancer autant de
fois que tu veux sans consommer de quota.

Prérequis : PostgreSQL doit tourner (voir db/docker-compose.yml)
et psycopg2 doit être installé : pip install psycopg2-binary
"""

from __future__ import annotations

import json
import logging

import psycopg as psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

CONNEXION_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "football_db",
    "user": "football",
    "password": "football_pwd",
}


def charger_fixtures(chemin_fichier: str) -> list[dict]:
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        return json.load(f)


def charger_stats(chemin_fichier: str) -> dict[str, list[dict]]:
    """
    stats_recuperees.json est structuré comme {fixture_id: [stats_equipe1, stats_equipe2]}
    si tu as sauvegardé le dict retourné par requete_economique_statistiques.
    """
    with open(chemin_fichier, "r", encoding="utf-8") as f:
        return json.load(f)


def inserer_equipe(cur, equipe_id: int, nom: str) -> None:
    if equipe_id is None or nom is None:
        return
    cur.execute(
        """
        INSERT INTO equipes (id, nom)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING;
        """,
        (equipe_id, nom),
    )


def inserer_match(cur, fixture: dict) -> None:
    cur.execute(
        """
        INSERT INTO matchs (
            fixture_id, date_match, statut, journee, saison,
            equipe_domicile_id, equipe_exterieur_id, buts_domicile, buts_exterieur
        )
        VALUES (%(fixture_id)s, %(date)s, %(statut)s, %(journee)s, %(saison)s,
                %(equipe_domicile_id)s, %(equipe_exterieur_id)s, %(buts_domicile)s, %(buts_exterieur)s)
        ON CONFLICT (fixture_id) DO NOTHING;
        """,
        fixture,
    )


def inserer_stats(cur, fixture_id: int, stats_equipe: dict) -> None:
    cur.execute(
        """
        INSERT INTO stats_match (
            fixture_id, equipe_id, possession, tirs_total, tirs_cadres,
            tirs_non_cadres, tirs_bloques, corners, fautes,
            cartons_jaunes, cartons_rouges, passes_total, passes_reussies, precision_passes
        )
        VALUES (%(fixture_id)s, %(equipe_id)s, %(possession)s, %(tirs_total)s, %(tirs_cadres)s,
                %(tirs_non_cadres)s, %(tirs_bloques)s, %(corners)s, %(fautes)s,
                %(cartons_jaunes)s, %(cartons_rouges)s, %(passes_total)s, %(passes_reussies)s, %(precision_passes)s)
        ON CONFLICT (fixture_id, equipe_id) DO NOTHING;
        """,
        {**stats_equipe, "fixture_id": fixture_id, "equipe_id": stats_equipe.get("equipe_id")},
    )

    cur.execute(
        "UPDATE matchs SET stats_recuperees = TRUE WHERE fixture_id = %s;",
        (fixture_id,),
    )


def main():
    fixtures = charger_fixtures("fixtures_recuperes.json")
    stats_par_match = charger_stats("stats_recuperees.json")

    logger.info("%s fixtures et %s matchs avec stats à charger", len(fixtures), len(stats_par_match))

    conn = psycopg2.connect(**CONNEXION_PARAMS)
    try:
        with conn.cursor() as cur:
            # 1. Équipes d'abord (car matchs et stats_match ont des FK vers equipes)
            for fixture in fixtures:
                inserer_equipe(cur, fixture.get("equipe_domicile_id"), fixture.get("equipe_domicile"))
                inserer_equipe(cur, fixture.get("equipe_exterieur_id"), fixture.get("equipe_exterieur"))

            # 2. Les matchs
            for fixture in fixtures:
                inserer_match(cur, fixture)

            # 3. Les statistiques (structure : {"1208078": [stats_equipe1, stats_equipe2], ...})
            for fixture_id_str, liste_stats in stats_par_match.items():
                fixture_id = int(fixture_id_str)
                for stats_equipe in liste_stats:
                    inserer_stats(cur, fixture_id, stats_equipe)

        conn.commit()
        logger.info("Chargement terminé avec succès")

    except Exception as exc:
        conn.rollback()
        logger.error("Erreur pendant le chargement, tout annulé (rollback) : %s", exc)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()