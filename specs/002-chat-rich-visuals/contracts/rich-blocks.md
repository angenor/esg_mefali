# Contrat: Rich Blocks (Blocs Visuels)

**Date**: 2026-03-30

## Convention de balisage

Les blocs visuels sont encodes dans le contenu textuel des messages sous forme de fenced code blocks markdown avec un identifiant de langage specifique :

```
texte normal en markdown...

` ` `chart
{"type":"radar","data":{"labels":["E","S","G"],"datasets":[{"data":[65,72,58]}]}}
` ` `

suite du texte normal...
```

(Les espaces dans ` ` ` sont ajoutes pour echappement — en realite, pas d'espaces.)

## Types de blocs supportes

| Identifiant | Contenu | Format |
|-------------|---------|--------|
| `chart` | Configuration Chart.js | JSON |
| `mermaid` | Code diagramme Mermaid | Texte brut |
| `table` | Donnees tabulaires | JSON |
| `gauge` | Jauge de score | JSON |
| `progress` | Barres de progression | JSON |
| `timeline` | Frise chronologique | JSON |

## Schemas JSON par type

### chart
```json
{
  "type": "radar",
  "data": {
    "labels": ["Environnement", "Social", "Gouvernance"],
    "datasets": [{
      "label": "Score ESG",
      "data": [65, 72, 58],
      "backgroundColor": "rgba(16, 185, 129, 0.2)",
      "borderColor": "#10B981"
    }]
  },
  "options": {}
}
```
**Champs requis** : `type`, `data.labels`, `data.datasets`

### table
```json
{
  "headers": ["Critere", "Score", "Statut"],
  "rows": [
    ["Emissions CO2", 72, "Bon"],
    ["Gestion dechets", 45, "A ameliorer"]
  ],
  "highlightColumn": 1,
  "sortable": true
}
```
**Champs requis** : `headers`, `rows`

### gauge
```json
{
  "value": 72,
  "max": 100,
  "label": "Score ESG",
  "thresholds": [
    { "limit": 40, "color": "#EF4444" },
    { "limit": 70, "color": "#F59E0B" },
    { "limit": 100, "color": "#10B981" }
  ],
  "unit": "/100"
}
```
**Champs requis** : `value`, `max`, `label`, `thresholds`

### progress
```json
{
  "items": [
    { "label": "Environnement", "value": 65, "max": 100, "color": "#10B981" },
    { "label": "Social", "value": 72, "max": 100, "color": "#3B82F6" },
    { "label": "Gouvernance", "value": 58, "max": 100, "color": "#8B5CF6" }
  ]
}
```
**Champs requis** : `items` (chaque item : `label`, `value`, `max`)

### timeline
```json
{
  "events": [
    { "date": "2026-Q1", "title": "Audit initial", "status": "done" },
    { "date": "2026-Q2", "title": "Plan d'action", "status": "in_progress", "description": "Elaboration du plan ESG" },
    { "date": "2026-Q3", "title": "Certification", "status": "todo" }
  ]
}
```
**Champs requis** : `events` (chaque event : `date`, `title`, `status`)

### mermaid
```
graph LR
    A[Evaluation] --> B[Plan d'action]
    B --> C[Implementation]
    C --> D[Certification]
```
**Validation** : `mermaid.parse()` doit retourner true.

## Comportement d'erreur

| Situation | Comportement |
|-----------|--------------|
| JSON invalide (parse error) | Afficher code brut + "Impossible d'afficher la visualisation" |
| Champs requis manquants | Afficher code brut + message erreur |
| Syntaxe Mermaid invalide | Afficher code brut + message erreur |
| Echec de rendu (Canvas/SVG) | Fallback vers code brut |
| Bloc incomplet (streaming) | Placeholder "Generation du graphique..." avec spinner |

## Palette de couleurs

| Couleur | Hex | Usage |
|---------|-----|-------|
| Vert | #10B981 | Scores positifs, statut "done" |
| Bleu | #3B82F6 | Donnees principales, statut "in_progress" |
| Violet | #8B5CF6 | Donnees secondaires |
| Orange | #F59E0B | Scores moyens, attention |
| Rouge | #EF4444 | Scores faibles, alertes |
