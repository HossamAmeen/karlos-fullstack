# Usage: make deploy [ENV=staging|production] [ARGS="--full"]
ENV ?= staging
ARGS ?=

.PHONY: deploy deploy-staging deploy-production verify

deploy:
	./deploy/deploy.sh $(ENV) $(ARGS)

deploy-staging:
	./deploy/deploy.sh staging $(ARGS)

deploy-production:
	./deploy/deploy.sh production $(ARGS)

verify:
	./deploy/deploy.sh $(ENV) --verify
