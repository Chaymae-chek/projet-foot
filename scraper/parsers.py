"""
Fonctions de parsing pures pour les réponses JSON d'API-Football.

Comme pour le scraper FBref, ces fonctions ne font aucun appel réseau —
elles prennent des dicts Python (déjà désérialisés depuis du JSON) et
retournent des structures propres. Entièrement testables hors-ligne.
"""

from __future__ import annotations


def parser_fixture(fixture_brut: dict) -> dict:
    """
    Parse un élément de la réponse GET /fixtures d'API-Football.
    Structure réelle : {"fixture": {...}, "league": {...}, "teams": {...}, "goals": {...}}
    """
    fixture = fixture_brut.get("fixture", {})
    teams = fixture_brut.get("teams", {})
    goals = fixture_brut.get("goals", {})
    league = fixture_brut.get("league", {})

    return {
        "fixture_id": fixture.get("id"),
        "date": fixture.get("date"),
        "statut": (fixture.get("status") or {}).get("short"),
        "journee": league.get("round"),
        "saison": league.get("season"),
        "equipe_domicile": (teams.get("home") or {}).get("name"),
        "equipe_domicile_id": (teams.get("home") or {}).get("id"),
        "equipe_exterieur": (teams.get("away") or {}).get("name"),
        "equipe_exterieur_id": (teams.get("away") or {}).get("id"),
        "buts_domicile": goals.get("home"),
        "buts_exterieur": goals.get("away"),
    }


def parser_liste_fixtures(reponse_api: dict) -> list[dict]:
    """Parse la réponse complète GET /fixtures (clé 'response' = liste de fixtures)."""
    elements = reponse_api.get("response", [])
    return [parser_fixture(f) for f in elements]


# Table de correspondance entre les libellés bruts de l'API et nos noms de colonnes
_CORRESPONDANCE_STATS = {
    "Ball Possession": "possession",
    "Total Shots": "tirs_total",
    "Shots on Goal": "tirs_cadres",
    "Shots off Goal": "tirs_non_cadres",
    "Blocked Shots": "tirs_bloques",
    "Corner Kicks": "corners",
    "Fouls": "fautes",
    "Yellow Cards": "cartons_jaunes",
    "Red Cards": "cartons_rouges",
    "Total passes": "passes_total",
    "Passes accurate": "passes_reussies",
    "Passes %": "precision_passes",
}


def _nettoyer_valeur_stat(valeur):
    """Certaines valeurs arrivent en '58%' (str) plutôt qu'en nombre -> on normalise."""
    if valeur is None:
        return None
    if isinstance(valeur, str) and valeur.endswith("%"):
        try:
            return float(valeur.replace("%", ""))
        except ValueError:
            return None
    return valeur


def parser_statistiques_match(reponse_api: dict) -> list[dict]:
    """
    Parse la réponse GET /fixtures/statistics?fixture={id}.
    Structure réelle : {"response": [ {"team": {...}, "statistics": [{"type": "...", "value": ...}, ...]}, ... ]}
    Retourne une liste de 2 dicts (un par équipe), avec des clés normalisées.
    """
    elements = reponse_api.get("response", [])
    resultat = []

    for element in elements:
        equipe = element.get("team", {})
        stats_brutes = element.get("statistics", [])

        stats_normalisees = {"equipe_id": equipe.get("id"), "equipe_nom": equipe.get("name")}

        for stat in stats_brutes:
            type_stat = stat.get("type")
            cle = _CORRESPONDANCE_STATS.get(type_stat)
            if cle is not None:
                stats_normalisees[cle] = _nettoyer_valeur_stat(stat.get("value"))

        resultat.append(stats_normalisees)

    return resultat