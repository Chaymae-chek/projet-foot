-- db/init_schema.sql
--
-- Schéma adapté aux données réelles retournées par parsers.py
-- (parser_liste_fixtures et parser_statistiques_match)

-- ============================================================
-- Table des équipes
-- ============================================================
CREATE TABLE IF NOT EXISTS equipes (
    id INT PRIMARY KEY,              -- l'id fourni par API-Football (pas un SERIAL : on réutilise leur id)
    nom VARCHAR(150) NOT NULL UNIQUE
);

-- ============================================================
-- Table des matchs (fixtures)
-- ============================================================
CREATE TABLE IF NOT EXISTS matchs (
    fixture_id INT PRIMARY KEY,      -- id unique du match chez API-Football
    date_match TIMESTAMP,
    statut VARCHAR(10),              -- 'FT' = terminé, 'NS' = pas encore joué, etc.
    journee VARCHAR(50),
    saison INT,
    equipe_domicile_id INT REFERENCES equipes(id),
    equipe_exterieur_id INT REFERENCES equipes(id),
    buts_domicile INT,
    buts_exterieur INT,
    stats_recuperees BOOLEAN NOT NULL DEFAULT FALSE,  -- clé pour l'économie de quota
    inseree_le TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Table des statistiques de match (une ligne par équipe et par match)
-- ============================================================
CREATE TABLE IF NOT EXISTS stats_match (
    id SERIAL PRIMARY KEY,
    fixture_id INT REFERENCES matchs(fixture_id),
    equipe_id INT REFERENCES equipes(id),
    possession DECIMAL(5,2),
    tirs_total INT,
    tirs_cadres INT,
    tirs_non_cadres INT,
    tirs_bloques INT,
    corners INT,
    fautes INT,
    cartons_jaunes INT,
    cartons_rouges INT,
    passes_total INT,
    passes_reussies INT,
    precision_passes DECIMAL(5,2),
    UNIQUE (fixture_id, equipe_id)   -- une seule ligne de stats par équipe et par match
);

-- ============================================================
-- Index utiles pour les requêtes fréquentes du dashboard
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_matchs_saison ON matchs(saison);
CREATE INDEX IF NOT EXISTS idx_matchs_stats_recuperees ON matchs(stats_recuperees);
CREATE INDEX IF NOT EXISTS idx_stats_match_equipe ON stats_match(equipe_id);