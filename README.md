# ⚽ Football Analytics

Pipeline de données de bout en bout analysant les dynamiques de jeu en Premier League — collecte, transformation, et visualisation interactive de ce qui se passe réellement sur le terrain (possession, tirs, corners, discipline).

![CI/CD](https://github.com/Chaymae-chek/projet-foot/actions/workflows/ci.yml/badge.svg)

## 📊 Aperçu

Ce projet reproduit une architecture de data engineering complète et industrialisée, développée en autonomie pour approfondir mes compétences en data engineering : collecte automatisée, modélisation en couches, tests de qualité, dashboard interactif, conteneurisation et orchestration.

**Question analytique centrale** : que révèlent les statistiques de jeu (possession, tirs, corners, discipline) sur la façon dont une équipe joue et gagne — match par match et sur une saison entière ?

## 🏗️ Architecture

```
API-Football (source de données)
        |
        v
   Scraper Python  ---- consulte la base avant chaque appel
        |              (evite de re-consommer le quota gratuit)
        v
  PostgreSQL (raw)
        |
        v
   dbt (staging -> marts)  ---- 17 tests de qualite de donnees
        |
        v
  Dashboard Dash/Plotly  ---- 3 vues interactives
        |
        v
   Orchestre par Dagster (scraper -> chargement -> dbt -> dashboard)
        |
   Conteneurise avec Docker + teste automatiquement via CI/CD
```

## 🛠️ Stack technique

| Catégorie | Outils |
|---|---|
| Langage | Python 3.12 |
| Collecte de données | API-Football (REST), requests |
| Base de données | PostgreSQL 16 |
| Transformation | dbt (data build tool) |
| Visualisation | Dash, Plotly |
| Orchestration | Dagster |
| Conteneurisation | Docker, Docker Compose |
| Tests | pytest (code), dbt tests (données) |
| CI/CD | GitHub Actions |

## ✨ Fonctionnalités du dashboard

- **Vue Équipe** — classement des 20 équipes de Premier League sur plusieurs métriques (possession, tirs, corners, passes), avec sélection dynamique de la métrique affichée
- **Vue Match** — détail d'un match précis : score, et comparaison en barres groupées des statistiques des deux équipes
- **Comparaison** — face-à-face entre 2 équipes au choix, sous forme de radar chart

## 📸 Captures d'écran

Ajoute tes propres captures dans un dossier `screenshots/` à la racine du projet, puis ajoute ici :
`![Vue Équipe](screenshots/vue-equipe.png)`

## 🚀 Lancer le projet

### Option rapide — tout avec Docker

```
git clone https://github.com/Chaymae-chek/projet-foot.git
cd projet-foot
copy .env.example .env
docker compose build
docker compose up -d
```

Dashboard disponible sur http://localhost:8060

### Option détaillée — étape par étape

```
cd db
docker compose up -d

cd ../scraper
pip install -r requirements.txt
python api_client.py

cd ../db
python charger_json_vers_db.py

cd ../dbt_project
dbt run
dbt test

cd ../dashboard
pip install -r requirements.txt
python app.py
```

### Orchestration automatisée (Dagster)

```
cd orchestration
pip install -r requirements.txt
dagster dev -f dagster_pipeline.py
```

## ✅ Tests

```
cd scraper
pytest tests/ -v

cd dbt_project
dbt test
```

11 tests pytest + 17 tests dbt, exécutés automatiquement à chaque push via GitHub Actions.

## 📁 Structure du projet

```
projet-foot/
├── scraper/
├── db/
├── dbt_project/
├── dashboard/
├── orchestration/
├── .github/workflows/
├── docker-compose.yml
└── .env.example
```

## 🔍 Points techniques notables

- **Économie de quota** : le scraper interroge PostgreSQL avant chaque appel API pour ne jamais redemander les statistiques d'un match déjà en base
- **Idempotence** : les insertions en base utilisent ON CONFLICT DO NOTHING
- **Architecture en couches dbt** : séparation raw -> staging -> marts
- **CI/CD avec base éphémère** : les tests dbt tournent sur un PostgreSQL temporaire recréé à chaque run

---

*Projet développé pour approfondir mes compétences en data engineering : pipeline ELT, orchestration, tests, CI/CD.*