.PHONY: install demo test api wiki clean-outputs check-env lint install-frontend frontend

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"
	@echo "--- Installing CadQuery (optional but recommended; large download) ---"
	-$(PIP) install -e "backend[cad]" || echo "WARNING: CadQuery install failed; demo will use labeled placeholder STL writer."
	@echo "Install complete. Run: make demo"

demo:
	$(PY) scripts/run_demo.py

test:
	$(PY) -m pytest backend/tests -q

api:
	$(PY) -m uvicorn app.main:app --app-dir backend --reload --port 8000

wiki:
	$(PY) scripts/update_wiki.py

clean-outputs:
	rm -rf outputs/*
	@echo "outputs/ cleaned"

check-env:
	$(PY) scripts/check_env.py

lint:
	$(VENV)/bin/ruff check backend scripts

install-frontend:
	cd frontend && npm install --no-audit --no-fund

frontend:
	cd frontend && npm run dev
