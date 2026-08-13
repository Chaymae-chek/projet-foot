-- models/staging/stg_equipes.sql
--
-- Renomme simplement les colonnes de la table brute `equipes` pour
-- des noms plus explicites et cohérents dans toute la suite du projet.

select
    id   as equipe_id,
    nom  as equipe_nom
from {{ source('public', 'equipes') }}