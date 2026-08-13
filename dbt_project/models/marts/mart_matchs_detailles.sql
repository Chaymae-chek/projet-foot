-- models/marts/mart_matchs_detailles.sql
--
-- Un match par ligne, mais avec les stats des DEUX équipes côte à côte
-- (préfixes dom_/ext_). C'est la table que la "Vue Match" du dashboard
-- interroge pour construire ses graphiques de comparaison.

select
    m.fixture_id,
    m.date_match,
    m.journee,
    m.equipe_domicile,
    m.equipe_exterieur,
    m.buts_domicile,
    m.buts_exterieur,
    m.vainqueur,

    sd.possession        as dom_possession,
    sd.tirs_total         as dom_tirs_total,
    sd.tirs_cadres         as dom_tirs_cadres,
    sd.corners             as dom_corners,
    sd.fautes              as dom_fautes,
    sd.cartons_jaunes      as dom_cartons_jaunes,
    sd.cartons_rouges      as dom_cartons_rouges,
    sd.passes_reussies     as dom_passes_reussies,
    sd.precision_passes    as dom_precision_passes,

    se.possession        as ext_possession,
    se.tirs_total         as ext_tirs_total,
    se.tirs_cadres         as ext_tirs_cadres,
    se.corners             as ext_corners,
    se.fautes              as ext_fautes,
    se.cartons_jaunes      as ext_cartons_jaunes,
    se.cartons_rouges      as ext_cartons_rouges,
    se.passes_reussies     as ext_passes_reussies,
    se.precision_passes    as ext_precision_passes

from {{ ref('mart_matchs') }} m
join {{ ref('stg_matchs') }} sm
    on m.fixture_id = sm.fixture_id
join {{ ref('stg_stats_match') }} sd
    on sd.fixture_id = m.fixture_id and sd.equipe_id = sm.equipe_domicile_id
join {{ ref('stg_stats_match') }} se
    on se.fixture_id = m.fixture_id and se.equipe_id = sm.equipe_exterieur_id
where m.stats_recuperees = true