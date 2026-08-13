-- models/staging/stg_matchs.sql
--
-- Nettoie la table brute `matchs` : typage explicite de la date,
-- et on garde uniquement les matchs terminés (statut FT) puisque ce
-- sont les seuls exploitables pour l'analyse.

select
    fixture_id,
    date_match::date  as date_match,
    statut,
    journee,
    saison,
    equipe_domicile_id,
    equipe_exterieur_id,
    buts_domicile,
    buts_exterieur,
    stats_recuperees
from {{ source('public', 'matchs') }}
where statut = 'FT'