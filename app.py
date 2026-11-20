"""Collèges et risques : quels collèges publics du Loiret diagnostiquer en premier.

Lancer : uv run streamlit run app.py
Les calculs sont dans risques.py, le design dans theme.py ; ce fichier filtre et affiche.
Parcours : indicateurs → carte ou classement (un clic choisit un collège) → fiche du collège.
"""

from html import escape

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import theme
from risques import (
    CARTES_ARGILES,
    DIAGNOSTICS,
    FAMILLES,
    FAMILLES_COURT,
    FICHIER_CATNAT,
    FICHIER_HISTORIQUE,
    FICHIER_PRIORITE,
    ORLEANS,
    SEUIL_CASIAS,
    SEUIL_SEVESO_KM,
    ajouter_familles,
    catnat_commune,
    charger_catnat,
    charger_historique,
    charger_priorite,
    classer,
    compter_familles,
    distance_km,
    facteurs,
    filtrer_communes,
    historique_college,
    indicateurs,
)

st.set_page_config(page_title="Collèges et risques · Loiret", page_icon="🏫", layout="wide")
st.markdown(theme.CSS, unsafe_allow_html=True)

RAYON_ORLEANS_KM = 15


@st.cache_data
def donnees(version: tuple[float, ...]):
    """Les trois Parquet préparés. `version` (dates de modification des fichiers) fait partie
    de la clé du cache : après un git push qui change les données, le cache se renouvelle."""
    return charger_priorite(), charger_historique(), charger_catnat()


def fr(n: float) -> str:
    """Nombre à la française ; l'espace fine insécable empêche « 8 941 » de se couper."""
    return f"{n:,.0f}".replace(",", " ")


def niveau(n: int) -> str:
    return "aucun risque" if n == 0 else f"{n} risque{'s' if n > 1 else ''}"


def point_clique(cle: str) -> str | None:
    """Collège cliqué sur le graphique `cle`, seulement si le clic est nouveau."""
    etat = st.session_state.get(cle)
    try:
        points = etat["selection"]["points"]
    except (TypeError, KeyError):
        points = []
    uai = None
    if points:
        cd = points[0].get("customdata")
        uai = cd[0] if isinstance(cd, list | tuple) else cd
    precedent = st.session_state.get(f"_{cle}")
    st.session_state[f"_{cle}"] = uai
    return uai if uai and uai != precedent else None


colleges, historique, catnat = donnees(
    tuple(f.stat().st_mtime for f in (FICHIER_PRIORITE, FICHIER_HISTORIQUE, FICHIER_CATNAT))
)

# ---------------------------------------------------------------- filtres
with st.sidebar:
    st.markdown("### Filtres")
    familles = st.pills(
        "Familles de risque prises en compte",
        options=list(FAMILLES),
        default=list(FAMILLES),
        selection_mode="multi",
        format_func=FAMILLES_COURT.get,
        help="Le classement ne compte que les familles choisies.",
    )
    communes = st.multiselect(
        "Communes",
        options=sorted(colleges["commune"].unique()),
        placeholder="Toutes les communes",
        help="Sans choix, toutes les communes qui ont un collège public sont affichées.",
    )
    seulement_hausse = st.toggle("Seulement les collèges qui gagnent des élèves (2020 → 2025)")
    st.markdown("### Sensibilité")
    carte_argiles = (
        st.segmented_control(
            "Carte des argiles",
            options=list(CARTES_ARGILES),
            default="geoloiret",
            format_func={"geoloiret": "GéoLoiret", "georisques": "Géorisques"}.get,
            help="GéoLoiret compte 10 collèges en aléa fort, Géorisques 34 en exposition "
            "importante : le classement dépend de la carte choisie.",
        )
        or "geoloiret"
    )
    seuil_seveso = st.slider(
        "Distance à un site Seveso comptée comme risque (km)",
        min_value=0.5,
        max_value=5.0,
        value=SEUIL_SEVESO_KM,
        step=0.5,
        help="Testez la sensibilité du classement à ce rayon, qui est un choix du projet.",
    )
    seuil_casias = st.slider(
        "Anciens sites industriels à moins de 500 m, à partir de",
        min_value=1,
        max_value=20,
        value=SEUIL_CASIAS,
        help="Par défaut 5 : le quart des collèges les plus entourés. À 1, 40 collèges sur 58 "
        "seraient comptés.",
    )
    st.markdown("### Règles")
    st.markdown(
        '<div class="note"><b>Sol</b> : argiles fortes selon la carte choisie, ou cavité, ou '
        "mouvement de terrain à moins de 500 m.<br><b>Inondation</b> : dans un périmètre de "
        "PPRI, ou remontée de nappe existante.<br><b>Technologique</b> : zone TMD de 500 m, "
        "ou site Seveso dans le rayon choisi.<br><b>Sols pollués</b> : anciens sites "
        "industriels (CASIAS) à moins de 500 m, au-delà du seuil choisi.<br><br>Rayons et "
        "seuils choisis par le projet, pas des seuils officiels.</div>",
        unsafe_allow_html=True,
    )

if not familles:
    st.warning("Choisissez au moins une famille de risque.")
    st.stop()

vue = compter_familles(
    ajouter_familles(colleges, seuil_seveso, carte_argiles, seuil_casias), familles
)
vue = filtrer_communes(vue, communes)
if seulement_hausse:
    vue = vue[vue["evolution_pct"] > 0]
if vue.empty:
    st.warning("Aucun collège ne correspond à ces filtres.")
    st.stop()
vue = classer(vue)
vue["niveau"] = vue["nb_familles"].map(niveau)
k = indicateurs(vue)
perimetre = f"rentrée 2025 · {k['colleges']} collège{'s' if k['colleges'] > 1 else ''} public"
perimetre += "s" if k["colleges"] > 1 else ""
if communes:
    perimetre += " · " + (
        ", ".join(communes) if len(communes) <= 3 else f"{len(communes)} communes"
    )

# ---------------------------------------------------------------- collège choisi
options = vue["uai"].tolist()
for cle in ("carte", "classement"):
    nouveau = point_clique(cle)
    if nouveau in options:
        st.session_state["college"] = nouveau
if st.session_state.get("college") not in options:
    st.session_state["college"] = options[0]
choisi = st.session_state["college"]

# ---------------------------------------------------------------- en-tête
part = k["eleves_cumul"] / max(vue["effectif_total"].sum(), 1)
# Le titre dit le constat, accordé au nombre : aucun, un, ou plusieurs collèges.
if k["colleges_cumul"] == 0:
    titre_hero = 'Aucun collège ne cumule <span class="serif grad">deux risques</span>'
    phrase = (
        f"Mais <b>{k['colleges_expose']} sur {k['colleges']}</b> sont exposés à un risque "
        f"({fr(k['eleves_expose'])} élèves)."
    )
else:
    un = k["colleges_cumul"] == 1
    titre_hero = (
        f"{k['colleges_cumul']} collège{'' if un else 's'} cumule{'' if un else 'nt'} "
        '<span class="serif grad">au moins deux risques</span>'
    )
    phrase = (
        f"<b>{fr(k['eleves_cumul'])} élèves</b> y ont cours, soit {part:.0%} des élèves "
        "des collèges affichés."
    )
st.markdown(
    f"""
<div class="hero">
  <span class="pill"><span class="dot"></span>Département du Loiret
    <span class="tag">{escape(perimetre)}</span></span>
  <h1>{titre_hero}</h1>
  <p class="lead">{phrase} Cliquez un collège sur la carte ou dans le classement pour savoir
    <b>quel diagnostic demander en premier</b>.</p>
  <div class="kpis">
    <div class="kpi"><div class="lab">Collèges à 2 risques ou +</div>
      <div class="val grad">{k["colleges_cumul"]}</div>
      <div class="sub">sur {k["colleges"]} collèges publics</div></div>
    <div class="kpi"><div class="lab">Élèves concernés</div>
      <div class="val">{fr(k["eleves_cumul"])}</div>
      <div class="sub">dans ces collèges, rentrée 2025</div></div>
    <div class="kpi"><div class="lab">Exposés à 1 risque ou +</div>
      <div class="val">{k["colleges_expose"]}<span class="sur"> / {k["colleges"]}</span></div>
      <div class="sub">{fr(k["eleves_expose"])} élèves</div></div>
  </div>
</div>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- carte et classement
st.markdown(
    '<div class="section"><div class="eyebrow">01 · Vue d\'ensemble</div>'
    "<h2>Où sont les collèges exposés</h2></div>",
    unsafe_allow_html=True,
)


def afficher_carte() -> None:
    """La carte des collèges ; un clic choisit un collège."""
    with st.container(key="verre_carte"):
        cumul = vue[vue["nb_familles"] >= 2]
        pres = int((distance_km(cumul["lat"], cumul["lon"], ORLEANS) < RAYON_ORLEANS_KM).sum())
        titre = (
            f"{pres} des {len(cumul)} collèges à 2 risques ou + sont à moins de "
            f"{RAYON_ORLEANS_KM} km d'Orléans"
            if len(cumul)
            else "Aucun collège ne cumule deux risques avec ces filtres"
        )
        st.markdown(
            f'<div class="titre-graph">{titre}</div>'
            f'<div class="aide">{k["colleges"]} collèges · taille = élèves · '
            "un clic ouvre la fiche</div>",
            unsafe_allow_html=True,
        )
        carte = px.scatter_map(
            vue,
            lat="lat",
            lon="lon",
            size="effectif_total",
            size_max=22,
            color="niveau",
            color_discrete_map=theme.NIVEAUX,
            category_orders={"niveau": list(theme.NIVEAUX)},
            custom_data=["uai"],
            hover_name="nom",
            hover_data={
                "commune": True,
                "effectif_total": True,
                "familles_exposees": True,
                "lat": False,
                "lon": False,
                "niveau": False,
            },
            labels={
                "effectif_total": "Élèves",
                "familles_exposees": "Risques",
                "commune": "Commune",
            },
            map_style="carto-darkmatter",
            # Tout le Loiret par défaut ; zoom sur les collèges des communes choisies.
            center=(
                {"lat": vue["lat"].mean(), "lon": vue["lon"].mean()}
                if communes
                else {"lat": 47.9, "lon": 2.3}
            ),
            zoom=7.75 if not communes else (11 if len(communes) == 1 else 9),
        )
        sel = vue[vue["uai"] == choisi]
        carte.add_trace(
            go.Scattermap(
                lat=sel["lat"],
                lon=sel["lon"],
                customdata=sel[["uai"]].to_numpy(),
                mode="markers",
                marker={"size": 46, "color": theme.A1, "opacity": 0.28},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        theme.styliser(carte, 470)
        carte.update_layout(
            legend={
                "orientation": "h",
                "y": 0.99,
                "yanchor": "top",
                "x": 0.01,
                "bgcolor": "rgba(5,6,10,.7)",
            },
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
        )
        st.plotly_chart(
            carte,
            key="carte",
            on_select="rerun",
            selection_mode="points",
            width="stretch",
            config={"displayModeBar": False, "scrollZoom": True},
        )


def afficher_classement() -> None:
    """Les 15 premiers collèges exposés ; un clic choisit un collège."""
    with st.container(key="verre_classement"):
        top = vue[vue["nb_familles"] >= 1].head(15)
        if top.empty:
            st.info("Aucun collège exposé avec ces filtres.")
        else:
            tete = top.iloc[0]
            st.markdown(
                f'<div class="titre-graph">{escape(tete["nom"])} ({escape(tete["commune"])}) '
                f"arrive en tête avec {niveau(int(tete['nb_familles']))}</div>"
                f'<div class="aide">les {len(top)} premiers des {k["colleges_expose"]} exposés · '
                "classés par risques puis par élèves</div>",
                unsafe_allow_html=True,
            )
            barres = px.bar(
                top,
                x="effectif_total",
                y="nom",
                color="niveau",
                orientation="h",
                text="familles_exposees",
                custom_data=["uai"],
                color_discrete_map=theme.NIVEAUX,
                category_orders={"nom": top["nom"].tolist(), "niveau": list(theme.NIVEAUX)},
                labels={"effectif_total": "Élèves", "nom": "", "niveau": ""},
                hover_data={"commune": True, "diagnostics": True, "familles_exposees": False},
            )
            # Le collège choisi garde sa couleur pleine ; les autres sont atténués.
            for trace in barres.data:
                rang = [i for i, cd in enumerate(trace.customdata) if cd[0] == choisi]
                trace.selectedpoints = rang
                trace.selected = {"marker": {"opacity": 1}}
                trace.unselected = {"marker": {"opacity": 0.45}}
            barres.update_traces(
                textposition="outside", textfont={"color": theme.MU, "size": 12}, cliponaxis=False
            )
            barres.update_xaxes(range=[0, top["effectif_total"].max() * 1.75], title=None)
            barres.update_yaxes(tickfont={"color": theme.TX})
            theme.styliser(barres, 470)
            barres.update_layout(
                legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0},
                uniformtext={"minsize": 11, "mode": "show"},
                bargap=0.32,
            )
            st.plotly_chart(
                barres,
                key="classement",
                on_select="rerun",
                selection_mode="points",
                width="stretch",
                config={"displayModeBar": False},
            )


vue_graph = st.segmented_control(
    "Vue",
    ["Classement", "Carte"],
    default="Classement",
    key="vue_graph",
    label_visibility="collapsed",
)
if vue_graph == "Carte":
    afficher_carte()
else:
    afficher_classement()


# ---------------------------------------------------------------- fiche du collège
st.markdown(
    '<div class="section"><div class="eyebrow">02 · Fiche collège</div>'
    "<h2>Quel diagnostic demander</h2></div>",
    unsafe_allow_html=True,
)
noms = vue.set_index("uai")
st.selectbox(
    "Collège",
    options=options,
    key="college",
    format_func=lambda u: f"#{noms.at[u, 'rang']} · {noms.at[u, 'nom']} — {noms.at[u, 'commune']}",
    help="Ou cliquez un collège sur la carte ou dans le classement.",
)
c = noms.loc[choisi]
detail = facteurs(c, seuil_seveso, seuil_casias)

with st.container(key="verre_fiche"):
    evol = c["evolution_pct"]
    evol_txt = (
        "" if evol != evol else f" · <b>{evol:+.1f} %</b> d'élèves depuis 2020".replace(".", ",")
    )
    chips = "".join(
        f'<span class="chip{" on" if c[f] else ""}" style="--c:{theme.COULEURS_FAMILLES[f]}">'
        f"<i></i>{FAMILLES_COURT[f]}{'' if c[f] else ' · non'}</span>"
        for f in familles
    )
    st.markdown(
        f"""<div class="fiche-tete"><div>
  <span class="rang">#{c["rang"]} sur {k["colleges"]} · {niveau(int(c["nb_familles"]))}</span>
  <div class="nom">{escape(c["nom"])}</div>
  <div class="meta">{escape(c["commune"])} · <b>{fr(c["effectif_total"])} élèves</b>{evol_txt}
    · IPS {c["ips"]:.0f}</div></div>
  <div class="chips">{chips}</div></div>""",
        unsafe_allow_html=True,
    )
    col_pourquoi, col_diag = st.columns([1.5, 1], gap="large")
    with col_pourquoi:
        lignes = "".join(
            f'<div class="facteur{" on" if c[f] else ""}" style="--c:{theme.COULEURS_FAMILLES[f]}">'
            f'<div class="f">{FAMILLES_COURT[f].upper()}</div>'
            f'<div class="d">{escape(detail[f])}</div></div>'
            for f in familles
        )
        st.markdown(
            f'<div class="eyebrow">Pourquoi</div><div>{lignes}</div>', unsafe_allow_html=True
        )
    with col_diag:
        actifs = [f for f in familles if c[f]]
        contenu = (
            "<ul>" + "".join(f"<li>{DIAGNOSTICS[f].capitalize()}</li>" for f in actifs) + "</ul>"
            if actifs
            else '<div class="vide">Aucun diagnostic prioritaire selon ces règles.</div>'
        )
        annee = c["annee_dicrim"]
        dicrim = (
            "Pas de DICRIM communal recensé."
            if annee is None or annee != annee
            else f"DICRIM communal de {int(annee)}."
        )
        st.markdown(
            f'<div class="diag"><div class="eyebrow">Diagnostic à demander</div>{contenu}'
            f'<div class="note" style="margin-top:12px">{dicrim}</div></div>',
            unsafe_allow_html=True,
        )

    col_eff, col_cat = st.columns(2, gap="large")
    with col_eff:
        h = historique_college(historique, choisi)
        if h.empty:
            st.caption("Pas d'historique d'effectifs.")
        else:
            premier, dernier = h.iloc[0], h.iloc[-1]
            var = dernier["effectif_total"] / premier["effectif_total"] - 1
            st.markdown(
                f'<div class="titre-graph">{var:+.0%} d\'élèves entre {int(premier["rentree"])} '
                f"et {int(dernier['rentree'])}</div>"
                f'<div class="aide">{len(h)} rentrées · effectif total</div>',
                unsafe_allow_html=True,
            )
            eff = px.area(h, x="rentree", y="effectif_total", markers=True)
            eff.update_traces(
                line={"color": theme.A1, "width": 2.5, "shape": "spline"},
                fillcolor="rgba(94,234,212,.10)",
                marker={"size": 6, "color": theme.A1},
                hovertemplate="Rentrée %{x} : %{y} élèves<extra></extra>",
            )
            theme.styliser(eff, 250)
            eff.update_xaxes(title=None, dtick=1, tickformat="d")
            eff.update_yaxes(title=None, rangemode="tozero")
            st.plotly_chart(eff, width="stretch", config={"displayModeBar": False})
    with col_cat:
        cat = catnat_commune(catnat, c["code_insee"])
        if cat.empty:
            st.caption("Aucun arrêté CatNat pour cette commune.")
        else:
            total = int(cat["arretes"].sum())
            inond = int(cat.loc[cat["peril"] == "Inondation", "arretes"].sum())
            st.markdown(
                f'<div class="titre-graph">{escape(c["commune"])} : {total} arrêtés CatNat '
                f"depuis {int(cat['annee'].min())}, dont {inond} pour inondation</div>"
                '<div class="aide">le risque déjà vécu, par année de l\'événement</div>',
                unsafe_allow_html=True,
            )
            hist = px.bar(
                cat,
                x="annee",
                y="arretes",
                color="peril",
                color_discrete_map=theme.COULEURS_PERILS,
                labels={"annee": "", "arretes": "Arrêtés", "peril": ""},
            )
            theme.styliser(hist, 250)
            hist.update_layout(
                bargap=0.25, legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0}
            )
            hist.update_yaxes(title=None, dtick=1)
            st.plotly_chart(hist, width="stretch", config={"displayModeBar": False})

# ---------------------------------------------------------------- méthode et sources
with st.expander("Méthode et limites"):
    st.markdown(
        "- Un **aléa** n'est pas un risque, et un **périmètre de PPRI** n'est pas la zone "
        "inondable : le collège peut être dans le périmètre sans être inondé.\n"
        "- L'exposition est mesurée **au point du collège**, dont la précision est inconnue.\n"
        "- Un arrêté **CatNat** suppose que le maire l'ait demandé : les comptes disent la "
        "procédure autant que la catastrophe.\n"
        "- Les installations classées (ICPE) ne sont pas utilisées : tous les collèges en ont une "
        "à moins de 2,2 km, et la couche compte aussi des élevages et des éoliennes.\n"
        "- Un **ancien site industriel** (inventaire CASIAS) n'est pas une pollution prouvée : "
        "c'est une activité passée qui a pu polluer le sol. Le diagnostic le vérifie.\n"
        "- La **remontée de nappe** et les **argiles Géorisques** viennent du rapport Géorisques "
        "à l'adresse du collège. Les deux cartes des argiles ne classent pas pareil : "
        "le sélecteur « Carte des argiles » montre l'effet sur le classement."
    )
st.markdown(
    '<div class="note" style="margin-top:18px">Sources : Département du Loiret (GéoLoiret), BRGM, '
    "DDT45, Géorisques (API : CASIAS, remontée de nappe, argiles ; GASPAR), "
    "ministère de l'Éducation nationale · Licence Ouverte 2.0</div>",
    unsafe_allow_html=True,
)
