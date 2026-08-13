"""
Dashboard Football Analytics — Dash/Plotly

3 vues :
  - Vue Équipe   : classement et comparaison des équipes sur la saison
  - Vue Match    : détail d'un match précis (stats des deux équipes)
  - Comparaison  : face-à-face entre 2 équipes au choix

Se connecte directement aux marts dbt (schéma `analytics`) —
aucune logique métier ici, tout le calcul a déjà été fait par dbt.
"""

from __future__ import annotations

import os

import pandas as pd
import psycopg
from dash import Dash, dcc, html, Input, Output, callback

# ============================================================
# CONNEXION BASE DE DONNÉES
# ============================================================
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": 5432,
    "dbname": "football_db",
    "user": "football",
    "password": "football_pwd",
}


def charger_donnees(requete: str) -> pd.DataFrame:
    with psycopg.connect(**DB_PARAMS) as conn:
        return pd.read_sql(requete, conn)


def charger_stats_equipe() -> pd.DataFrame:
    return charger_donnees("SELECT * FROM analytics.mart_stats_equipe ORDER BY possession_moyenne DESC;")


def charger_matchs_detailles() -> pd.DataFrame:
    return charger_donnees("SELECT * FROM analytics.mart_matchs_detailles ORDER BY date_match DESC;")


# ============================================================
# DESIGN TOKENS (cohérent avec le reste du projet)
# ============================================================
COULEURS = {
    "bg": "#0A0F1E",
    "surface": "#121A2E",
    "surface_2": "#17203A",
    "border": "#233052",
    "text": "#E7ECF6",
    "text_muted": "#8B96AF",
    "accent": "#38E0C8",
    "amber": "#F2B84B",
    "domicile": "#38E0C8",
    "exterieur": "#F2B84B",
}

STYLE_CARTE = {
    "backgroundColor": COULEURS["surface"],
    "border": f"1px solid {COULEURS['border']}",
    "borderRadius": "12px",
    "padding": "24px",
    "marginBottom": "20px",
}

STYLE_DROPDOWN = {
    "backgroundColor": COULEURS["surface_2"],
    "color": "#000",
    "borderRadius": "8px",
    "marginBottom": "16px",
}

MISE_EN_PAGE_GRAPHIQUE = dict(
    paper_bgcolor=COULEURS["surface"],
    plot_bgcolor=COULEURS["surface"],
    font=dict(color=COULEURS["text"], family="Arial"),
    xaxis=dict(gridcolor=COULEURS["border"]),
    yaxis=dict(gridcolor=COULEURS["border"]),
    margin=dict(l=40, r=20, t=50, b=40),
)

# Styles explicites des onglets -- le thème par défaut de dcc.Tabs part du
# principe d'un fond clair, donc sans ça le texte des onglets non-sélectionnés
# est presque invisible sur un fond sombre.
STYLE_ONGLET = {
    "backgroundColor": COULEURS["surface"],
    "color": COULEURS["text_muted"],
    "border": f"1px solid {COULEURS['border']}",
    "padding": "14px",
    "fontWeight": "500",
}

STYLE_ONGLET_ACTIF = {
    "backgroundColor": COULEURS["surface_2"],
    "color": COULEURS["accent"],
    "border": f"1px solid {COULEURS['accent']}",
    "borderBottom": f"3px solid {COULEURS['accent']}",
    "padding": "14px",
    "fontWeight": "700",
}

# ============================================================
# APP
# ============================================================
app = Dash(__name__, title="Football Analytics")
server = app.server  # utile pour un futur déploiement (gunicorn, etc.)

app.layout = html.Div(
    style={"backgroundColor": COULEURS["bg"], "minHeight": "100vh", "fontFamily": "Arial", "padding": "32px"},
    children=[
        html.Div(
            [
                html.H1("⚽ Football Analytics", style={"color": COULEURS["text"], "marginBottom": "4px"}),
                html.P(
                    "Qu'est-ce qui se passe sur le terrain — Premier League 2024",
                    style={"color": COULEURS["text_muted"], "marginTop": "0"},
                ),
            ],
            style={"marginBottom": "24px"},
        ),

        dcc.Tabs(
            id="onglets",
            value="vue-equipe",
            children=[
                dcc.Tab(label="Vue Équipe", value="vue-equipe", style=STYLE_ONGLET, selected_style=STYLE_ONGLET_ACTIF),
                dcc.Tab(label="Vue Match", value="vue-match", style=STYLE_ONGLET, selected_style=STYLE_ONGLET_ACTIF),
                dcc.Tab(label="Comparaison", value="comparaison", style=STYLE_ONGLET, selected_style=STYLE_ONGLET_ACTIF),
            ],
        ),

        html.Div(id="contenu-onglet", style={"marginTop": "24px"}),
    ],
)


# ============================================================
# CALLBACK PRINCIPAL : change le contenu selon l'onglet actif
# ============================================================
@callback(Output("contenu-onglet", "children"), Input("onglets", "value"))
def afficher_onglet(onglet_actif):
    if onglet_actif == "vue-equipe":
        return construire_vue_equipe()
    elif onglet_actif == "vue-match":
        return construire_vue_match()
    elif onglet_actif == "comparaison":
        return construire_vue_comparaison()
    return html.Div("Onglet inconnu")


# ============================================================
# VUE ÉQUIPE
# ============================================================
def construire_vue_equipe():
    df = charger_stats_equipe()

    metriques = {
        "possession_moyenne": "Possession moyenne (%)",
        "tirs_moyens": "Tirs moyens par match",
        "tirs_cadres_moyens": "Tirs cadrés moyens",
        "corners_moyens": "Corners moyens",
        "passes_reussies_moyennes": "Passes réussies moyennes",
        "precision_passes_moyenne": "Précision des passes (%)",
    }

    return html.Div(
        style=STYLE_CARTE,
        children=[
            html.H3("Classement des équipes", style={"color": COULEURS["text"]}),
            html.P(
                f"Basé sur {df['matchs_avec_stats'].sum()} lignes de statistiques collectées jusqu'ici.",
                style={"color": COULEURS["text_muted"], "fontSize": "13px"},
            ),
            dcc.Dropdown(
                id="metrique-equipe",
                options=[{"label": v, "value": k} for k, v in metriques.items()],
                value="possession_moyenne",
                clearable=False,
                style=STYLE_DROPDOWN,
            ),
            dcc.Graph(id="graphique-equipe"),
        ],
    )


@callback(Output("graphique-equipe", "figure"), Input("metrique-equipe", "value"))
def maj_graphique_equipe(metrique):
    df = charger_stats_equipe().sort_values(metrique, ascending=True)

    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=df[metrique],
        y=df["equipe_nom"],
        orientation="h",
        marker=dict(color=COULEURS["accent"]),
    ))
    fig.update_layout(**MISE_EN_PAGE_GRAPHIQUE, height=560)
    return fig


# ============================================================
# VUE MATCH
# ============================================================
def construire_vue_match():
    df = charger_matchs_detailles()

    if df.empty:
        return html.Div(
            "Aucun match avec statistiques complètes pour le moment — relance le scraper puis dbt run.",
            style={**STYLE_CARTE, "color": COULEURS["text_muted"]},
        )

    options_matchs = [
        {
            "label": f"{r.equipe_domicile} {r.buts_domicile}-{r.buts_exterieur} {r.equipe_exterieur} ({r.date_match})",
            "value": r.fixture_id,
        }
        for r in df.itertuples()
    ]

    return html.Div(
        style=STYLE_CARTE,
        children=[
            html.H3("Détail d'un match", style={"color": COULEURS["text"]}),
            dcc.Dropdown(
                id="selection-match",
                options=options_matchs,
                value=options_matchs[0]["value"],
                clearable=False,
                style=STYLE_DROPDOWN,
            ),
            html.Div(id="resume-match", style={"marginBottom": "16px"}),
            dcc.Graph(id="graphique-match"),
        ],
    )


@callback(
    [Output("resume-match", "children"), Output("graphique-match", "figure")],
    Input("selection-match", "value"),
)
def maj_vue_match(fixture_id):
    df = charger_matchs_detailles()
    m = df[df["fixture_id"] == fixture_id].iloc[0]

    resume = html.Div(
        [
            html.Span(f"{m.equipe_domicile} ", style={"color": COULEURS["domicile"], "fontWeight": "bold"}),
            html.Span(f"{m.buts_domicile} - {m.buts_exterieur}", style={"color": COULEURS["text"], "fontSize": "20px", "margin": "0 10px"}),
            html.Span(f"{m.equipe_exterieur}", style={"color": COULEURS["exterieur"], "fontWeight": "bold"}),
            html.Div(f"Vainqueur : {m.vainqueur} · Journée {m.journee}", style={"color": COULEURS["text_muted"], "fontSize": "13px", "marginTop": "6px"}),
        ]
    )

    metriques = ["possession", "tirs_total", "tirs_cadres", "corners", "cartons_jaunes"]
    labels = ["Possession (%)", "Tirs totaux", "Tirs cadrés", "Corners", "Cartons jaunes"]

    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=m.equipe_domicile,
        x=labels,
        y=[m[f"dom_{met}"] for met in metriques],
        marker=dict(color=COULEURS["domicile"]),
    ))
    fig.add_trace(go.Bar(
        name=m.equipe_exterieur,
        x=labels,
        y=[m[f"ext_{met}"] for met in metriques],
        marker=dict(color=COULEURS["exterieur"]),
    ))
    fig.update_layout(**MISE_EN_PAGE_GRAPHIQUE, barmode="group", height=440,
                       legend=dict(bgcolor="rgba(0,0,0,0)"))
    return resume, fig


# ============================================================
# COMPARAISON (2 équipes tête-à-tête)
# ============================================================
def construire_vue_comparaison():
    df = charger_stats_equipe()
    options = [{"label": nom, "value": nom} for nom in sorted(df["equipe_nom"])]

    return html.Div(
        style=STYLE_CARTE,
        children=[
            html.H3("Comparaison tête-à-tête", style={"color": COULEURS["text"]}),
            html.Div(
                style={"display": "flex", "gap": "16px"},
                children=[
                    dcc.Dropdown(id="equipe-a", options=options, value=options[0]["value"],
                                 clearable=False, style={**STYLE_DROPDOWN, "flex": 1}),
                    dcc.Dropdown(id="equipe-b", options=options, value=options[-1]["value"],
                                 clearable=False, style={**STYLE_DROPDOWN, "flex": 1}),
                ],
            ),
            dcc.Graph(id="graphique-comparaison"),
        ],
    )


@callback(
    Output("graphique-comparaison", "figure"),
    [Input("equipe-a", "value"), Input("equipe-b", "value")],
)
def maj_comparaison(equipe_a, equipe_b):
    df = charger_stats_equipe().set_index("equipe_nom")

    metriques = ["possession_moyenne", "tirs_moyens", "tirs_cadres_moyens", "corners_moyens", "precision_passes_moyenne"]
    labels = ["Possession", "Tirs", "Tirs cadrés", "Corners", "Précision passes"]

    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[df.loc[equipe_a, met] for met in metriques],
        theta=labels, fill="toself", name=equipe_a,
        line=dict(color=COULEURS["domicile"]),
    ))
    fig.add_trace(go.Scatterpolar(
        r=[df.loc[equipe_b, met] for met in metriques],
        theta=labels, fill="toself", name=equipe_b,
        line=dict(color=COULEURS["exterieur"]),
    ))
    fig.update_layout(
        **MISE_EN_PAGE_GRAPHIQUE,
        polar=dict(
            bgcolor=COULEURS["surface"],
            radialaxis=dict(gridcolor=COULEURS["border"], color=COULEURS["text_muted"]),
            angularaxis=dict(gridcolor=COULEURS["border"], color=COULEURS["text"]),
        ),
        height=520,
        showlegend=True,
    )
    return fig


if __name__ == "__main__":
    # host="0.0.0.0" : indispensable en conteneur Docker pour que le port
    # publié (8060) puisse atteindre le serveur -- "127.0.0.1" par défaut
    # ne serait accessible que depuis l'intérieur du conteneur lui-même.
    # debug=True reste pratique en local (hors Docker) ; on le désactive
    # par défaut pour un usage "conteneurisé" plus proche de la production.
    mode_debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8060, debug=mode_debug)