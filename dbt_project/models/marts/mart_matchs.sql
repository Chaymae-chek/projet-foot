-- models/marts/mart_matchs.sql
--
-- Table métier "un match = une ligne", avec les noms d'équipes
-- lisibles (au lieu des ids) et le vainqueur déjà calculé.
-- C'est cette table que la "Vue Match" du dashboard va interroger.

select
    m.fixture_id,
    m.date_match,
    m.journee,
    m.saison,
    ed.equipe_nom  as equipe_domicile,
    ee.equipe_nom  as equipe_exterieur,
    m.buts_domicile,
    m.buts_exterieur,
    case
        when m.buts_domicile > m.buts_exterieur then ed.equipe_nom
        when m.buts_exterieur > m.buts_domicile then ee.equipe_nom
        else 'Match nul'
    end as vainqueur,
    m.stats_recuperees
from {{ ref('stg_matchs') }} m
left join {{ ref('stg_equipes') }} ed on m.equipe_domicile_id = ed.equipe_id
left join {{ ref('stg_equipes') }} ee on m.equipe_exterieur_id = ee.equipe_id