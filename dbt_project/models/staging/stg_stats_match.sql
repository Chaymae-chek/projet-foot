-- models/staging/stg_stats_match.sql
--
-- Reprend la table brute `stats_match` telle quelle -- elle est déjà
-- propre grâce au parsing fait en amont (parsers.py) -- mais on passe
-- quand même par une couche staging pour garder l'architecture
-- cohérente (raw -> staging -> marts) et pouvoir y ajouter des règles
-- de nettoyage plus tard sans toucher aux marts.

select
    fixture_id,
    equipe_id,
    possession,
    tirs_total,
    tirs_cadres,
    tirs_non_cadres,
    tirs_bloques,
    corners,
    fautes,
    cartons_jaunes,
    cartons_rouges,
    passes_total,
    passes_reussies,
    precision_passes
from {{ source('public', 'stats_match') }}