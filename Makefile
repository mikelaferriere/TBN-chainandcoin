SHELL := /bin/bash -e -o pipefail
.DEFAULT_GOAL := help

help:
	cat README.md

pip-test:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements-test.txt

pip-dev:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements-dev.txt

pip: pip-dev pip-test
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt

install-pre-commit:
	@pre-commit install && pre-commit install -t pre-push

run-node:
	python blockchain_node.py

run-console:
	python console.py

.PHONY: \
	help
