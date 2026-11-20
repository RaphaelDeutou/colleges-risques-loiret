# Collèges et risques · réponses aux questions du cours

Tous les chiffres portent sur les **58 collèges publics** du Loiret (rentrée 2025), avec les réglages par défaut de l'appli : carte des argiles GéoLoiret, rayon Seveso de 2 km, au moins 5 anciens sites industriels (voir § 4). Ils sont recalculables avec `risques.py`.

## 1. Le problème à résoudre

Le Département du Loiret possède les collèges publics. Il les construit, les agrandit et paie leurs grosses réparations (code de l'éducation, L213-2). Or le territoire a des risques : argiles qui gonflent et se rétractent sous les bâtiments, cavités souterraines, crues de la Loire, remontées de nappe, sites industriels, transport de matières dangereuses, sols pollués par d'anciennes activités.

Le budget de prévention est limité : on ne peut pas tout diagnostiquer en même temps.

**Décision à éclairer** : *quels collèges publics inscrire en premier au programme de diagnostics, et quel diagnostic demander pour chacun* (sol, inondation, technologique, sols pollués).

**Utilisateurs** : la direction du Département chargée des bâtiments et des collèges, qui prépare le programme de travaux, et les élus, qui votent les crédits.

## 2. De quoi parle le jeu de données

**Six fichiers préparés par le formateur** à partir du catalogue **GéoLoiret** (182 jeux), de l'**Éducation nationale** et de **Géorisques**. Licence Ouverte 2.0.

| Fichier | Une ligne = | Ce qu'il contient |
|---|---|---|
| `colleges_risques.parquet` | un collège (70, dont 58 publics) | élèves, IPS, et l'exposition **au point du collège** : aléa argiles, PPRI, cavités et mouvements de terrain à moins de 500 m, distance aux ICPE, aux sites Seveso, aux axes TMD, aux centrales, aux repères de crues ; arrêtés CatNat de la commune ; DICRIM |
| `colleges.parquet` | un collège × une rentrée (2016-2025) | effectifs par niveau, IPS, brevet |
| `risques_communes.parquet` | une commune (325) | exposition de la commune et arrêtés CatNat par péril |
| `risques_catnat.parquet` | un arrêté × une commune × un péril (2 065) | arrêtés de catastrophe naturelle de 1983 à 2025 |
| `*.geojson` | un secteur ou une commune | contours pour les cartes |

**Un enrichissement que nous avons ajouté nous-mêmes**, avec l'**API publique de Géorisques** (Licence Ouverte), interrogée une fois pour chaque collège par `georisques.py` :

| Donnée | Ce que c'est | Pourquoi elle est utile |
|---|---|---|
| `nb_casias_500m`, `casias_proches` | anciens sites industriels et de service (inventaire **CASIAS**) à moins de 500 m, et les trois plus proches | de 0 à 47 selon le collège : départage bien |
| `nappe_georisques` | risque de **remontée de nappe** à l'adresse du collège | 20 collèges en « risque existant » |
| `argiles_georisques` | argiles selon la **carte nationale** servie par Géorisques | ne classe pas comme GéoLoiret : sert à tester la sensibilité |

Nous avons aussi regardé ce qui ne départage pas, et l'avons écarté : le **radon** (classe 1 pour les 58 collèges) et la **pollution des sols en oui ou non** (oui partout).

**Vocabulaire à maîtriser pour la soutenance :**
- **Aléa** : le phénomène possible (argile qui gonfle). Le **risque**, c'est l'aléa croisé avec ce qui est exposé (un collège, des élèves).
- **PPRI** : plan de prévention du risque inondation. Un *périmètre* de PPRI n'est pas la zone inondable.
- **Remontée de nappe** : l'eau souterraine qui monte et inonde les sous-sols, sans débordement de rivière.
- **ICPE** : installation classée pour l'environnement. **Seveso** : site industriel dangereux, classé selon la directive Seveso.
- **CASIAS** : carte des anciens sites industriels et activités de service (garages, usines à gaz, teintureries). Un site CASIAS n'est pas une pollution prouvée, mais une activité qui a pu polluer.
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
| Enrichissement | **API Géorisques** (`georisques.py`, bibliothèque standard `urllib`) | appelée une seule fois, résultat mis en cache dans `data/georisques_colleges.parquet` : l'appli ne dépend pas d'internet |
| Machine learning | **scikit-learn** (`prevision.py`) | régression Ridge, une par horizon de 1 à 5 ans, évaluée contre une méthode naïve |
| Appli web | **Streamlit** | une seule page en Python, déploiement gratuit, clic sur un graphique avec `on_select` pour le drill-down |
| Graphiques | **Plotly Express** | carte interactive (fond CARTO sombre), barres cliquables, survols |
| Design | CSS dans `theme.py` + `.streamlit/config.toml` | thème sombre repris de mon portfolio |
| Qualité | **ruff** (style), **pytest** (12 tests) | grille : « ruff propre, un test » |
| Hébergement | **GitHub** + **Streamlit Community Cloud** | chaque `git push` redéploie l'appli |
| Assistant | Claude Code | exploration du catalogue, cadrage, code (dit dans le README) |

**Pourquoi Streamlit plutôt que Dash, en deux phrases :** Streamlit relance le script à chaque interaction, ce qui suffit pour 58 collèges et garde le code court et lisible pour tout le groupe. Son clic sur graphique (`on_select`) donne le drill-down sans écrire de callbacks.

**Séparation calculs / affichage** (grille, qualité du code) : `risques.py` calcule, `theme.py` habille, `app.py` affiche, `preparer.py`, `georisques.py` et `prevision.py` préparent.

## 4. Nos règles de classement

| Famille | Règle | Collèges publics | Diagnostic |
|---|---|---|---|
| Sol | argiles **fortes** selon la carte choisie, ou cavité, ou mouvement de terrain à moins de 500 m | 28 | étude géotechnique |
| Inondation | dans un périmètre de PPRI, ou remontée de nappe « risque existant » | 20 (6 PPRI + 14 nappe seule) | diagnostic de vulnérabilité inondation |
| Technologique | zone TMD de 500 m, ou site Seveso à moins de 2 km | 27 | revue du plan de mise en sûreté (confinement) |
| Sols pollués | au moins **5** anciens sites industriels à moins de 500 m | 16 | diagnostic de la qualité des sols et de l'air intérieur |

Classement : **le plus de familles d'abord, puis le plus d'élèves**. On compte des familles, on n'additionne pas des risques différents : c'est plus facile à justifier.

**Pourquoi 5 sites CASIAS ?** C'est le seuil du quart des collèges les plus entourés (3ᵉ quartile). Avec 1 seul site, 40 collèges sur 58 seraient comptés, et la famille ne départagerait plus.

**Ce qu'on a écarté, et pourquoi :**
- **les ICPE** : tous les collèges en ont une à moins de 2,2 km, et la couche compte aussi des élevages et des éoliennes ;
- **les argiles moyennes** : elles touchent 42 collèges sur 58, donc elles ne départagent pas ;
- **les centrales nucléaires** : la plus proche est à 7 km au minimum, et le plan d'urgence nucléaire relève de la préfecture, pas du bâtiment ;
- **le radon** : classe 1 pour les 58 collèges.

## 5. Questions métier (page du cas)

**1. Quels collèges publics examiner en priorité, et sur quel risque ?**
Aucun collège ne cumule les 4 familles. **Neuf collèges en cumulent 3** :

| Rang | Collège | Élèves | Familles |
|---|---|---|---|
| 1 | Pierre de Coubertin (Saint-Jean-de-Braye) | 808 | sol + technologique + sols pollués |
| 2 | Montjoie (Saran) | 642 | sol + technologique + sols pollués |
| 3 | Robert Goupil (Beaugency) | 640 | sol + technologique + sols pollués |
| 4 | Clos Ferbois (Jargeau) | 631 | sol + inondation + technologique |
| 5 | Alice et Jean Pelletier (Orléans) | 533 | sol + inondation + sols pollués |
| 6 | Charles Desvergnes (Bellegarde) | 476 | sol + inondation + sols pollués |
| 7 | Jacques Prévert (Saint-Jean-le-Blanc) | 469 | sol + inondation + technologique |
| 8 | Le Grand Clos (Montargis) | 452 | inondation + technologique + sols pollués |
| 9 | André Malraux (Saint-Jean-de-la-Ruelle) | 444 | sol + technologique + sols pollués |

**2. Combien d'élèves sont exposés ?**
- **18 019 élèves** dans les 33 collèges à 2 risques ou plus, soit 57 % des élèves du public ;
- **26 812 élèves** dans les 49 collèges exposés à au moins 1 risque, sur 31 463 ;
- 10 740 élèves dans les 20 collèges de la famille inondation, dont 3 004 dans les 6 collèges en périmètre de PPRI ;
- 8 588 élèves dans les 16 collèges entourés d'anciens sites industriels.

Avec 4 familles, « 2 risques ou plus » concerne plus de la moitié des collèges. Pour une liste courte à financer en premier, regardez les **9 collèges à 3 risques**.

**3. Les collèges qui grandissent sont-ils exposés ?**
Oui. 26 collèges ont gagné des élèves entre 2020 et 2025, dont **14 qui cumulent au moins 2 risques**. Les plus marqués :
- **Montjoie** (Saran) : +24 %, 3 risques ;
- **Nelson Mandela** (Saint-Ay) : +23 % ;
- **André Malraux** (Saint-Jean-de-la-Ruelle) : +19 %, 3 risques ;
- **Montesquieu** (Orléans) : +18 % ;
- **Le Grand Clos** (Montargis) : +17 %, 3 risques.

Ce sont des priorités fortes, car un agrandissement dans une zone exposée doit intégrer le risque dès la conception. Dans l'appli : le filtre « Seulement les collèges qui gagnent des élèves ».

**4. Quel diagnostic pour quel collège ?**
Une famille correspond à un diagnostic (tableau du § 4). La fiche de chaque collège affiche le ou les diagnostics à demander. Par exemple, pour Pierre de Coubertin : étude géotechnique, revue du plan de mise en sûreté, et diagnostic de la qualité des sols et de l'air intérieur. Il a 6 anciens sites industriels à moins de 500 m, dont une tôlerie à 91 m.

**5. Comment montrer à un élu la différence entre risque exposé et risque vécu ?**
La fiche met les deux côte à côte : en haut, « Pourquoi » (aléas, distances, anciens sites : le risque *exposé*) ; en bas, les arrêtés CatNat de la commune par année (le risque *vécu*). Exemple : Jargeau est dans le PPRI de la Loire mais n'a que 2 arrêtés « inondation » depuis 1989. Un risque peut être réel sans avoir encore coûté.

**6. Les collèges les plus exposés accueillent-ils des publics plus fragiles ?**
Non, pas dans ces données. L'IPS moyen est de 93,1 sans risque, 98,2 avec 1 risque, 99,1 avec 2 risques et 96,4 avec 3 risques. La corrélation est quasi nulle (+0,09). Les collèges exposés sont surtout dans l'agglomération d'Orléans et à Montargis, socialement variées.

## 6. Questions ouvertes sur les données (page du cas)

**1. Quels collèges cumulent le plus ? Comment justifier la règle ?**
Voir la question métier 1. La justification : chaque famille correspond à **un diagnostic différent**, commandé à un prestataire différent. Compter les familles revient donc à compter les diagnostics à lancer, et à départager à égalité par le nombre d'élèves protégés.

**2. Élèves en PPRI, et leur commune a-t-elle beaucoup d'arrêtés inondation ?**
6 collèges, 3 004 élèves. Leurs communes comptent 2 à 5 arrêtés « inondation » : Sully-sur-Loire et Olivet en ont 5, Orléans 4, Saint-Jean-le-Blanc 3, Jargeau et Saint-Denis-en-Val 2. La médiane des 58 collèges est de 3. Un collège en PPRI n'est donc pas forcément dans une commune souvent sinistrée : le PPRI anticipe une crue majeure de la Loire, plus forte que celles qu'enregistrent les arrêtés depuis 1983. Avec la remontée de nappe, 14 collèges de plus entrent dans la famille inondation sans être dans un PPRI.

**3. Le classement change-t-il si l'on change les rayons et les seuils ?**
Oui, il faut le dire. Le top 10 par défaut sert de référence :

| Réglage | Collèges à 2 risques ou + | Top 10 conservé |
|---|---|---|
| Par défaut | 33 | 10 / 10 |
| Seveso à 1 km | 31 | 10 / 10 |
| Seveso à 5 km | 36 | 8 / 10 |
| Carte des argiles Géorisques | 40 | 8 / 10 |
| Au moins 10 sites CASIAS | 27 | 7 / 10 |
| Au moins 1 site CASIAS | 43 | 5 / 10 |

Le haut du classement résiste bien au rayon Seveso et à la carte des argiles. Il est **plus sensible au seuil des sites industriels** : c'est le réglage à justifier en priorité, d'où le choix du 3ᵉ quartile. Les trois réglages se testent en direct dans la partie « Sensibilité » de l'appli.

**4. L'exposition est-elle liée à l'IPS ?**
Non : la corrélation est de +0,09 (voir la question métier 6).

**5. Quels collèges sont proches d'un axe TMD ou d'un site Seveso, et lesquels cumulent avec un risque naturel ?**
27 collèges ont la famille technologique : 21 sont dans une zone TMD de 500 m et 9 ont un site Seveso à moins de 2 km. **17 d'entre eux cumulent avec un risque naturel** (sol ou inondation), soit 9 381 élèves.

**6. Quels collèges exposés sont dans une commune sans DICRIM ?**
Onze collèges. Les plus importants :
- **Montjoie** (Saran) : 3 risques, et +24 % d'élèves ;
- **Charles Desvergnes** (Bellegarde) : 3 risques ;
- **Léon Delagrange** (Neuville-aux-Bois) : 2 risques ;
- **Gutenberg** (Malesherbes) : 2 risques.

Les autres : Montabuzard (Ingré), La Forêt (Traînou), Aristide Bruant (Courtenay), Mary Jackson (Dadonville), Alfred de Musset (Patay), La Vallée de l'Ouanne (Château-Renard), Louis Joseph Soulas (Bazoches-les-Gallerandes).

C'est un levier peu coûteux : demander à ces mairies de publier leur DICRIM.

## 7. La couche ML : prévoir les effectifs

**Ce que ça apporte à la décision** : des travaux votés aujourd'hui sont livrés dans 2 ou 3 ans. Ce qui compte, ce sont les élèves qui *seront* dans le collège exposé. L'appli affiche la prévision dans l'indicateur « Élèves concernés », dans la fiche collège (en pointillé sur le graphique des effectifs), et peut s'en servir pour départager le classement.

**Le modèle** : une régression **Ridge** par horizon, de 1 à 5 ans. Un exemple, c'est un collège à une rentrée ; la cible, la variation de son effectif quelques années plus tard. Les variables sont les parts de 6e, 5e et 4e (une grosse promotion de 6e reste 3 ans encore), l'IPS et la taille du collège. Ridge est un modèle linéaire régularisé : il convient à un petit jeu de données.

**L'évaluation** : on cache la rentrée 2025, on la prédit avec un modèle qui ne l'a jamais vue, et on mesure l'erreur absolue moyenne (MAE) en élèves. On la compare à la méthode naïve « l'effectif ne bouge pas ».

| Horizon | Modèle | « Ne bouge pas » | Exemples |
|---|---|---|---|
| 1 an | 14,5 | 15,8 | 286 |
| 2 ans | 21,1 | 21,6 | 228 |
| 3 ans | 26,5 | 27,4 | 170 |
| 4 ans | 34,3 | 32,4 | 112 |
| 5 ans | 43,8 | 41,9 | 56 |

**Ce qu'il faut en dire honnêtement** : le modèle fait un peu mieux que la méthode naïve jusqu'à 3 ans, mais l'écart est faible. Au-delà, il n'a que 1 ou 2 années d'exemples et fait moins bien : l'appli le signale. Avec 7 rentrées connues et sans les effectifs de CM2 des écoles voisines, une prévision d'effectifs reste un ordre de grandeur. Elle sert à repérer les collèges qui vont grandir, pas à dimensionner une classe.

## 8. Limites à dire avant qu'on vous les demande

- L'exposition est mesurée **en un point** (l'adresse géocodée du collège), pas sur l'emprise du bâtiment.
- « Non cartographié » pour les argiles peut vouloir dire une couche incomplète, et les deux cartes des argiles ne classent pas pareil.
- Un ancien site industriel **n'est pas une pollution prouvée** : c'est le diagnostic qui le vérifie.
- Les rayons (500 m, 2 km) et le seuil de 5 sites sont **nos choix**, pas des seuils officiels.
- Un arrêté CatNat mesure aussi la **démarche du maire**, pas seulement la catastrophe.
- Les **12 collèges privés** sont exclus : ils n'appartiennent pas au Département.
- Les données Géorisques sont celles du jour de l'appel. `uv run python preparer.py --rafraichir` les met à jour.
