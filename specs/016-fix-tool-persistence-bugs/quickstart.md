# Quickstart: Fix Tool Persistence Bugs

## Fichiers à modifier (7 fichiers)

### Backend (5 fichiers)

1. **`backend/app/prompts/esg_scoring.py`**
   - Remonter la section "SAUVEGARDE PAR LOT" avant les instructions visuelles
   - Ajouter "REGLE ABSOLUE" : forcer batch_save_esg_criteria après chaque réponse ESG

2. **`backend/app/graph/nodes.py` (esg_scoring_node, lignes 601-615)**
   - Ajouter `batch_save_esg_criteria` dans la liste des tools documentés
   - Remplacer les tool_instructions par le pattern "REGLE ABSOLUE"

3. **`backend/app/graph/nodes.py` (carbon_node, lignes 758-768)**
   - Remplacer les tool_instructions par le pattern "REGLE ABSOLUE" pour save_emission_entry

4. **`backend/app/prompts/financing.py`**
   - Retirer la liste détaillée des fonds (section "BASE DE DONNEES DES FONDS")
   - Garder seulement "Tu as accès à une base de fonds verts via search_compatible_funds"

5. **`backend/app/graph/nodes.py` (financing_node, lignes 868-876)**
   - Renforcer les tool_instructions avec "REGLE ABSOLUE"

6. **`backend/app/prompts/system.py` (build_system_prompt)**
   - Ajouter instruction de correction des données inexistantes dans _format_profile_section

### Frontend (1 fichier)

7. **`frontend/app/components/chat/MessageParser.vue`**
   - Condition : si `!segment.isComplete && !isStreaming` → tenter de rendre le bloc au lieu d'afficher BlockPlaceholder

## Ordre d'implémentation

1. Tests d'abord (TDD) : écrire les tests de conformité des prompts
2. Backend prompts/nodes : appliquer le pattern "REGLE ABSOLUE" aux 3 modules
3. Backend system.py : ajouter instruction correction données inexistantes
4. Frontend MessageParser : fix gauge bloquée
5. Tests d'intégration : vérifier avec le plan de test

## Commandes

```bash
# Backend
source backend/venv/bin/activate
cd backend && python -m pytest tests/ -v --tb=short

# Frontend
cd frontend && npm run test
```
