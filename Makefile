# Colombus developer entry points. `make demo` is the one a doctor sees.
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup test eval demo demo-real demo-mock assess packet verify reset

setup:            ## create venv, install package + dev deps
	python3 -m venv .venv
	$(PIP) install -q -e ".[dev]"

test:             ## unit + property tests
	$(PY) -m pytest

eval:             ## run every case in cases/ against its golden expectation
	$(PY) -m colombus.cli eval

assess:           ## assess one case: make assess CASE=cases/demo/singh.yaml
	$(PY) -m colombus.cli assess $(CASE)

packet:           ## build + verify a packet for one case into out/
	$(PY) -m colombus.cli packet $(CASE)

demo:             ## run the web app on http://127.0.0.1:8765 (real cases, default)
	$(PY) -m colombus.cli serve

demo-real:        ## run the web app with real filesystem cases (USE_MOCK_PMS_API off)
	USE_MOCK_PMS_API=0 USE_MOCK_DATA=0 PMS_USE_MOCKS=0 $(PY) -m colombus.cli serve

demo-mock:        ## run the web app with dummy mock fixtures (USE_MOCK_PMS_API=true)
	USE_MOCK_PMS_API=true $(PY) -m colombus.cli serve

reset:            ## wipe demo state (assertions, sign-offs, audit log)
	rm -rf var/
