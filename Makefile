SHELL := /bin/bash -e -o pipefail
.DEFAULT_GOAL := help

help:
	cat README.md

pip:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements-dev.txt

install-pre-commit:
	@pre-commit install && pre-commit install -t pre-push

.PHONY: \
	help
