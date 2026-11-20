# Collèges et risques · réponses aux questions du cours

Tous les chiffres portent sur les **58 collèges publics** du Loiret (rentrée 2025), avec les règles de l'appli (voir § 4). Ils sont recalculables avec `risques.py`.

## 1. Le problème à résoudre

Le Département du Loiret possède les collèges publics. Il les construit, les agrandit et paie leurs grosses réparations (code de l'éducation, L213-2). Or le territoire a des risques : argiles qui gonflent et se rétractent sous les bâtiments, cavités souterraines, crues de la Loire, sites industriels, transport de matières dangereuses.

Le budget de prévention est limité : on ne peut pas tout diagnostiquer en même temps.

**Décision à éclairer** : *quels collèges publics inscrire en premier au programme de diagnostics, et quel diagnostic demander pour chacun* (sol, inondation ou industriel).

**Utilisateurs** : la direction du Département chargée des bâtiments et des collèges, qui prépare le programme de travaux, et les élus, qui votent les crédits.

## 2. De quoi parle le jeu de données

Six fichiers préparés par le formateur à partir du catalogue **GéoLoiret** (182 jeux), de l'**Éducation nationale** et de **Géorisques**. Licence Ouverte 2.0.

| Fichier | Une ligne = | Ce qu'il contient |
|---|---|---|
| `colleges_risques.parquet` | un collège (70, dont 58 publics) | élèves, IPS, et l'exposition **au point du collège** : aléa argiles, PPRI, cavités et mouvements de terrain à moins de 500 m, distance aux ICPE, aux sites Seveso, aux axes TMD, aux centrales, aux repères de crues ; arrêtés CatNat de la commune ; DICRIM |
| `colleges.parquet` | un collège × une rentrée (2016-2025) | effectifs par niveau, IPS, brevet |
| `risques_communes.parquet` | une commune (325) | exposition de la commune et arrêtés CatNat par péril |
| `risques_catnat.parquet` | un arrêté × une commune × un péril (2 065) | arrêtés de catastrophe naturelle de 1983 à 2025 |
| `*.geojson` | un secteur ou une commune | contours pour les cartes |

**Vocabulaire à maîtriser pour la soutenance :**
- **Aléa** : le phénomène possible (argile qui gonfle). Le **risque**, c'est l'aléa croisé avec ce qui est exposé (un collège, des élèves).
- **PPRI** : plan de prévention du risque inondation. Un *périmètre* de PPRI n'est pas la zone inondable.
- **ICPE** : installation classée pour l'environnement. **Seveso** : site industriel dangereux, classé selon la directive Seveso.
- **TMD** : transport de matières dangereuses (routes, autoroutes, voies ferrées).
- **CatNat** : arrêté de catastrophe naturelle. C'est le risque *vécu*, mais il suppose que le maire en ait fait la demande.
- **DICRIM** : document d'information communal sur les risques majeurs.
- **IPS** : indice de position sociale des élèves (100 = moyenne nationale).

## 3. Technologies utilisées

| Couche | Outil | Pourquoi |
|---|---|---|
| Langage | Python 3.12 | imposé par le cours |
| Environnement | **uv** (`pyproject.toml`, `uv.lock`) | installation reproductible, la même en local et en ligne |
| Données | **pandas** + **Parquet** (pyarrow) | Parquet est léger (moins de 1 Mo ici) et garde les types ; la préparation tourne une fois dans `preparer.py` |
| Appli web | **Streamlit** | une seule page en Python, déploiement gratuit, clic sur un graphique avec `on_select` pour le drill-down |
| Graphiques | **Plotly Express** | carte interactive (fond CARTO sombre), barres cliquables, survols |
| Design | CSS dans `theme.py` + `.streamlit/config.toml` | thème sombre repris de mon portfolio |
| Qualité | **ruff** (style), **pytest** (6 tests) | grille : « ruff propre, un test » |
| Hébergement | **GitHub** + **Streamlit Community Cloud** | chaque `git push` redéploie l'appli |
| Assistant | Claude Code | exploration du catalogue, cadrage, code (dit dans le README) |

**Pourquoi Streamlit plutôt que Dash, en deux phrases :** Streamlit relance le script à chaque interaction, ce qui suffit pour 58 collèges et garde le code court et lisible pour tout le groupe. Son clic sur graphique (`on_select`) donne le drill-down sans écrire de callbacks.

**Séparation calculs / affichage** (grille, qualité du code) : `risques.py` calcule, `theme.py` habille, `app.py` affiche, `preparer.py` prépare.

## 4. Nos règles de classement

| Famille | Règle | Collèges publics | Diagnostic |
|---|---|---|---|
| Sol | argiles **fortes** au point, ou cavité, ou mouvement de terrain à moins de 500 m | 28 | étude géotechnique |
| Inondation | dans un périmètre de PPRI | 6 | diagnostic de vulnérabilité inondation |
| Technologique | zone TMD de 500 m, ou site Seveso à moins de 2 km | 27 | revue du plan de mise en sûreté (confinement) |

Classement : **le plus de familles d'abord, puis le plus d'élèves**. On compte des familles, on n'additionne pas des risques différents : c'est plus facile à justifier.

**Ce qu'on a écarté, et pourquoi :**
- **les ICPE** : tous les collèges en ont une à moins de 2,2 km, et la couche compte aussi des élevages et des éoliennes ;
- **les argiles moyennes** : elles touchent 42 collèges sur 58, donc elles ne départagent pas ;
- **les centrales nucléaires** : la plus proche est à 7 km au minimum, et le plan d'urgence nucléaire relève de la préfecture, pas du bâtiment.

## 5. Questions métier (page du cas)

**1. Quels collèges publics examiner en priorité, et sur quel risque ?**
Deux collèges cumulent les trois familles : **Clos Ferbois (Jargeau, 631 élèves)** et **Jacques Prévert (Saint-Jean-le-Blanc, 469)**. Suivent 14 collèges à 2 risques, presque tous « sol + technologique » : Pierre de Coubertin (Saint-Jean-de-Braye, 808 élèves), Pierre Mendès France (Chécy), Montjoie (Saran)…

**2. Combien d'élèves sont exposés ?**
- **8 941 élèves** dans les 16 collèges à 2 risques ou plus ;
- **23 561 élèves** dans les 43 collèges exposés à au moins 1 risque, sur 31 463 ;
- **3 004 élèves** dans les 6 collèges situés dans un périmètre de PPRI.

**3. Les collèges qui grandissent sont-ils exposés ?**
Oui. 26 collèges ont gagné des élèves entre 2020 et 2025, dont **8 qui cumulent 2 risques**. Les plus marqués : **Montjoie (Saran, +24 %)**, **Nelson Mandela (Saint-Ay, +23 %)** et **André Malraux (Saint-Jean-de-la-Ruelle, +19 %)**. Ce sont des priorités fortes, car un agrandissement dans une zone exposée doit intégrer le risque dès la conception. Dans l'appli : le filtre « Seulement les collèges qui gagnent des élèves ».

**4. Quel diagnostic pour quel collège ?**
Une famille correspond à un diagnostic (tableau du § 4). La fiche de chaque collège affiche le ou les diagnostics à demander. Par exemple, pour Clos Ferbois : étude géotechnique, diagnostic de vulnérabilité inondation et revue du plan de mise en sûreté.

**5. Comment montrer à un élu la différence entre risque exposé et risque vécu ?**
La fiche met les deux côte à côte : à gauche, « Pourquoi » (aléas et distances, le risque *exposé*) ; en bas, les arrêtés CatNat de la commune par année (le risque *vécu*). Exemple : Jargeau est dans le PPRI de la Loire mais n'a que 2 arrêtés « inondation » depuis 1989. Un risque peut être réel sans avoir encore coûté.

**6. Les collèges les plus exposés accueillent-ils des publics plus fragiles ?**
Non, pas dans ces données. L'IPS moyen est de 94,9 pour les collèges sans risque, de 97,9 pour ceux à 1 risque, de 97,6 pour ceux à 2 risques et de 112,2 pour les 2 collèges à 3 risques. La corrélation est faible (+0,18). Les collèges exposés sont plutôt dans l'agglomération d'Orléans, socialement moyenne à favorisée.

## 6. Questions ouvertes sur les données (page du cas)

**1. Quels collèges cumulent le plus ? Comment justifier la règle ?**
Voir la question métier 1. La justification : chaque famille correspond à **un diagnostic différent** commandé à un prestataire différent. Compter les familles revient donc à compter les diagnostics à lancer, et à départager à égalité par le nombre d'élèves protégés.

**2. Élèves en PPRI, et leur commune a-t-elle beaucoup d'arrêtés inondation ?**
6 collèges, 3 004 élèves. Leurs communes comptent 2 à 5 arrêtés « inondation » : Sully-sur-Loire et Olivet en ont 5, Orléans 4, Saint-Jean-le-Blanc 3, Jargeau et Saint-Denis-en-Val 2. La médiane des 58 collèges est de 3. Un collège en PPRI n'est donc pas forcément dans une commune souvent sinistrée : le PPRI anticipe une crue majeure de la Loire, plus forte que celles qu'enregistrent les arrêtés depuis 1983.

**3. Le classement change-t-il si l'on change les rayons ?**
Oui, il faut le dire :
- **Seveso à 1 km** au lieu de 2 : 13 collèges cumulent 2 risques au lieu de 16, et 9 des 10 premiers restent dans le top 10 ;
- **Seveso à 5 km** : 22 collèges cumulent, et 7 des 10 premiers restent dans le top 10 ;
- **Sol réduit aux argiles fortes**, sans les cavités ni les mouvements de terrain : seulement 7 collèges cumulent, et 7 des 10 premiers restent.

Le **haut du classement est stable**, le bas bouge. Dans l'appli, le curseur « rayon Seveso » le montre en direct. Le rayon des cavités (500 m) ne se règle pas dans l'appli : il faudrait relancer le script du formateur avec les couches brutes.

**4. L'exposition est-elle liée à l'IPS ?**
Lien faible : corrélation de +0,18 (voir la question métier 6). On ne peut pas dire que les publics fragiles sont plus exposés.

**5. Quels collèges sont proches d'un axe TMD ou d'un site Seveso, et lesquels cumulent avec un risque naturel ?**
27 collèges ont la famille technologique : 21 sont dans une zone TMD de 500 m et 9 ont un site Seveso à moins de 2 km. **15 d'entre eux cumulent avec un risque naturel** (sol ou inondation), soit 8 444 élèves.

**6. Quels collèges exposés sont dans une commune sans DICRIM ?**
Neuf collèges. Le plus important : **Montjoie (Saran, sol + technologique, 642 élèves)**, qui gagne aussi 24 % d'élèves. Les autres :
- Montabuzard (Ingré, 867 élèves) ;
- Léon Delagrange (Neuville-aux-Bois) ;
- Aristide Bruant (Courtenay) ;
- Gutenberg (Malesherbes) ;
- Mary Jackson (Dadonville) ;
- Charles Desvergnes (Bellegarde) ;
- Alfred de Musset (Patay) ;
- Louis Joseph Soulas (Bazoches-les-Gallerandes).

C'est un levier peu coûteux : demander à ces mairies de publier leur DICRIM.

## 7. Limites à dire avant qu'on vous les demande

- L'exposition est mesurée **en un point** (l'adresse géocodée du collège), pas sur l'emprise du bâtiment.
- « Non cartographié » pour les argiles peut vouloir dire une couche incomplète.
- Les rayons de 500 m et 2 km sont **nos choix**, pas des seuils officiels.
- Un arrêté CatNat mesure aussi la **démarche du maire**, pas seulement la catastrophe.
- Les **12 collèges privés** sont exclus : ils n'appartiennent pas au Département.
