.ONESHELL:
SHELL := /bin/bash
REQUIRED_BINS := yarn virtualenv pip
$(foreach bin,$(REQUIRED_BINS),\
    $(if $(shell command -v $(bin) 2> /dev/null),$(info Found `$(bin)`),$(error Please install `$(bin)`)))

.PHONY: check-envfile check-env-% check-env cdk venv dev clean synth diff deploy fresh freshdev

check-envfile:
	[[ ! -f env.sh ]] && echo "Please copy and edit env.sh.sample to env.sh" && exit 1

check-env-%:
	[[ ! -v ${*} ]] && echo "Environment variable $* not set" && exit 1

check-env: check-envfile check-env-HLS_STACKNAME check-env-HLS_LAADS_TOKEN

cdk:
	test -f node_modules/.bin/cdk || \
	yarn add cdk

venv:
	test -d venv || virtualenv venv

install: check-env cdk venv
	source venv/bin/activate
	pip install . --no-binary :.:

dev: check-env cdk venv
	source venv/bin/activate
	pip install -e .[test] --no-binary :.:

clean:
	rm -fr venv
	rm -fr dist
	rm -fr cdk.out 
	rm -fr node_modules
	find -iname "*.pyc" -delete
	rm package.json
	rm yarn.lock
	rm -fr *.egg-info

synth: check-env
	source env.sh
	yarn cdk synth

diff: check-env
	source env.sh
	yarn cdk diff

deploy: check-env
	source env.sh
	yarn cdk deploy

fresh: clean dev synth

