SHELL := /bin/bash -e -o pipefail
.DEFAULT_GOAL := help

help:
	cat README.md

pip-dev:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements-dev.txt

pip: pip-dev
	python3 -m pip install -r requirements.txt

install-pre-commit:
	@pre-commit install && pre-commit install -t pre-push

run-node:
	python blockchain_node.py

.PHONY: \
	help
