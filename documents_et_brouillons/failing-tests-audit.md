# Audit des 34 tests en échec (pré-existants)

**Date** : 2026-04-02
**Branche** : 016-fix-tool-persistence-bugs (tests hérités, pas causés par cette branche)
**Suite totale** : 901 tests (867 pass, 34 fail)

---

## Résumé par catégorie

| # | Catégorie | Tests | Fichiers | Cause racine |
|---|-----------|-------|----------|--------------|
| 1 | Auth 401 — financing status | 5 | `test_financing_status.py` | Patch auth non persistant dans AsyncClient |
| 2 | Auth 401 — intermediaires | 7 | `test_financing_intermediaries.py` | Idem |
| 3 | Auth 401 — préparation fiche | 3 | `test_financing_preparation.py` | Idem |
| 4 | Financing node — state incomplet | 4 | `test_financing_node.py` | State dict manque des clés requises |
| 5 | WeasyPrint — lib système absente | 6 | `test_report_router.py`, `test_report_service.py` | `libgobject-2.0` non installée |
| 6 | Credit node — state incomplet | 3 | `test_credit/test_node.py` | State dict manque des clés requises |
| 7 | Chat — Form vs JSON mismatch | 3 | `test_chat.py` | Endpoint attend Form(), tests envoient JSON |
| 8 | Application node — mock type | 1 | `test_applications/test_node.py` | MagicMock au lieu de AIMessage |
| | **TOTAL** | **34** | **9 fichiers** | **5 causes racines distinctes** |

---

## Catégorie 1-3 : Auth 401 (15 tests)

### Symptôme
Tous les tests retournent `401 Unauthorized` au lieu du status attendu (200, 404, 409, etc.).

### Tests concernés

**test_financing_status.py** (5) :
- `test_update_status_suggested_to_interested` — attend 200, reçoit 401
- `test_update_status_invalid_transition` — attend 409, reçoit 401
- `test_update_status_not_found` — attend 404, reçoit 401
- `test_update_intermediary_success` — attend 200, reçoit 401
- `test_update_intermediary_not_linked` — attend 409, reçoit 401

**test_financing_intermediaries.py** (7) :
- `test_list_intermediaries` — 401
- `test_list_intermediaries_with_type_filter` — 401
- `test_list_intermediaries_with_fund_filter` — 401
- `test_get_intermediary_detail` — 401
- `test_get_intermediary_not_found` — 401
- `test_nearby_intermediaries` — 401
- `test_nearby_requires_city` — 401

**test_financing_preparation.py** (3) :
- `test_preparation_sheet_endpoint` — 401
- `test_preparation_sheet_not_found` — 401
- `test_generate_preparation_sheet_content` — 401

### Cause racine
Les tests patchent `get_current_user` avec `@patch` mais le patch n'est pas persistant dans le cycle de vie async de `AsyncClient`. FastAPI évalue les dépendances AVANT le handler — le vrai `get_current_user` s'exécute, le header `Authorization: Bearer test` n'est pas un JWT valide → 401.

### Correction requise
Utiliser `app.dependency_overrides[get_current_user]` dans un fixture pytest au lieu de `@patch`. Exemple :

```python
@pytest.fixture
def override_auth(test_user):
    async def mock_get_current_user():
        return test_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
```

### Fichiers à modifier
- `backend/tests/test_financing_status.py`
- `backend/tests/test_financing_intermediaries.py`
- `backend/tests/test_financing_preparation.py`
- (ou créer un fixture partagé dans `backend/tests/conftest.py`)

---

## Catégorie 4 : Financing node — state incomplet (4 tests)

### Tests concernés

**test_financing_node.py** :
- `test_financing_node_generates_response`
- `test_financing_node_without_esg_redirects`
- `TestFinancingDetection::test_detect_subvention`
- `TestFinancingDetection::test_detect_credit_carbone`

### Cause racine
Le state dict passé aux tests ne contient pas toutes les clés requises par `ConversationState`. Les nodes accèdent à des champs comme `user_profile`, `financing_data`, `active_module`, etc. qui sont absents du mock state.

### Correction requise
Créer un fixture `make_conversation_state()` qui initialise un state complet avec toutes les clés de `ConversationState` à leurs valeurs par défaut (`None`, `[]`, `False`, etc.).

### Fichiers à modifier
- `backend/tests/test_financing_node.py`

---

## Catégorie 5 : WeasyPrint — lib système absente (6 tests)

### Tests concernés

**test_report_router.py** (5) :
- `TestGenerateEndpoint::test_generate_report_201`
- `TestStatusEndpoint::test_status_returns_200`
- `TestDownloadEndpoint::test_download_returns_pdf`
- `TestDownloadEndpoint::test_download_403_other_user`
- `TestListReportsEndpoint::test_list_reports_paginated`
- `TestListReportsEndpoint::test_list_reports_filter_by_assessment`
- `TestListReportsEndpoint::test_list_reports_user_isolation`

**test_report_service.py** (1) :
- `TestGenerateReport::test_generate_report_success`

### Cause racine
WeasyPrint nécessite des bibliothèques système C (`libgobject-2.0`, `libcairo`, `libpango`, `libgdk-pixbuf`). L'import `from weasyprint import HTML` échoue à `app/modules/reports/service.py:305` avec `OSError: cannot load library 'libgobject-2.0-0'`.

### Correction requise (2 options)

**Option A** (recommandée) : Mocker WeasyPrint dans les tests.
```python
@patch("app.modules.reports.service.HTML")
async def test_generate_report_201(self, mock_html, ...):
    mock_html.return_value.write_pdf.return_value = b"%PDF-1.4..."
```

**Option B** : Installer les dépendances système.
```bash
# macOS
brew install pango glib cairo gdk-pixbuf

# Linux
apt-get install libpango-1.0-0 libglib2.0-0 libcairo2 libgdk-pixbuf2.0-0
```

### Fichiers à modifier
- `backend/tests/test_report_router.py`
- `backend/tests/test_report_service.py`

---

## Catégorie 6 : Credit node — state incomplet (3 tests)

### Tests concernés

**test_credit/test_node.py** :
- `test_credit_node_generates_visual_blocks`
- `test_credit_node_no_score`
- `test_credit_node_preserves_credit_data`

### Cause racine
Même pattern que la catégorie 4 — le state dict du test est incomplet. Les tests mockent le LLM mais le state ne contient pas toutes les clés requises par `ConversationState`.

### Correction requise
Compléter le state dict avec toutes les clés de `ConversationState` (ou utiliser le même fixture `make_conversation_state()`).

### Fichiers à modifier
- `backend/tests/test_credit/test_node.py`

---

## Catégorie 7 : Chat — Form vs JSON mismatch (3 tests)

### Tests concernés

**test_chat.py** :
- `test_send_message_empty_content` — attend 422, reçoit 200
- `test_send_message_persists` — message non reçu par le endpoint
- `test_send_message_too_long` — validation longueur non déclenchée

### Cause racine
L'endpoint `send_message` déclare `content: str = Form(None)` (attend des données Form/multipart). Les tests envoient `json={"content": "..."}` (JSON body). FastAPI ne parse pas les champs `Form()` depuis un body JSON → `content=None` systématiquement.

### Correction requise (2 options)

**Option A** : Modifier les tests pour envoyer du Form data.
```python
response = await client.post("/api/chat/send", data={"content": "Mon message"})
```

**Option B** : Modifier l'endpoint pour accepter JSON.
```python
class MessageCreate(BaseModel):
    content: str

@router.post("/send")
async def send_message(body: MessageCreate, ...):
```

### Fichiers à modifier
- `backend/tests/test_chat.py` (si Option A)
- `backend/app/routers/chat.py` + `backend/tests/test_chat.py` (si Option B)

---

## Catégorie 8 : Application node — mock type incorrect (1 test)

### Test concerné

**test_applications/test_node.py** :
- `test_application_node_returns_messages`

### Cause racine
Le test crée `mock_response = MagicMock()` avec `.content = "..."`. Le node fait `response = await llm.ainvoke(...)` mais le mock de `get_llm()` retourne un coroutine qui, une fois awaited, tente d'appeler `.ainvoke()` sur un objet qui n'a pas cette méthode (l'async mock chain est incorrecte).

Erreur exacte : `AttributeError: 'coroutine' object has no attribute 'ainvoke'`

### Correction requise
Utiliser `AIMessage` au lieu de `MagicMock` et corriger le mock chain async :

```python
from langchain_core.messages import AIMessage

mock_response = AIMessage(content="Votre dossier SUNREF est en bonne voie !")
mock_llm = AsyncMock()
mock_llm.bind_tools.return_value = mock_llm  # chainage
mock_llm.ainvoke.return_value = mock_response
```

### Fichiers à modifier
- `backend/tests/test_applications/test_node.py`

---

## Plan de correction suggéré

### Phase 1 — Quick wins (impact maximal)
1. **Auth fixture partagé** dans `conftest.py` → corrige 15 tests (catégories 1-3)
2. **State fixture** `make_conversation_state()` → corrige 7 tests (catégories 4, 6)

### Phase 2 — Corrections ciblées
3. **Form vs JSON** dans `test_chat.py` → corrige 3 tests (catégorie 7)
4. **Mock AIMessage** dans `test_applications/test_node.py` → corrige 1 test (catégorie 8)

### Phase 3 — Dépendance système
5. **WeasyPrint mock ou install** → corrige 6 tests (catégorie 5)
6. Installer `brew install pango glib cairo gdk-pixbuf` OU mocker dans les tests

### Résultat attendu
34 tests corrigés → **901/901 tests pass (100%)**
