SHELL := /bin/bash -e -o pipefail
.DEFAULT_GOAL := help

help:
	cat README.md

pip:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt

run:
	python blockchain_api.py

.PHONY: \
	help
