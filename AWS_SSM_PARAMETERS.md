# AWS SSM Parameter Store Commands

This file contains all AWS SSM commands to configure parameters for both ansari-whatsapp and ansari-backend services.

**Instructions:**
1. Replace placeholder values with actual values from your `.env` files
2. Run these commands using AWS CLI with the `ansari` profile
3. Commands are separated by environment (staging/production)

***TOC:***

- [AWS SSM Parameter Store Commands](#aws-ssm-parameter-store-commands)
  - [ansari-whatsapp Parameters](#ansari-whatsapp-parameters)
    - [Staging Environment](#staging-environment)
    - [Production Environment](#production-environment)
  - [ansari-backend Parameters](#ansari-backend-parameters)
    - [Staging Environment](#staging-environment-1)
    - [Production Environment](#production-environment-1)
  - [Notes](#notes)


---

## ansari-whatsapp Parameters

### Staging Environment

```bash
aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/deployment-type" --value "staging" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/backend-server-url" --value "YOUR_STAGING_BACKEND_URL" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/whatsapp-service-api-key" --value "YOUR_GENERATED_API_KEY" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/origins" --value "YOUR_CORS_ORIGINS" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/meta-api-version" --value "v22.0" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/meta-business-phone-number-id" --value "YOUR_META_PHONE_ID" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" --value "YOUR_META_ACCESS_TOKEN" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/meta-webhook-verify-token" --value "YOUR_WEBHOOK_VERIFY_TOKEN" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/meta-app-secret" --value "YOUR_META_APP_SECRET" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/whatsapp-under-maintenance" --value "False" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/whatsapp-chat-retention-hours" --value "3" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/whatsapp-message-age-threshold-seconds" --value "86400" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/always-return-ok-to-meta" --value "True" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/logging-level" --value "DEBUG" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/mock-ansari-client" --value "False" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/staging/mock-meta-api" --value "False" --type "SecureString" --overwrite
```

### Production Environment

```bash
aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/deployment-type" --value "production" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/backend-server-url" --value "YOUR_PRODUCTION_BACKEND_URL" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/whatsapp-service-api-key" --value "YOUR_GENERATED_API_KEY" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/origins" --value "YOUR_CORS_ORIGINS" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/meta-api-version" --value "v22.0" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/meta-business-phone-number-id" --value "YOUR_META_PHONE_ID" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/meta-access-token-from-sys-user" --value "YOUR_META_ACCESS_TOKEN" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/meta-webhook-verify-token" --value "YOUR_WEBHOOK_VERIFY_TOKEN" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/meta-app-secret" --value "YOUR_META_APP_SECRET" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/whatsapp-under-maintenance" --value "False" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/whatsapp-chat-retention-hours" --value "3" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/whatsapp-message-age-threshold-seconds" --value "86400" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/always-return-ok-to-meta" --value "True" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/logging-level" --value "INFO" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/mock-ansari-client" --value "False" --type "SecureString" --overwrite

aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-whatsapp/production/mock-meta-api" --value "False" --type "SecureString" --overwrite
```

---

## ansari-backend Parameters

### Staging Environment

```bash
aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-backend/staging/whatsapp-service-api-key" --value "YOUR_GENERATED_API_KEY" --type "SecureString" --overwrite

```

### Production Environment

```bash
aws ssm put-parameter --profile ansari --name "/app-runtime/ansari-backend/production/whatsapp-service-api-key" --value "YOUR_GENERATED_API_KEY" --type "SecureString" --overwrite

```

---

## Notes

- **WHATSAPP_SERVICE_API_KEY**: MUST be identical in both ansari-whatsapp and ansari-backend
- **META_APP_SECRET**: Only added to ansari-whatsapp (new security feature)
- Replace ALL `YOUR_*` placeholders with actual values from `.env` files
- SecureString parameters are encrypted at rest in AWS
- Use `--overwrite` flag to update existing parameters
