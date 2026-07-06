.PHONY: venv test-backend rebuild test-frontend verify

VENV := backend/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	test -f backend/requirements.txt && $(PIP) install -r backend/requirements.txt -q || true
	test -f backend/requirements-dev.txt && $(PIP) install -r backend/requirements-dev.txt -q || true

test-backend: venv
	cd backend && .venv/bin/pytest -q

rebuild:
	docker compose down
	docker compose up -d --build
	@echo "Waiting for services to become healthy..."
	@for i in $$(seq 1 30); do \
		if curl -sf http://localhost:8000/health > /dev/null 2>&1; then \
			echo "Backend healthy."; exit 0; \
		fi; sleep 2; \
	done; echo "Backend did not become healthy in 60s" && docker compose logs backend --tail 50 && exit 1

test-frontend:
	docker compose run --rm frontend npm run test

verify: test-backend rebuild test-frontend
	@echo "✅ verify passed"
