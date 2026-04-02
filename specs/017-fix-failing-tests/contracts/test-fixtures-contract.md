# Contract: Fixtures de test partagés

## Fixture `override_auth`

**Scope**: function
**Emplacement**: `backend/tests/conftest.py`

### Comportement
- Override `get_current_user` dependency avec un mock user
- Nettoyage automatique après chaque test (yield pattern)
- Le mock user a un `id` UUID valide, `email` unique, `is_active=True`

### Usage
```python
@pytest.mark.usefixtures("override_auth")
async def test_my_endpoint(client):
    response = await client.get("/api/some-endpoint")
    assert response.status_code == 200
```

## Helper `make_conversation_state(**overrides)`

**Emplacement**: `backend/tests/conftest.py`

### Comportement
- Retourne un dict complet avec les 27 clés de ConversationState
- Toutes les valeurs par défaut sont les "zéro values" (None, [], False, 0)
- Accepte des overrides via kwargs pour personnaliser le state par test

### Usage
```python
state = make_conversation_state(
    messages=[HumanMessage(content="test")],
    user_id="user-123",
    _route_financing=True,
)
```
