-- models/marts/mart_stats_equipe.sql
--
-- Agrège les statistiques de jeu par équipe, sur tous les matchs
-- pour lesquels on a des données -- exactement ce qu'il faut pour
-- répondre à "qu'est-ce qui se passe sur le terrain" au niveau
-- d'une équipe sur la saison. C'est la table de la "Vue Équipe".

select
    e.equipe_nom,
    count(*)                                as matchs_avec_stats,
    round(avg(s.possession), 1)             as possession_moyenne,
    round(avg(s.tirs_total), 1)             as tirs_moyens,
    round(avg(s.tirs_cadres), 1)            as tirs_cadres_moyens,
    round(avg(s.corners), 1)                as corners_moyens,
    round(avg(s.passes_reussies), 1)        as passes_reussies_moyennes,
    round(avg(s.precision_passes), 1)       as precision_passes_moyenne,
    sum(s.cartons_jaunes)                   as total_cartons_jaunes,
    sum(s.cartons_rouges)                   as total_cartons_rouges
from {{ ref('stg_stats_match') }} s
join {{ ref('stg_equipes') }} e on s.equipe_id = e.equipe_id
group by e.equipe_nom
order by possession_moyenne desc