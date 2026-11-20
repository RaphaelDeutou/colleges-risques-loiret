# Cadrage · Collèges et risques dans le Loiret

## 1. Quelles données ? Pas les 182 jeux

**Ne téléchargez pas tout le catalogue GéoLoiret.** Sur 182 jeux, environ 170 ne servent pas ce cas : fonds BD TOPO (bâtiments, routes, haies…), découpages administratifs, action sociale, tourisme, trafic. Certains sont énormes (Bâtiments : 534 000 objets, BAN : 287 000), alors que le cours limite à 50 Mo et demande un Parquet léger lu par l'appli.

**Le formateur a déjà fait le croisement.** Les 6 fichiers du cas sont copiés dans `data/` (≈ 0,9 Mo au total) :

| Fichier | Contenu | Rôle dans l'appli |
|---|---|---|
| `colleges_risques.parquet` | 70 collèges × 29 colonnes, exposition au point du collège | **fichier principal** |
| `colleges.parquet` | 70 collèges × 10 rentrées (2016-2025), effectifs, IPS, brevet | collèges qui grandissent |
| `risques_communes.parquet` | 325 communes, exposition et CatNat | contexte communal |
| `risques_catnat.parquet` | 2 065 arrêtés CatNat (1983-2025) | drill-down « risque vécu » |
| `colleges_secteurs.geojson` | secteurs de recrutement | carte |
| `risques_communes.geojson` | contours des communes | carte |

Ils viennent de ces 10 jeux GéoLoiret, plus l'Éducation nationale et Géorisques (GASPAR) :

- Collèges publics et privés · Secteurs des collèges
- Aléa retrait-gonflement des argiles · Cavités souterraines · Mouvements de terrain (BRGM)
- Périmètres des PPRI (Loire, Loing, Ouanne, Essonne) · Repères de crues
- Installations classées (ICPE, Seveso) · Transport de matières dangereuses + zones de 500 m · Centrales nucléaires

Le script qui les produit : `awp-gabarit/sources/build_colleges_risques.py`. Retournez au catalogue uniquement pour un ajout précis, par exemple *Données carroyées 2023* (population autour du collège).

**Licence** : Licence Ouverte 2.0. À citer dans l'appli : « Source : BRGM / DDT45 / Département du Loiret, année », « Géorisques, GASPAR », « ministère de l'Éducation nationale ».

## 2. Ce que disent déjà les données (58 collèges publics, 31 463 élèves)

| Facteur | Collèges publics |
|---|---|
| Argiles aléa **fort** / moyen | **10** / 42 |
| Dans un périmètre de PPRI (tous Loire) | **6** (3 004 élèves) |
| Dans une zone TMD de 500 m | 21 |
| Site Seveso à moins de 2 km | 9 |
| Au moins une cavité à moins de 500 m | 14 |
| Au moins un mouvement de terrain à moins de 500 m | 15 |
| Commune sans DICRIM | 12 |

Ce qu'on en tire :

- Les **ICPE** ne départagent pas les collèges : tous en ont une à moins de 2,2 km (médiane : 4 à moins de 1 km), et la couche compte aussi des élevages et des éoliennes. Utilisez plutôt **Seveso**.
- Les **argiles moyennes** touchent 42 collèges sur 58 et départagent peu. Retenez **fort** comme facteur.
- Seuls **58 collèges** sont publics : filtrez `statut == "public"` avant de classer.

## 3. Fiche de cadrage (les 8 points du cours)

1. **Utilisateur** : un chargé de patrimoine à la direction des collèges du Département. Il connaît ses bâtiments, pas les couches BRGM. Les élus regardent l'écran en commission.
2. **Décision** : *choisir les collèges publics à inscrire en priorité au programme de diagnostics 2027, et le type de diagnostic à commander pour chacun (sol, inondation ou industriel).*
3. **Trois questions, dans l'ordre :**
   1. Combien de collèges et d'élèves sont exposés, et à quel risque ?
   2. Quels collèges cumulent plusieurs familles de risque ?
   3. Pour ce collège, quel diagnostic demander, et qu'a déjà vécu sa commune (arrêtés CatNat) ?
4. **Indicateurs (3, calculés sur la vue filtrée)** : collèges publics exposés à au moins 2 familles · élèves dans ces collèges · collèges en argiles fortes ou en PPRI.
5. **Filtres** : famille de risque (sol / inondation / technologique) ; effectif ou évolution des effectifs (collèges qui grandissent) ; EPCI ou commune.
6. **Drill-down, 3 niveaux** : famille de risque → commune → fiche collège (facteurs, effectifs sur 10 ans, arrêtés CatNat de la commune).
7. **Couche IA (LLM recommandé)** : une **fiche risques pour un élu**, générée à partir des seuls indicateurs affichés, avec les chiffres sources visibles à côté. Variante ML : un k-means sur les variables d'exposition, pour obtenir des profils de risque.
8. **Framework : Streamlit.** Une page, un déploiement gratuit sur Community Cloud, et `on_select` sur Plotly pour le drill-down par clic. Ça suffit pour 70 points.

## 4. Classement : rester transparent

Plutôt qu'un score opaque, comptez des **familles de risque** binaires et justifiables :

| Famille | Règle proposée | Diagnostic associé |
|---|---|---|
| Sol | argiles **fort** OU cavité OU mouvement de terrain à moins de 500 m | étude géotechnique |
| Inondation | `dans_ppri` | diagnostic de vulnérabilité inondation |
| Technologique | zone TMD de 500 m OU Seveso à moins de 2 km | PPMS, confinement |

Classez par **nombre de familles**, puis par **effectif**. Affichez la règle dans l'appli : c'est ce qui donne les points de « pertinence métier ». Les rayons (500 m, 2 km) sont des choix du projet, pas des seuils officiels : dites-le.

**À afficher dans l'appli** : un aléa n'est pas un risque ; un périmètre PPRI n'est pas la zone inondable ; le nombre d'arrêtés CatNat dépend aussi des demandes des maires.

## 5. Page dessinée

```
[ Titre = le constat : « 13 collèges publics cumulent 2 risques : 7 200 élèves » ]
[ KPI 1 ]        [ KPI 2 ]        [ KPI 3 ]
Filtres |  Carte des collèges (taille = élèves, couleur = nb de familles)
        |  Barres : collèges classés (clic → fiche)
        |  Fiche collège : facteurs, effectifs 10 ans, CatNat, bouton « fiche élu » (LLM)
```

(Les chiffres du titre sont des exemples : calculez les vrais au sprint 1.)
