.PHONY: run_nox, run_black

run_nox:
	python -m nox -r

run_black:
	python -m nox -rs black