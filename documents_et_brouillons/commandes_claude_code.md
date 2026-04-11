claude --effort low
claude --effort medium
claude --effort high
claude --effort max

---

# Comment l'assistant IA génère-t-il le bilan carbone et le plan d'action ?

L'assistant intelligent d'ESG Mefali n'invente rien : il s'appuie sur des **données vérifiées et des règles de calcul fiables**. Voici, en termes simples, sur quoi il se base.

## 1. Le Bilan Carbone

**L'IA joue le rôle d'un enquêteur, pas d'un calculateur.**

Concrètement, l'assistant pose des questions à l'entreprise, récupère les informations (consommation d'électricité, litres de carburant, quantité de déchets…), puis **confie tous les calculs à des outils automatiques intégrés à la plateforme**. L'IA elle-même n'a pas le droit de calculer les tonnes de CO2 — c'est une règle stricte pour garantir la fiabilité des résultats.

### Les sources de données utilisées

**Des facteurs d'émission adaptés à l'Afrique de l'Ouest**
Ce sont les coefficients officiels qui permettent de transformer une consommation (par exemple 100 litres de diesel) en tonnes de CO2. La plateforme utilise des valeurs spécifiques à la région :
- Électricité du réseau ivoirien : 0,41 kg de CO2 par kWh
- Diesel : 2,68 kg de CO2 par litre
- Essence : 2,31 kg de CO2 par litre
- Gaz butane : 2,98 kg de CO2 par kg
- Déchets enfouis : 0,5 kg de CO2 par kg

**Des tarifs de référence en FCFA**
Beaucoup de PME connaissent le montant de leur facture sans savoir combien de kWh ou de litres cela représente. La plateforme dispose donc d'une table qui convertit automatiquement un montant en FCFA vers la quantité réelle consommée.

**Des repères sectoriels (benchmarks)**
Pour 11 secteurs d'activité (agriculture, agroalimentaire, énergie, transport…), la plateforme connaît l'empreinte carbone moyenne d'une entreprise typique. Cela permet de dire à l'utilisateur : « votre entreprise est en dessous / dans la moyenne / au-dessus de votre secteur ».

**Des équivalences parlantes**
Pour rendre les résultats compréhensibles, l'IA traduit les tonnes de CO2 en images concrètes : nombre de vols Paris-Dakar équivalents, kilomètres en voiture, etc.

### Le déroulement
L'assistant guide l'entreprise **catégorie par catégorie** : d'abord l'énergie, puis les transports, puis les déchets, et enfin les processus industriels ou l'agriculture si le secteur le justifie. À chaque réponse, un outil interne calcule et enregistre automatiquement l'émission correspondante.

## 2. Le Plan d'Action

**L'IA joue le rôle d'un conseiller qui lit le dossier complet de l'entreprise avant de proposer ses recommandations.**

Avant de générer un plan d'action, la plateforme rassemble **toutes les informations déjà collectées sur l'entreprise** et les transmet à l'IA. Cette dernière ne produit donc jamais de recommandations génériques : ses propositions sont toujours basées sur la situation réelle de l'entreprise.

### Les informations transmises à l'IA

| Source | Contenu |
|---|---|
| **Profil de l'entreprise** | Secteur d'activité, nombre de salariés, chiffre d'affaires, pays |
| **Évaluation ESG** | Dernier score environnemental, social et gouvernance obtenu |
| **Bilan carbone** | Dernier bilan finalisé (tonnes de CO2, année) |
| **Financements compatibles** | Les 5 meilleurs fonds verts qui correspondent au projet (avec leur score de compatibilité) |
| **Annuaire des intermédiaires** | Les organismes partenaires qui peuvent accompagner l'entreprise dans sa démarche (nom, adresse, téléphone, email) |
| **Horizon choisi** | 6, 12 ou 24 mois |

### Ce que produit l'IA

L'IA rédige une **liste d'actions concrètes et personnalisées**, classées dans 6 catégories :
- Environnement
- Social
- Gouvernance
- Financement
- Carbone
- Contact avec un intermédiaire

Pour chaque action, elle précise : le titre, la description, la priorité, la date d'échéance, le coût estimé en FCFA, le bénéfice attendu et éventuellement un fonds ou un intermédiaire à contacter.

### Un point important : la traçabilité
Lorsque l'IA recommande de contacter un intermédiaire, ses coordonnées (nom, adresse, téléphone, email) sont **enregistrées définitivement dans le plan d'action au moment de la génération**. Ainsi, même si l'annuaire de la plateforme évolue par la suite, l'entreprise garde les informations exactes qui lui ont été fournies.

**Prérequis :** l'entreprise doit avoir rempli son profil avant de pouvoir générer un plan d'action, sinon la plateforme bloque la demande.

## En résumé

- **Pour le bilan carbone**, l'IA est un **enquêteur guidé** : elle pose les bonnes questions et laisse les outils de calcul produire les chiffres, en s'appuyant sur des facteurs d'émission et des référentiels adaptés à l'Afrique de l'Ouest.
- **Pour le plan d'action**, l'IA est un **conseiller contextuel** : elle analyse les scores ESG, le bilan carbone, les financements compatibles et l'annuaire des intermédiaires *réellement liés à l'entreprise*, puis propose des recommandations sur mesure — jamais de conseils génériques.

Dans les deux cas, la règle fondamentale est la même : **l'IA ne fabrique pas de chiffres, elle exploite uniquement des données vérifiées stockées dans la plateforme**.

---

# Les formules de calcul utilisées par la plateforme

Voici, module par module, toutes les formules mathématiques qui tournent « derrière » l'IA. Ce sont ces formules — et non l'IA — qui produisent les chiffres affichés à l'utilisateur.

## 1. Bilan Carbone

### 1.1 Calcul des émissions d'une source (en tonnes de CO2)

```
émissions (tCO2e) = (quantité consommée × facteur d'émission) ÷ 1000
```

- **quantité consommée** : ce que l'entreprise a utilisé (litres de diesel, kWh d'électricité, kg de déchets…)
- **facteur d'émission** : coefficient officiel adapté à l'Afrique de l'Ouest (ex : 2,68 kg CO2 par litre de diesel)
- **÷ 1000** : pour convertir les kilos en tonnes

**Exemple :** 500 litres de diesel × 2,68 ÷ 1000 = **1,34 tonne de CO2**

### 1.2 Conversion d'un montant en FCFA vers une quantité physique

```
quantité = montant en FCFA ÷ prix unitaire de référence
```

**Exemple :** facture d'électricité de 1 000 000 FCFA ÷ 100 FCFA/kWh = **10 000 kWh consommés**

### 1.3 Équivalences parlantes

```
nombre d'équivalents = total tCO2e ÷ valeur de l'équivalence
```

- 1 vol Paris-Dakar = 1,2 tCO2e
- 1 année de conduite automobile = 2,4 tCO2e
- 1 arbre absorbe par an = 0,025 tCO2e

**Exemple :** 10 tCO2e ÷ 1,2 = **8,3 vols Paris-Dakar**

### 1.4 Positionnement sectoriel (benchmark)

La plateforme compare le total de l'entreprise à la médiane et à la moyenne de son secteur :

| Situation | Position | Percentile |
|---|---|---|
| ≤ médiane × 0,7 | Bien en dessous de la moyenne | 20 |
| ≤ médiane | En dessous de la moyenne | 35 |
| ≤ moyenne | Dans la moyenne | 50 |
| ≤ moyenne × 1,3 | Au-dessus de la moyenne | 70 |
| > moyenne × 1,3 | Bien au-dessus de la moyenne | 85 |

### 1.5 Répartition par catégorie

```
pourcentage d'une catégorie = (émissions de la catégorie ÷ total) × 100
```

## 2. Scoring ESG (sur 100)

### 2.1 Notation de chaque critère
Chaque critère est noté **de 0 à 10** (30 critères au total : 10 pour l'Environnement, 10 pour le Social, 10 pour la Gouvernance).

### 2.2 Score d'un pilier (E, S ou G)

```
score du pilier = [ Σ (note × poids) ÷ (Σ poids × 10) ] × 100
```

- **note** : note du critère entre 0 et 10
- **poids** : coefficient qui dépend du secteur (par défaut 1,0 ; jusqu'à 1,5 pour les critères clés du secteur)

**Exemple Agriculture** : le critère « gestion de l'eau » a un poids de 1,5 au lieu de 1,0, car c'est un enjeu majeur du secteur.

### 2.3 Score global ESG

```
score global = (score Environnement + score Social + score Gouvernance) ÷ 3
```

Les trois piliers pèsent **à parts égales** (33 % chacun).

## 3. Plan d'Action — Progression

```
progression globale (%) = (actions terminées ÷ actions totales) × 100

progression d'une catégorie (%) = (actions terminées de la catégorie ÷ actions totales de la catégorie) × 100
```

**Exemple :** 8 actions terminées sur 20 → **40 % de progression globale**.

## 4. Matching Financement — Score de compatibilité (sur 100)

```
score final = secteur × 30 %
            + ESG × 25 %
            + documents × 20 %
            + taille × 15 %
            + localisation × 10 %
```

### Détail des sous-scores

| Critère | Calcul |
|---|---|
| **Secteur** | 100 si secteur exact, 70 si secteur similaire, 20 sinon |
| **ESG** | Si score ESG ≥ minimum requis : 50 + (score ÷ min) × 25, plafonné à 100. Sinon : (score ÷ min) × 50, minimum 10 |
| **Taille** | Basé sur le ratio chiffre d'affaires / fourchette acceptée par le fonds |
| **Localisation** | 100 si pays éligible, 10 sinon |
| **Documents** | (documents fournis ÷ documents exigés) × 100 |

**Exemple :** PME agricole, ESG 55/100, CA 500 M FCFA, Côte d'Ivoire
```
(100 × 0,30) + (60 × 0,25) + (80 × 0,20) + (80 × 0,15) + (100 × 0,10)
= 30 + 15 + 16 + 12 + 10 = 83/100
```

## 5. Scoring Crédit Vert Alternatif (sur 100)

### 5.1 Score de solvabilité

```
solvabilité = régularité d'activité × 20 %
            + cohérence des informations × 20 %
            + gouvernance × 20 %
            + transparence financière × 20 %
            + sérieux de l'engagement × 20 %
```

Chaque facteur est noté de 0 à 100, les cinq pèsent autant.

### 5.2 Score d'impact vert

```
impact vert = score ESG global × 40 %
            + tendance ESG × 20 %
            + engagement carbone × 20 %
            + projets verts × 20 %
```

### 5.3 Indice de confiance

```
confiance = 0,5 + (couverture des sources × 0,3) + (fraîcheur des données × 0,2)
```
La confiance est toujours comprise entre **0,5 et 1,0**.

- **couverture des sources** : proportion des 6 sources disponibles (profil, ESG, carbone, documents, candidatures, interactions)
- **fraîcheur** : 1 si les données sont récentes, 0 si elles ont plus de 12 mois

### 5.4 Score final combiné

```
score crédit = ( solvabilité × 50 % + impact vert × 50 % ) × confiance
```

**Exemple :** solvabilité 75, impact vert 65, confiance 0,85
```
(75 × 0,5 + 65 × 0,5) × 0,85 = 70 × 0,85 = 59,5/100
```

### 5.5 Score d'engagement avec les intermédiaires

```
engagement = (intermédiaires contactés, max 2) × 15
           + (rendez-vous, max 1) × 20
           + (dossiers soumis, max 1) × 30
           + (dossiers acceptés, max 1) × 20
```

**Exemple :** 2 contacts + 1 rendez-vous + 1 dossier soumis = 30 + 20 + 30 = **80/100**

---

## Récapitulatif des formules principales

| Module | Formule clé | Échelle |
|---|---|---|
| **Carbone** | `tCO2e = (quantité × facteur) ÷ 1000` | tonnes |
| **ESG par pilier** | `[Σ(note × poids) ÷ (Σ poids × 10)] × 100` | /100 |
| **ESG global** | `(E + S + G) ÷ 3` | /100 |
| **Plan d'action** | `(actions terminées ÷ total) × 100` | % |
| **Matching financement** | `30 % secteur + 25 % ESG + 20 % docs + 15 % taille + 10 % lieu` | /100 |
| **Crédit vert** | `(50 % solvabilité + 50 % impact) × confiance` | /100 |

**À retenir :** toutes ces formules sont **fixes et auditables**. L'IA peut expliquer les résultats avec des mots, mais ce sont ces calculs déterministes — et non le modèle de langage — qui produisent les chiffres affichés dans la plateforme.
