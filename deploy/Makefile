ENV ?= staging

.PHONY: help deploy deploy-sh install config

help:
	@echo "make config      - overwrite config.yml with config.yml.example"
	@echo "make install     - install Python dependencies"
	@echo "make deploy      - deploy (ENV=staging|production, default staging)"
	@echo "make deploy-sh   - same, via the shell script"

config:
	cp config.yml.example config.yml
	@echo "config.yml replaced from config.yml.example"

install:
	pip install -r requirements.txt

deploy:
	python3 deploy.py $(ENV)

deploy-sh:
	./deploy.sh $(ENV)

restart:
	python3 restart.py $(ENV)

logs-service:
	python3 logs.py service $(ENV) -n $(or $(N),100)

logs-service-follow:
	python3 logs.py service $(ENV) -f

errors:
	python3 logs.py service $(ENV) -e -n $(or $(N),100)

errors-nginx:
	python3 logs.py nginx $(ENV) -e -n $(or $(N),100)

logs-nginx:
	python3 logs.py nginx $(ENV) -n $(or $(N),100)

logs-nginx-follow:
	python3 logs.py nginx $(ENV) -f
