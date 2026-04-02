# State Contract: active_module dans ConversationState

## Champs ajoutes

### active_module
- **Type**: `str | None`
- **Valeurs valides**: `None`, `"esg_scoring"`, `"carbon"`, `"financing"`, `"application"`, `"credit"`, `"profiling"`, `"document"`, `"action_plan"`
- **Producteurs**: router_node (activation/desactivation), noeuds specialistes (activation au demarrage, desactivation a la finalisation)
- **Consommateurs**: router_node (decision de routing), noeuds specialistes (lecture du contexte)

### active_module_data
- **Type**: `dict | None`
- **Producteurs**: noeuds specialistes (mise a jour apres chaque action)
- **Consommateurs**: noeuds specialistes (lecture de la progression)
- **Invariant**: Si `active_module` est `None`, `active_module_data` DOIT etre `None`

## Contrat du routeur

### Priorite de routing (ordre de decision)

```
1. SI active_module != None ET is_continuation(message) == True:
     → router vers active_module
     → conserver active_module et active_module_data inchanges

2. SI active_module != None ET is_continuation(message) == False:
     → active_module = None, active_module_data = None
     → classifier le message normalement (etape 3)

3. SI active_module == None:
     → classification normale du message (comportement actuel)
     → definir les flags _route_* comme avant
```

### Contrat is_continuation(message)

- **Entree**: message utilisateur (str), module actif (str)
- **Sortie**: bool (True = continuer dans le module, False = changement de sujet)
- **Defaut en cas d'erreur**: True (rester dans le module)
- **Methode**: Appel LLM classification binaire

## Contrat des noeuds specialistes

### Au demarrage de session
```
Le noeud retourne:
  active_module = nom_du_module
  active_module_data = {assessment_id, progression initiale}
```

### En cours de session
```
Le noeud retourne:
  active_module = nom_du_module (inchange)
  active_module_data = {assessment_id, progression mise a jour}
```

### A la finalisation
```
Le noeud retourne:
  active_module = None
  active_module_data = None
```
