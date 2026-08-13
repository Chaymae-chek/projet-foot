"""
Pipeline Dagster — orchestre l'enchaînement complet :

    scraper (api_client.py)
        -> chargement en base (charger_json_vers_db.py)
            -> transformation dbt (dbt run)
                -> tests de qualité (dbt test)

Chaque étape est un "op" -- ce fichier automatise exactement les commandes
que tu tapais à la main jusqu'ici (voir les commentaires sous chaque op).

Lancer l'interface Dagster :
    cd orchestration
    dagster dev -f dagster_pipeline.py
Puis ouvrir http://localhost:3000 -- clique sur "Materialize"/"Launch Run"
pour déclencher le pipeline complet manuellement, ou laisse le schedule
quotidien s'en charger tout seul.
"""

import os
import shutil
import subprocess

from dagster import (
    op,
    job,
    schedule,
    Definitions,
    OpExecutionContext,
    Failure,
    ScheduleEvaluationContext,
    RunRequest,
)

# ============================================================
# Chemins vers les autres dossiers du projet (en supposant que
# orchestration/ est au même niveau que scraper/, db/, dbt_project/)
# ============================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_SCRAPER = os.path.join(RACINE, "scraper")
DOSSIER_DB = os.path.join(RACINE, "db")
DOSSIER_DBT = os.path.join(RACINE, "dbt_project")


def _executer_commande(context: OpExecutionContext, commande: list[str], dossier: str) -> None:
    """
    Lance une commande shell dans un dossier donné, logge sa sortie dans
    l'interface Dagster, et transforme un code de sortie non-nul en
    échec explicite de l'op (au lieu de continuer silencieusement).
    """
    resultat = subprocess.run(
        commande, cwd=dossier, capture_output=True, text=True, env=os.environ,
    )
    if resultat.stdout:
        context.log.info(resultat.stdout)
    if resultat.stderr:
        context.log.warning(resultat.stderr)

    if resultat.returncode != 0:
        raise Failure(f"Commande {' '.join(commande)} échouée (code {resultat.returncode}) dans {dossier}")


# ============================================================
# OP 1 -- équivalent de : cd scraper && python api_client.py
# ============================================================
@op
def op_scraper(context: OpExecutionContext) -> bool:
    context.log.info("Lancement du scraper (récupération des nouveaux matchs)...")
    _executer_commande(context, ["python", "api_client.py"], DOSSIER_SCRAPER)
    return True


# ============================================================
# OP 2 -- équivalent de :
#   copy fixtures_recuperes.json ..\db\ -Force
#   copy stats_recuperees.json ..\db\ -Force
#   cd db && python charger_json_vers_db.py
# ============================================================
@op
def op_charger_en_base(context: OpExecutionContext, depend_de: bool) -> bool:
    context.log.info("Copie des fichiers JSON vers db/...")
    for nom_fichier in ["fixtures_recuperes.json", "stats_recuperees.json"]:
        source = os.path.join(DOSSIER_SCRAPER, nom_fichier)
        destination = os.path.join(DOSSIER_DB, nom_fichier)
        shutil.copy(source, destination)

    context.log.info("Chargement en base PostgreSQL...")
    _executer_commande(context, ["python", "charger_json_vers_db.py"], DOSSIER_DB)
    return True


# ============================================================
# OP 3 -- équivalent de : cd dbt_project && dbt run
# ============================================================
@op
def op_dbt_run(context: OpExecutionContext, depend_de: bool) -> bool:
    context.log.info("Transformation des données avec dbt (dbt run)...")
    _executer_commande(context, ["dbt", "run"], DOSSIER_DBT)
    return True


# ============================================================
# OP 4 -- équivalent de : cd dbt_project && dbt test
# ============================================================
@op
def op_dbt_test(context: OpExecutionContext, depend_de: bool) -> None:
    context.log.info("Vérification de la qualité des données (dbt test)...")
    _executer_commande(context, ["dbt", "test"], DOSSIER_DBT)
    context.log.info("Pipeline complet terminé avec succès -- le dashboard reflète maintenant les nouvelles données.")


# ============================================================
# JOB -- enchaîne les 4 ops dans l'ordre
# ============================================================
@job
def pipeline_football():
    resultat_scraper = op_scraper()
    resultat_chargement = op_charger_en_base(resultat_scraper)
    resultat_dbt_run = op_dbt_run(resultat_chargement)
    op_dbt_test(resultat_dbt_run)


# ============================================================
# SCHEDULE -- déclenche le pipeline chaque jour à 9h
# (le quota API-Football se reset à 00h UTC, donc 9h laisse
# une bonne marge tout en gardant une heure fixe et prévisible)
# ============================================================
@schedule(cron_schedule="0 9 * * *", job=pipeline_football)
def schedule_quotidien(context: ScheduleEvaluationContext) -> RunRequest:
    return RunRequest(run_key=None)


defs = Definitions(
    jobs=[pipeline_football],
    schedules=[schedule_quotidien],
)