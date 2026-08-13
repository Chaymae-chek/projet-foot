# Football Analytics

Pipeline de données de bout en bout pour l'analyse des statistiques de matchs de Premier League.

Le projet couvre la collecte des données depuis une API, leur stockage dans PostgreSQL, leur transformation avec dbt, leur orchestration avec Dagster et leur visualisation à travers un dashboard interactif Dash/Plotly.

![CI/CD](https://github.com/Chaymae-chek/projet-foot/actions/workflows/ci.yml/badge.svg)

## Objectif

Analyser les statistiques de matchs de Premier League afin d'étudier les performances des équipes à partir de différents indicateurs : possession, tirs, corners, passes et discipline.

Le pipeline permet de suivre les données depuis leur ingestion jusqu'à leur exploitation dans le dashboard.

## Architecture

```text
API-Football
     │
     ▼
Scraper Python
     │
     ▼
PostgreSQL
     │
     ▼
dbt
(raw → staging → marts)
     │
     ▼
Dash / Plotly
     │
     ▼
Dashboard

Dagster : orchestration du pipeline
Docker : conteneurisation
GitHub Actions : CI/CD
```

## Stack technique

| Domaine           | Technologies           |
| ----------------- | ---------------------- |
| Langage           | Python 3.12            |
| Source de données | API-Football           |
| Ingestion         | Python, Requests       |
| Base de données   | PostgreSQL 16          |
| Transformation    | dbt                    |
| Visualisation     | Dash, Plotly           |
| Orchestration     | Dagster                |
| Conteneurisation  | Docker, Docker Compose |
| Tests             | Pytest, dbt tests      |
| CI/CD             | GitHub Actions         |

## Dashboard

Le dashboard propose trois vues principales :

### Vue Équipe

Classement des équipes de Premier League selon différentes statistiques :

* Possession
* Tirs
* Corners
* Passes
* Statistiques de jeu disponibles

La métrique affichée peut être sélectionnée dynamiquement.

### Vue Match

Analyse détaillée d'un match avec :

* Score final
* Équipes participantes
* Statistiques des deux équipes
* Comparaison graphique des performances

### Comparaison

Comparaison entre deux équipes à partir de plusieurs indicateurs, avec une visualisation sous forme de radar chart.

## Pipeline de données

### 1. Ingestion

Les données sont récupérées depuis API-Football à l'aide d'un client Python.

Avant chaque appel API, le scraper vérifie si les données du match sont déjà présentes en base afin de limiter les appels inutiles et de préserver le quota disponible.

### 2. Stockage

Les données brutes sont stockées dans PostgreSQL.

### 3. Transformation

Les données sont transformées avec dbt selon une architecture en couches :

```text
raw
 │
 ▼
staging
 │
 ▼
marts
```

Les modèles staging permettent de nettoyer et standardiser les données. Les modèles marts sont destinés à l'analyse.

### 4. Tests

La qualité des données est contrôlée avec des tests Pytest et des tests dbt.

Le projet comprend actuellement :

* 11 tests Pytest
* 17 tests dbt

Les tests sont exécutés automatiquement via GitHub Actions.

### 5. Orchestration

Dagster permet d'orchestrer les différentes étapes du pipeline :

```text
Scraping
   ↓
Chargement PostgreSQL
   ↓
Transformation dbt
   ↓
Dashboard
```

## Points techniques

### Gestion du quota API

Le scraper vérifie la présence des données en base avant d'effectuer un nouvel appel à l'API.

Cela permet de limiter les appels inutiles et de réduire la consommation du quota.

### Idempotence

Les insertions en base utilisent notamment :

```sql
ON CONFLICT DO NOTHING
```

afin d'éviter les doublons lors des exécutions répétées.

### Modélisation dbt

Les données sont organisées en trois niveaux :

```text
raw → staging → marts
```

Cette organisation facilite la maintenance et la séparation entre données brutes, données préparées et données analytiques.

### CI/CD

GitHub Actions exécute automatiquement les tests lors des modifications du repository.

### Conteneurisation

Les différents composants du projet peuvent être exécutés avec Docker et Docker Compose afin de faciliter la configuration et le déploiement de l'environnement.

## Structure du projet

```text
projet-foot/
│
├── scraper/
│   ├── api_client.py
│   ├── parsers.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── db/
│   ├── charger_json_vers_db.py
│   ├── init_schema.sql
│   └── requirements.txt
│
├── dbt_project/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       └── marts/
│
├── dashboard/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── orchestration/
│   ├── dagster_pipeline.py
│   └── requirements.txt
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Installation

### Prérequis

* Python 3.12+
* Docker et Docker Compose
* Git
* Une clé API-Football

### Cloner le projet

```bash
git clone https://github.com/Chaymae-chek/projet-foot.git
cd projet-foot
```

### Configuration

Créer le fichier `.env` à partir du modèle :

```bash
cp .env.example .env
```

Puis renseigner les paramètres nécessaires, notamment la clé API et les informations de connexion PostgreSQL.

Le fichier `.env` ne doit pas être versionné lorsqu'il contient des informations sensibles.

## Exécution avec Docker

```bash
docker compose build
docker compose up -d
```

Le dashboard est accessible sur :

```text
http://localhost:8060
```

## Exécution manuelle

### Scraper

```bash
cd scraper
pip install -r requirements.txt
python api_client.py
```

### Chargement des données

```bash
cd ../db
python charger_json_vers_db.py
```

### dbt

```bash
cd ../dbt_project
dbt run
dbt test
```

### Dashboard

```bash
cd ../dashboard
pip install -r requirements.txt
python app.py
```

## Orchestration avec Dagster

```bash
cd orchestration
pip install -r requirements.txt
dagster dev -f dagster_pipeline.py
```

## Tests

Tests Python :

```bash
cd scraper
pytest tests/ -v
```

Tests dbt :

```bash
cd dbt_project
dbt test
```

Les tests sont également exécutés automatiquement avec GitHub Actions.

## Compétences

* Python
* API REST
* Data ingestion
* PostgreSQL
* SQL
* dbt
* Data modeling
* Data quality testing
* Dash / Plotly
* Dagster
* Docker
* Git / GitHub
* GitHub Actions
* CI/CD

## Auteur

**Chaymae Chekrouni**

Étudiante ingénieure en Data & Software Engineering à l'INSEA.

GitHub : https://github.com/Chaymae-chek
