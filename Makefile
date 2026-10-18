# Usage: make deploy [ENV=staging|production] [ARGS="--full"]
#        make restart [ENV=staging|production]   (backend: pull, migrate, restart)
#        make errors [ENV=...] [N=100]           (backend errors only; errors-nginx for nginx)
#        make logs [ENV=...] / make logs-f       (backend logs / follow)
ENV ?= staging
ARGS ?=

.PHONY: errors errors-nginx logs logs-f deploy deploy-staging deploy-production verify restart logs-service logs-service-follow logs-nginx logs-nginx-follow

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

logs: logs-service

logs-f: logs-service-follow

errors errors-nginx logs-service logs-service-follow logs-nginx logs-nginx-follow:
	$(MAKE) -C deploy $@ ENV=$(ENV)
