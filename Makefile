.PHONY: dev build migrate test test-back test-front down logs

# Lancer en mode développement
dev:
	docker compose up --build

# Build de production
build:
	docker compose build

# Exécuter les migrations Alembic
migrate:
	docker compose exec backend alembic upgrade head

# Lancer tous les tests
test: test-back test-front

# Tests backend
test-back:
	docker compose exec backend python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Tests frontend
test-front:
	docker compose exec frontend npm run test

# Arrêter les services
down:
	docker compose down

# Voir les logs
logs:
	docker compose logs -f

# Arrêter et supprimer les volumes
clean:
	docker compose down -v
