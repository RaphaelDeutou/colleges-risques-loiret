# Collèges et risques dans le Loiret

**Décision** : choisir les collèges publics à inscrire en premier au programme de diagnostics, et le diagnostic à commander pour chacun (sol, inondation ou industriel).

**Utilisateurs** : la direction du Département chargée des collèges, et les élus qui votent les crédits de travaux.

**Appli en ligne** : https://colleges-risques-loiret.streamlit.app/

## Lancer en local

```bash
uv sync
uv run python preparer.py        # une fois : écrit data/colleges_priorite.parquet
uv run streamlit run app.py
```

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
| `georisques.py` | appel à l'API Géorisques (anciens sites industriels, remontée de nappe, argiles), mis en cache dans `data/georisques_colleges.parquet` |
| `risques.py` | calculs, sans affichage : règles des familles, classement, indicateurs, fiche collège |
| `theme.py` | design : couleurs, polices, cartes en verre, mise en forme des graphiques |
| `.streamlit/config.toml` | thème sombre de Streamlit |
| `app.py` | affichage Streamlit : filtres, indicateurs, classement ou carte cliquables, fiche collège |
| `tests/test_risques.py` | règles des familles, seuils, classement, préparation |
| `tests/test_prevision.py` | construction des exemples et prévisions du modèle |
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
