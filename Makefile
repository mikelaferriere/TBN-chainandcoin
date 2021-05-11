SHELL := /bin/bash -e -o pipefail
.DEFAULT_GOAL := help

help:
	cat README.md

linux-deps:
	sudo snap install protobuf --classic

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

generate-protobuf:
	protoc interfaces/transaction.proto --python_out ./ --proto_path generated=./interfaces/ --experimental_allow_proto3_optional
	protoc interfaces/block.proto --python_out ./ --proto_path generated=./interfaces/ --experimental_allow_proto3_optional

.PHONY: \
	help
