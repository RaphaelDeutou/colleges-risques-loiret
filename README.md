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
| `risques.py` | calculs, sans affichage : règles des familles, classement, indicateurs, fiche collège |
| `theme.py` | design : couleurs, polices, cartes en verre, mise en forme des graphiques |
| `.streamlit/config.toml` | thème sombre de Streamlit |
| `app.py` | affichage Streamlit : filtres, indicateurs, classement ou carte cliquables, fiche collège |
| `tests/test_risques.py` | règles des familles, classement, préparation |
| `data/` | les Parquet du cas et le Parquet préparé |
| `CADRAGE.md` | la fiche de cadrage |

## Parcours

1. En haut, trois indicateurs calculés sur la vue filtrée.
2. Le classement des collèges exposés, ou la carte : un clic sur une barre ou un point choisit un collège.
3. La fiche du collège : ses facteurs de risque avec les chiffres sources, le diagnostic à demander, ses effectifs sur 10 rentrées et les arrêtés CatNat de sa commune.

Filtres : familles de risque, collèges qui gagnent des élèves, rayon Seveso (pour tester la sensibilité du classement).

## Classement

Trois familles de risque, chacune avec une règle simple :

- **sol** : aléa argiles fort au point du collège, ou cavité, ou mouvement de terrain à moins de 500 m
- **inondation** : le collège est dans un périmètre de PPRI
- **technologique** : zone de sûreté TMD de 500 m, ou site Seveso à moins de 2 km

On classe d'abord par nombre de familles, puis par nombre d'élèves. Les rayons sont des choix du projet, pas des seuils officiels. Un aléa n'est pas un risque, et un périmètre de PPRI n'est pas la zone inondable.

## Données

Fichiers du cas 2 du cours (`awp-gabarit/data/projets`), construits à partir de :

- GéoLoiret ([catalogue](https://geoloiret.loiret-numerique.fr/apps/referentiel/catalogue_donnees.htm)) : collèges, secteurs, argiles, cavités, mouvements de terrain, PPRI, repères de crues, ICPE, TMD, centrales nucléaires
- ministère de l'Éducation nationale : effectifs et IPS
- Géorisques : arrêtés CatNat (GASPAR)

Licence Ouverte 2.0. Mentions : « Source : BRGM / DDT45 / Département du Loiret, année », « Géorisques, GASPAR », « ministère de l'Éducation nationale ».

## Assistant de code

Claude Code, utilisé pour : explorer le catalogue GéoLoiret, cadrer le projet, écrire la préparation, l'appli et le test.
