# Quickstart: Correction des 34 tests en échec

**Branch**: 017-fix-failing-tests

## Vérification rapide

```bash
cd backend
source venv/bin/activate

# Lancer uniquement les 9 fichiers impactés
pytest tests/test_financing_status.py tests/test_financing_intermediaries.py tests/test_financing_preparation.py tests/test_financing_node.py tests/test_credit/test_node.py tests/test_chat.py tests/test_applications/test_node.py tests/test_report_router.py tests/test_report_service.py -v

# Vérifier zéro régression sur la suite complète
pytest --tb=short -q
```

## Objectif

34 tests en échec → 0 échec. 901/901 pass.

## Fichiers à modifier

| Fichier | Modification |
|---------|-------------|
| `tests/conftest.py` | Ajouter fixture `override_auth` + helper `make_conversation_state()` |
| `tests/test_financing_status.py` | Utiliser fixture `override_auth`, supprimer `@patch` auth |
| `tests/test_financing_intermediaries.py` | Idem |
| `tests/test_financing_preparation.py` | Idem |
| `tests/test_financing_node.py` | Utiliser `make_conversation_state()` |
| `tests/test_credit/test_node.py` | Utiliser `make_conversation_state()` |
| `tests/test_chat.py` | Remplacer `json=` par `data=` |
| `tests/test_applications/test_node.py` | AIMessage + AsyncMock chain |
| `tests/test_report_router.py` | Mock WeasyPrint via sys.modules |
| `tests/test_report_service.py` | Mock WeasyPrint via sys.modules |
