# SG Office 2 -- round-trip fidelity gate (ADR 0016, Phase 1). Dev/QA only.
# `make test` opens the tracked corpus in the engine, saves it back, and fails
# on any regression vs baseline.json. The ONLYOFFICE engine is fetched into
# ./oracle (git-ignored, NEVER shipped) by fetch-oracle.sh.
ENGINE = oracle/extracted/opt/onlyoffice/documentbuilder

.PHONY: test baseline corpus oracle clean
test: oracle
	@python3 roundtrip.py --baseline baseline.json

oracle: $(ENGINE)/docbuilder
$(ENGINE)/docbuilder:
	@sh fetch-oracle.sh

baseline: oracle
	@rm -f baseline.json && python3 roundtrip.py --baseline baseline.json

# Regenerate the independent corpus (needs python-docx/openpyxl/python-pptx).
corpus:
	@python3 gen_corpus.py corpus

clean:
	@rm -rf oracle .venv out
