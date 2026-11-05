PYTHON ?= python3
CLI := tools/claims.py
LLM_CHECK = scripts/smoke_llm.py
NOTES_CHECK = tools/check_notes.py

.PHONY: check check-all clean smoke-llm check-notes

check:
	$(if $(CLAIM),,$(error Usage: make check CLAIM=C01 [TIER=reported|certified]))
	$(PYTHON) $(CLI) check $(CLAIM) $(if $(TIER),--tier $(TIER))

check-all:
	$(PYTHON) $(CLI) check --all $(if $(TIER),--tier $(TIER))

smoke-llm:
	$(PYTHON) $(LLM_CHECK)

check-notes:
	uv run python $(NOTES_CHECK)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete