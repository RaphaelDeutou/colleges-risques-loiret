# Collèges et risques dans le Loiret

**Décision** : choisir les collèges publics à inscrire en premier au programme de diagnostics, et le diagnostic à commander pour chacun (sol, inondation ou industriel).

**Utilisateurs** : la direction du Département chargée des collèges, et les élus qui votent les crédits de travaux.

**Appli en ligne** : https://colleges-risques-loiret.streamlit.app/

**API (FastAPI)** : _à compléter après le déploiement sur Render_ · documentation sur `/docs`

## Architecture

```
Appli Streamlit ── chatbot ──► LLM Groq (choisit un outil)
       │                 │
       │                 └─► client MCP ──► mcp_server.py (5 outils) ──► API FastAPI (api.py)
       │                                                                      │
       └──────────── risques.py (calculs communs) ◄──────────────────────────┘
                              │
                        data/*.parquet
```

L'appli, l'API et donc le chatbot utilisent les mêmes calculs (`risques.py`) : ils donnent les mêmes chiffres. Le chatbot lance lui-même le serveur MCP (en stdio) ; le serveur MCP appelle l'API par HTTP.

## Lancer en local

```bash
uv sync
uv run python preparer.py        # une fois : écrit les Parquet préparés dans data/
uv run uvicorn api:app --host 127.0.0.1 --port 8000      # terminal 1 : l'API
uv run streamlit run app.py                               # terminal 2 : l'appli
```

Pour l'assistant, copiez `.streamlit/secrets.toml.example` en `.streamlit/secrets.toml` (ignoré par git) et collez votre clé Groq (https://console.groq.com/keys). Sans clé, l'appli fonctionne et l'assistant explique comment le configurer.

Tester le serveur MCP seul : `npx @modelcontextprotocol/inspector uv run python mcp_server.py` (l'API doit tourner).

Tests et qualité :

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Organisation

| Fichier | Rôle |
|---|---|
| `preparer.py` | préparation hors de l'appli : 58 collèges publics, familles de risque, évolution des effectifs, historique et arrêtés CatNat des communes |
| `prevision.py` | couche ML : prévision des effectifs à 1-5 ans (régression Ridge) et son backtest |
| `api.py` | API FastAPI : `/indicateurs`, `/colleges`, `/colleges/recherche`, `/colleges/{uai}`, `/communes/{commune}/catnat` ; paramètres validés (422) |
| `mcp_server.py` | serveur MCP (FastMCP) : 5 outils pour le LLM, qui appellent l'API |
| `chatbot.py` | le chatbot : lance le serveur MCP, passe ses outils au LLM, exécute les appels |
| `render.yaml`, `requirements-api.txt` | déploiement de l'API seule sur Render |
| `georisques.py` | appel à l'API Géorisques (anciens sites industriels, remontée de nappe, argiles), mis en cache dans `data/georisques_colleges.parquet` |
| `risques.py` | calculs, sans affichage : règles des familles, classement, indicateurs, fiche collège |
| `theme.py` | design : couleurs, polices, cartes en verre, mise en forme des graphiques |
| `.streamlit/config.toml` | thème sombre de Streamlit |
| `app.py` | affichage Streamlit : filtres, indicateurs, classement ou carte cliquables, fiche collège |
| `tests/test_risques.py` | règles des familles, seuils, classement, préparation |
| `tests/test_prevision.py` | construction des exemples et prévisions du modèle |
| `tests/test_chatbot.py` | chaîne chatbot → MCP → API avec un faux LLM, validation de l'API |
| `tests/test_app.py` | l'appli s'ouvre, et la fiche de chacun des 58 collèges aussi |
| `REPONSES.md` | réponses aux questions du cas, chiffres à l'appui |
| `data/` | les Parquet du cas et le Parquet préparé |
| `CADRAGE.md` | la fiche de cadrage |

## Parcours

1. En haut, trois indicateurs calculés sur la vue filtrée.
2. Le classement des collèges exposés, ou la carte : un clic sur une barre ou un point choisit un collège.
3. La fiche du collège : ses facteurs de risque avec les chiffres sources, le diagnostic à demander, ses effectifs sur 10 rentrées et les arrêtés CatNat de sa commune.

Filtres : familles de risque, communes (la carte zoome sur les communes choisies), collèges qui gagnent des élèves, rayon Seveso (pour tester la sensibilité du classement).

## Classement

Quatre familles de risque, chacune avec une règle simple :

- **sol** : argiles fortes selon la carte choisie (GéoLoiret ou Géorisques), ou cavité, ou mouvement de terrain à moins de 500 m
- **inondation** : le collège est dans un périmètre de PPRI, ou en remontée de nappe « risque existant »
- **technologique** : zone de sûreté TMD de 500 m, ou site Seveso à moins de 2 km
- **sols pollués** : au moins 5 anciens sites industriels (CASIAS) à moins de 500 m, le quart des collèges les plus entourés

On classe d'abord par nombre de familles, puis par nombre d'élèves. Les rayons et seuils sont des choix du projet, pas des seuils officiels : la partie « Sensibilité » de l'appli permet de les changer. Un aléa n'est pas un risque, un périmètre de PPRI n'est pas la zone inondable, et un ancien site industriel n'est pas une pollution prouvée.

## Assistant : LLM, MCP et FastAPI

Le chatbot (section « 03 · Assistant ») envoie la question à un LLM **Groq** avec la liste des outils du serveur MCP. Le LLM choisit un outil d'après son nom et sa description ; le chatbot l'exécute via MCP, l'outil appelle l'API, et le résultat repart au LLM, qui rédige la réponse. Les outils appelés sont affichés sous chaque réponse.

| Outil MCP | Route de l'API | Sert à |
|---|---|---|
| `indicateurs_risques` | `GET /indicateurs` | chiffres clés, par commune ou pour tout le département |
| `classement_colleges` | `GET /colleges` | les collèges à diagnostiquer en priorité |
| `chercher_college` | `GET /colleges/recherche` | retrouver l'identifiant d'un collège à partir de son nom |
| `fiche_college` | `GET /colleges/{uai}` | risques expliqués, diagnostics, effectifs, prévision, CatNat |
| `arretes_catnat` | `GET /communes/{commune}/catnat` | les catastrophes naturelles déjà reconnues dans une commune |

Seules des données publiques et agrégées partent vers Groq. La clé reste dans les secrets, jamais dans git.

### Déployer

1. **API sur Render** : New → Blueprint → ce dépôt (`render.yaml`). Notez l'URL du service, par exemple `https://colleges-risques-api.onrender.com`, et vérifiez `/sante` et `/docs`.
2. **Secrets sur Streamlit Cloud** : Manage app → Settings → Secrets, collez le contenu de `.streamlit/secrets.toml.example` avec votre clé Groq et `API_URL` = l'URL Render.

L'offre gratuite de Render endort l'API après 15 minutes sans appel : la première question met environ une minute.

## Couche ML : prévision des effectifs

Des travaux votés aujourd'hui sont livrés dans 2 ou 3 ans : ce qui compte, ce sont les élèves qui seront dans le collège exposé. `prevision.py` entraîne **une régression Ridge par horizon** (1 à 5 ans). Elle prédit la variation de l'effectif à partir des parts de 6e, 5e et 4e, de l'IPS et de la taille du collège.

**Évaluation** : on cache la rentrée 2025, on la prédit avec un modèle entraîné sur les années d'avant, et on compare à la méthode naïve « l'effectif ne bouge pas ».

| Horizon | Erreur du modèle (élèves) | Erreur « ne bouge pas » | Exemples d'entraînement |
|---|---|---|---|
| 1 an | 14,5 | 15,8 | 286 |
| 2 ans | 21,1 | 21,6 | 228 |
| 3 ans | 26,5 | 27,4 | 170 |
| 4 ans | 34,3 | 32,4 | 112 |
| 5 ans | 43,8 | 41,9 | 56 |

Le modèle fait un peu mieux jusqu'à 3 ans. Au-delà, il n'a que 1 ou 2 années d'exemples et ne fait pas mieux : l'appli l'affiche dans la fiche collège. Dans l'appli, le curseur « Effectifs prévus dans » choisit l'horizon, et « Départager les collèges avec les élèves prévus » classe avec la prévision.

## Données

Fichiers du cas 2 du cours (`awp-gabarit/data/projets`), construits à partir de :

- GéoLoiret ([catalogue](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm)) : collèges, secteurs, argiles, cavités, mouvements de terrain, PPRI, repères de crues, ICPE, TMD, centrales nucléaires
- ministère de l'Éducation nationale : effectifs et IPS
- Géorisques : arrêtés CatNat (GASPAR)
- API Géorisques, interrogée par `georisques.py` : anciens sites industriels (CASIAS), remontée de nappe et argiles à l'adresse de chaque collège. Pour mettre à jour le cache : `uv run python preparer.py --rafraichir`

Licence Ouverte 2.0. Mentions : « Source : BRGM / DDT45 / Département du Loiret, année », « Géorisques, GASPAR », « ministère de l'Éducation nationale ».

## Assistant de code

Claude Code, utilisé pour : explorer le catalogue GéoLoiret, cadrer le projet, écrire la préparation, l'appli et le test.
