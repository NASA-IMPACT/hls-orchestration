SHELL := /bin/bash
REQUIRED_BINS := yarn virtualenv pip
$(foreach bin,$(REQUIRED_BINS),\
    $(if $(shell command -v $(bin) 2> /dev/null),$(info Found `$(bin)`),$(error Please install `$(bin)`)))

.ONESHELL:
.PHONY: check-env-% check-env cdk venv dev clean synth diff deploy fresh freshdev

check-env-%:
	@ if [ "${${*}}" = "" ]; then \
        echo "Environment variable $* not set"; \
        exit 1; \
    fi

check-env: check-env-STACKNAME check-env-LAADS_TOKEN

cdk:
	test -f node_modules/.bin/cdk || \
	yarn add cdk

venv:
	test -d venv || virtualenv venv
	source venv/bin/activate

install: cdk venv
	source venv/bin/activate
	pip install . --no-binary :.:

dev: cdk venv
	source venv/bin/activate
	pip install -e .[extra] --no-binary :.:

clean:
	rm -fr venv
	rm -fr dist
	rm -fr cdk.out 
	rm -fr node_modules
	find -iname "*.pyc" -delete

synth: check-env
	source venv/bin/activate
	yarn cdk synth

diff: check-env
	source venv/bin/activate
	yarn cdk diff

deploy: check-env
	source venv/bin/activate
	yarn cdk deploy

fresh: clean install

freshdev: clean dev
