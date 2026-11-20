"""Le design de l'appli, repris du portfolio : fond nuit, cartes en verre, dégradé
turquoise → indigo → rose, Inter Tight, Instrument Serif en italique, JetBrains Mono."""

BG, TX, MU, DIM = "#05060a", "#eef1f7", "#9aa3b5", "#5d6578"
A1, A2, A3 = "#5eead4", "#818cf8", "#f0abfc"
WARN, BAD = "#fbbf24", "#fb7185"
LIGNE = "rgba(255,255,255,.08)"

# Le nombre de risques est toujours écrit en clair à côté de la couleur.
NIVEAUX = {"3 risques": BAD, "2 risques": WARN, "1 risque": A2, "aucun risque": DIM}
COULEURS_FAMILLES = {"sol": WARN, "inondation": A2, "techno": A3}
COULEURS_PERILS = {
    "Sécheresse": WARN,
    "Inondation": A2,
    "Mouvement de terrain": A3,
    "Autre": DIM,
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#05060a; --card:rgba(255,255,255,.035); --card-h:rgba(255,255,255,.06);
  --line:rgba(255,255,255,.08); --line2:rgba(255,255,255,.14);
  --tx:#eef1f7; --mu:#9aa3b5; --dim:#5d6578;
  --a1:#5eead4; --a2:#818cf8; --a3:#f0abfc; --warn:#fbbf24; --bad:#fb7185; --ok:#4ade80;
  --grad:linear-gradient(110deg,var(--a1),var(--a2) 50%,var(--a3));
  --ease:cubic-bezier(.22,1,.36,1);
  --serif:'Instrument Serif',Georgia,serif; --mono:'JetBrains Mono',ui-monospace,monospace;
}
.stApp{
  background:
    radial-gradient(ellipse 70% 45% at 10% -5%, rgba(94,234,212,.09), transparent 60%),
    radial-gradient(ellipse 55% 45% at 95% 0%, rgba(129,140,248,.12), transparent 60%),
    radial-gradient(ellipse 50% 40% at 60% 100%, rgba(240,171,252,.05), transparent 60%),
    var(--bg);
}
header[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1260px;padding-top:2.2rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid var(--line)}
[data-testid="stSidebar"] h3{font-size:13px;font-family:var(--mono);font-weight:500;
  letter-spacing:.12em;text-transform:uppercase;color:var(--mu)}

.mono{font-family:var(--mono)}
.serif{font-family:var(--serif);font-style:italic;font-weight:400;letter-spacing:-.01em}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}

/* ---------- hero ---------- */
.hero{animation:fade .9s var(--ease) both}
.pill{display:inline-flex;align-items:center;gap:10px;padding:6px 14px 6px 8px;border-radius:999px;
  border:1px solid var(--line2);background:rgba(255,255,255,.03);font-size:13px;color:var(--mu)}
.pill .tag{font-family:var(--mono);font-size:11px;padding:2px 8px;border-radius:999px;
  background:rgba(94,234,212,.12);color:var(--a1)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--a1);animation:ping 2s infinite}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(94,234,212,.55)}70%{box-shadow:0 0 0 10px rgba(94,234,212,0)}100%{box-shadow:0 0 0 0 rgba(94,234,212,0)}}
@keyframes fade{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.hero h1{font-size:clamp(34px,5.4vw,68px)!important;line-height:1.02!important;letter-spacing:-.045em;
  font-weight:600!important;margin:22px 0 16px!important;padding:0!important;color:var(--tx)}
.hero h1 .serif{font-size:1.06em}
.lead{font-size:clamp(16px,1.5vw,19px);color:var(--mu);max-width:720px;line-height:1.55}
.lead b{color:var(--tx);font-weight:500}

/* ---------- indicateurs ---------- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:30px 0 8px}
.kpi{position:relative;padding:20px 22px;border-radius:20px;border:1px solid var(--line);
  background:var(--card);backdrop-filter:blur(14px);overflow:hidden;
  transition:border-color .3s,background .3s,transform .4s var(--ease)}
.kpi:hover{border-color:var(--line2);background:var(--card-h);transform:translateY(-2px)}
.kpi::before{content:"";position:absolute;inset:0 0 auto 0;height:1px;background:var(--grad);opacity:.6}
.kpi .lab{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.kpi .val{font-size:clamp(32px,3.6vw,44px);font-weight:600;letter-spacing:-.04em;line-height:1.1;margin-top:8px}
.kpi .sur{color:var(--dim)}
.kpi .sub{font-size:13px;color:var(--mu);margin-top:4px}

/* ---------- cartes en verre (conteneurs Streamlit à clé) ---------- */
[class*="st-key-verre"]{background:linear-gradient(180deg,rgba(17,20,32,.72),rgba(8,10,16,.72));
  border:1px solid var(--line)!important;border-radius:22px!important;padding:22px 22px 10px!important;
  backdrop-filter:blur(18px);box-shadow:0 30px 90px -40px rgba(129,140,248,.35),inset 0 1px 0 rgba(255,255,255,.05)}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--a1);margin-bottom:6px}
.titre-graph{font-size:20px;font-weight:600;letter-spacing:-.02em;line-height:1.25;color:var(--tx);margin:0 0 4px}
.aide{font-family:var(--mono);font-size:11.5px;color:var(--dim);margin:2px 0 4px}
.section{margin:44px 0 14px}
.section h2{font-size:clamp(26px,3vw,38px)!important;letter-spacing:-.035em;font-weight:600!important;padding:0!important;margin:6px 0 0!important}

/* ---------- fiche collège ---------- */
.fiche-tete{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:14px}
.rang{display:inline-block;font-family:var(--mono);font-size:12px;padding:4px 10px;border-radius:999px;
  border:1px solid var(--line2);color:var(--mu)}
.nom{font-family:var(--serif);font-style:italic;font-size:clamp(34px,4.4vw,54px);line-height:1;letter-spacing:-.02em;margin:10px 0 6px}
.meta{color:var(--mu);font-size:15px}
.meta b{color:var(--tx);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:8px;padding:7px 13px;border-radius:999px;font-size:13px;
  border:1px solid var(--line);color:var(--dim);background:rgba(255,255,255,.02)}
.chip i{width:8px;height:8px;border-radius:50%;background:var(--dim)}
.chip.on{color:var(--tx);border-color:var(--c);background:color-mix(in srgb,var(--c) 14%,transparent)}
.chip.on i{background:var(--c);box-shadow:0 0 12px var(--c)}
.facteur{display:grid;grid-template-columns:118px 1fr;gap:14px;padding:13px 0;border-top:1px solid var(--line)}
.facteur:first-child{border-top:0}
.facteur .f{font-family:var(--mono);font-size:12px;color:var(--dim);padding-top:2px}
.facteur.on .f{color:var(--c)}
.facteur .d{color:var(--mu);font-size:14.5px;line-height:1.5}
.facteur.on .d{color:var(--tx)}
.diag{position:relative;border-radius:18px;padding:20px 22px;background:rgba(8,10,16,.8)}
.diag::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:var(--grad);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
.diag ul{margin:10px 0 0 0;padding-left:18px}
.diag li{margin:6px 0;color:var(--tx);font-size:15px}
.diag li::marker{color:var(--a1)}
.diag .vide{color:var(--mu);font-size:14.5px;margin-top:8px}
.note{font-size:13px;color:var(--dim);line-height:1.5}
@media (max-width:640px){.facteur{grid-template-columns:1fr;gap:4px}}
</style>
"""


def styliser(fig, hauteur: int):
    """Mise en forme Plotly commune : fond transparent, grille discrète, police du thème."""
    fig.update_layout(
        template="plotly_dark",
        height=hauteur,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter Tight, system-ui, sans-serif", "size": 13, "color": MU},
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        hoverlabel={
            "bgcolor": "#0f121c",
            "bordercolor": "rgba(255,255,255,.14)",
            "font": {"family": "Inter Tight, sans-serif", "color": TX, "size": 13},
        },
        legend={"bgcolor": "rgba(0,0,0,0)", "title": None, "font": {"color": MU}},
    )
    fig.update_xaxes(gridcolor=LIGNE, zeroline=False, linecolor=LIGNE)
    fig.update_yaxes(gridcolor=LIGNE, zeroline=False, linecolor=LIGNE)
    return fig


# L'attribution OpenStreetMap / CARTO reste visible (licence), mais discrète sur fond sombre.
CSS += """<style>
.maplibregl-ctrl-attrib{background:rgba(5,6,10,.7)!important;color:#5d6578!important;font-size:10px!important}
.maplibregl-ctrl-attrib a{color:#9aa3b5!important}
.maplibregl-ctrl-attrib-button{filter:invert(1);opacity:.5}
</style>"""
