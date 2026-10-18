# Usage: make deploy [ENV=staging|production] [ARGS="--full"]
#        make restart [ENV=staging|production]   (backend: pull, migrate, restart)
ENV ?= staging
ARGS ?=

.PHONY: deploy deploy-staging deploy-production verify restart logs-service logs-service-follow logs-nginx logs-nginx-follow

deploy:
	./deploy/deploy.sh $(ENV) $(ARGS)

deploy-staging:
	./deploy/deploy.sh staging $(ARGS)

deploy-production:
	./deploy/deploy.sh production $(ARGS)

verify:
	./deploy/deploy.sh $(ENV) --verify

restart:
	cd deploy && python3 restart.py $(ENV)

logs-service logs-service-follow logs-nginx logs-nginx-follow:
	$(MAKE) -C deploy $@ ENV=$(ENV)
