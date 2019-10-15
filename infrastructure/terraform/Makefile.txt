TFVARS_FILE=$(ENV_NAME).tfvars
ifeq (,$(wildcard $(TFVARS_FILE)))
	TFVARS_FILE=sandbox/$(ENV_NAME).tfvars
endif

.PHONY: gcs_backend_creds
gcs_backend_creds:
	vault read --field=key $(ENV_NAME)/tf_backend_svc_account > gcs_backend_creds

.PHONY: deploy
deploy: tf-apply

.PHONY: tf-apply
tf-apply: tf-plan
	terraform apply plan.out

.PHONY: tf-plan
tf-plan: gcs_backend_creds
	test -n "$(ENV_NAME)" # $$ENV_NAME
	rm -f .terraform/terraform.tfstate
	terraform init -backend-config="bucket=taxfyle-$(ENV_NAME)-etl-tfstate"
	terraform plan -var-file="$(TFVARS_FILE)" -out=plan.out

.PHONY: tf-destroy
tf-destroy: gcs_backend_creds
	test -n "$(ENV_NAME)" # $$ENV_NAME
	rm -f .terraform/terraform.tfstate
	terraform init -backend-config="bucket=taxfyle-$(ENV_NAME)-etl-tfstate"
	terraform destroy -var-file="$(TFVARS_FILE)" --auto-approve