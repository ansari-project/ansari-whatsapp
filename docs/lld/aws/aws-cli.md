
- [AWS CLI Commands for ansari-whatsapp Deployment](#aws-cli-commands-for-ansari-whatsapp-deployment)
  - [Prerequisites](#prerequisites)
  - [1. Create ECR Repository](#1-create-ecr-repository)
  - [2. Create Staging Environment Variables (SSM Parameters)](#2-create-staging-environment-variables-ssm-parameters)
    - [Backend Integration](#backend-integration)
    - [Meta/WhatsApp Credentials](#metawhatsapp-credentials)
    - [Application Settings](#application-settings)
    - [Operational Settings](#operational-settings)
  - [3. Create Production Environment Variables (SSM Parameters)](#3-create-production-environment-variables-ssm-parameters)
    - [Quick Production Setup](#quick-production-setup)
  - [4. Verify SSM Parameters](#4-verify-ssm-parameters)
    - [List All Staging Parameters](#list-all-staging-parameters)
    - [List All Production Parameters](#list-all-production-parameters)
    - [View Specific Parameter (with decryption)](#view-specific-parameter-with-decryption)
  - [5. Update SSM Parameter (if needed)](#5-update-ssm-parameter-if-needed)
  - [6. Get Existing IAM Role ARNs](#6-get-existing-iam-role-arns)
    - [Get Service Role ARN](#get-service-role-arn)
    - [Get Instance Role ARN](#get-instance-role-arn)
  - [7. Verify IAM Policies (Optional)](#7-verify-iam-policies-optional)
  - [8. Delete Resources (Cleanup Commands)](#8-delete-resources-cleanup-commands)
    - [Delete ECR Repository](#delete-ecr-repository)
    - [Delete SSM Parameters](#delete-ssm-parameters)
    - [Delete App Runner Service](#delete-app-runner-service)
  - [Quick Reference](#quick-reference)
    - [Common Tasks](#common-tasks)
  - [Notes](#notes)


# AWS CLI Commands for ansari-whatsapp Deployment

This file contains all AWS CLI commands needed to set up the infrastructure for ansari-whatsapp.

## Prerequisites

- AWS CLI installed and configured
- AWS profile named `ansari` (or replace with your profile name)
- Admin permissions (or permissions for ECR, SSM, App Runner, IAM)
- Region: `us-west-2` (Oregon)

## 1. Create ECR Repository

This repository will store Docker images for ansari-whatsapp.

**Command to match ansari-backend repository settings:**

```bash
aws ecr create-repository \
  --repository-name ansari-whatsapp \
  --region us-west-2 \
  --image-tag-mutability MUTABLE \
  --image-scanning-configuration scanOnPush=false \
  --encryption-configuration encryptionType=AES256 \
  --profile ansari
```

**Expected Output:**
```json
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-west-2:AWS_ACCOUNT_ID:repository/ansari-whatsapp",
        "registryId": "AWS_ACCOUNT_ID",
        "repositoryName": "ansari-whatsapp",
        "repositoryUri": "AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/ansari-whatsapp",
        "createdAt": "2025-11-18T17:55:11.647000+02:00",
        "imageTagMutability": "MUTABLE",
        "imageScanningConfiguration": {
            "scanOnPush": false
        },
        "encryptionConfiguration": {
            "encryptionType": "AES256"
        }
    }
}
```

**Save the `repositoryUri`** - you'll need it for GitHub Secrets!

**Verify Repository Creation:**
```bash
aws ecr describe-repositories --repository-names ansari-whatsapp --region us-west-2
```

---

## 2. Create Staging Environment Variables (SSM Parameters)

These parameters store environment variables for the staging environment.

### Backend Integration

```bash
# Backend API URL
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/backend-server-url" \
  --value "https://staging-api.ansari.chat" \
  --type SecureString \
  --profile ansari --region us-west-2

# Deployment type
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/deployment-type" \
  --value "staging" \
  --type String \
  --profile ansari --region us-west-2
```

### Meta/WhatsApp Credentials

```bash
# Meta Access Token (System User)
# Get this from: https://business.facebook.com/settings/system-users
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
  --value "EAAC..." \
  --type SecureString \
  --profile ansari --region us-west-2

# Meta Business Phone Number ID
# Get this from: WhatsApp Business App Dashboard
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-business-phone-number-id" \
  --value "123456789012345" \
  --type SecureString \
  --profile ansari --region us-west-2

# Meta Webhook Verify Token
# This is a token YOU create (secure random string)
# It's used by Meta to verify your webhook endpoint
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-webhook-verify-token" \
  --value "your-secure-random-token-here" \
  --type SecureString \
  --profile ansari --region us-west-2

# Meta API Version
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-api-version" \
  --value "v22.0" \
  --type String \
  --profile ansari --region us-west-2
```

### Application Settings

```bash
# Host (bind to all interfaces)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/host" \
  --value "0.0.0.0" \
  --type String \
  --profile ansari --region us-west-2

# Port
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/port" \
  --value "8001" \
  --type String \
  --profile ansari --region us-west-2

# Chat retention hours (how long to keep chat history)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/whatsapp-chat-retention-hours" \
  --value "3" \
  --type String \
  --profile ansari --region us-west-2

# Message age threshold (reject messages older than this)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/whatsapp-message-age-threshold-seconds" \
  --value "86400" \
  --type String \
  --profile ansari --region us-west-2

# Maintenance mode
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/whatsapp-under-maintenance" \
  --value "False" \
  --type String \
  --profile ansari --region us-west-2
```

### Operational Settings

```bash
# Always return OK to Meta (required for webhooks!)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/always-return-ok-to-meta" \
  --value "True" \
  --type String \
  --profile ansari --region us-west-2

# Logging level
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/logging-level" \
  --value "INFO" \
  --type String \
  --profile ansari --region us-west-2

# CORS origins (auto-configured based on deployment type, but can override)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/origins" \
  --value "https://staging.ansari.chat,https://web.whatsapp.com" \
  --type String \
  --profile ansari --region us-west-2
```

---

## 3. Create Production Environment Variables (SSM Parameters)

Same as staging, but with production values.

### Quick Production Setup

```bash
# Backend Integration
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/backend-server-url" \
  --value "https://api.ansari.chat" \
  --type SecureString \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/deployment-type" \
  --value "production" \
  --type String \
  --profile ansari --region us-west-2

# Meta/WhatsApp Credentials (use PRODUCTION credentials!)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/meta-access-token-from-sys-user" \
  --value "EAAC..." \
  --type SecureString \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/meta-business-phone-number-id" \
  --value "123456789012345" \
  --type SecureString \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/meta-webhook-verify-token" \
  --value "your-production-verify-token" \
  --type SecureString \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/meta-api-version" \
  --value "v22.0" \
  --type String \
  --profile ansari --region us-west-2

# Application Settings (same as staging)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/host" \
  --value "0.0.0.0" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/port" \
  --value "8001" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/whatsapp-chat-retention-hours" \
  --value "3" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/whatsapp-message-age-threshold-seconds" \
  --value "86400" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/whatsapp-under-maintenance" \
  --value "False" \
  --type String \
  --profile ansari --region us-west-2

# Operational Settings
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/always-return-ok-to-meta" \
  --value "True" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/logging-level" \
  --value "INFO" \
  --type String \
  --profile ansari --region us-west-2

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/origins" \
  --value "https://ansari.chat,https://web.whatsapp.com" \
  --type String \
  --profile ansari --region us-west-2
```

---

## 4. Verify SSM Parameters

Check that all parameters were created correctly.

### List All Staging Parameters

```bash
aws ssm get-parameters-by-path \
  --path "/app-runtime/ansari-whatsapp/staging" \
  --profile ansari --region us-west-2
```

### List All Production Parameters

```bash
aws ssm get-parameters-by-path \
  --path "/app-runtime/ansari-whatsapp/production" \
  --profile ansari --region us-west-2
```

### View Specific Parameter (with decryption)

```bash
aws ssm get-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
  --with-decryption \
  --profile ansari --region us-west-2
```

---

## 5. Update SSM Parameter (if needed)

If you need to change a parameter value:

```bash
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/logging-level" \
  --value "DEBUG" \
  --type String \
  --overwrite \
  --profile ansari --region us-west-2
```

**Note:** After updating a parameter, you need to **redeploy** the App Runner service for changes to take effect.

---

## 6. Get Existing IAM Role ARNs

You'll need these ARNs for GitHub Secrets.

### Get Service Role ARN

```bash
aws iam get-role --role-name CustomAppRunnerServiceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2
```

**Expected Output:**
```
arn:aws:iam::<account-id>:role/CustomAppRunnerServiceRole
```

### Get Instance Role ARN

```bash
aws iam get-role --role-name CustomAppRunnerInstanceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2
```

**Expected Output:**
```
arn:aws:iam::<account-id>:role/CustomAppRunnerInstanceRole
```

---

## 7. Verify IAM Policies (Optional)

Check that the instance role has SSM Parameter Store access.

```bash
aws iam list-role-policies --role-name CustomAppRunnerInstanceRole \
  --profile ansari --region us-west-2

aws iam get-role-policy \
  --role-name CustomAppRunnerInstanceRole \
  --policy-name CustomAccessParameters \
  --profile ansari --region us-west-2
```

**Expected Policy Document:**
The policy should allow `ssm:GetParameters` and `ssm:GetParameter` actions on the parameter paths.

See [instance-role-parameters-access.json](./instance-role-parameters-access.json) for the complete policy.

---

## 8. Delete Resources (Cleanup Commands)

**⚠️ DANGER ZONE: Only use these if you want to completely remove ansari-whatsapp infrastructure!**

### Delete ECR Repository

```bash
# Delete all images first
aws ecr delete-repository --repository-name ansari-whatsapp --force \
  --profile ansari --region us-west-2
```

### Delete SSM Parameters

```bash
# Delete staging parameters
aws ssm delete-parameters \
  --names \
    "/app-runtime/ansari-whatsapp/staging/backend-server-url" \
    "/app-runtime/ansari-whatsapp/staging/deployment-type" \
    "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
    "/app-runtime/ansari-whatsapp/staging/meta-business-phone-number-id" \
    "/app-runtime/ansari-whatsapp/staging/meta-webhook-verify-token" \
    "/app-runtime/ansari-whatsapp/staging/meta-api-version" \
  --profile ansari --region us-west-2

# Repeat for production and other parameters...
```

### Delete App Runner Service

```bash
# Get service ARN first
aws apprunner list-services --profile ansari --region us-west-2

# Delete service
aws apprunner delete-service --service-arn <service-arn> \
  --profile ansari --region us-west-2
```

---

## Quick Reference

### Common Tasks

**Update a secret:**
```bash
aws ssm put-parameter --name "<path>" --value "<new-value>" --overwrite \
  --profile ansari --region us-west-2
```

**Check current value:**
```bash
aws ssm get-parameter --name "<path>" --with-decryption \
  --profile ansari --region us-west-2
```

**List all parameters:**
```bash
aws ssm describe-parameters --profile ansari --region us-west-2
```

**Check App Runner services:**
```bash
aws apprunner list-services --profile ansari --region us-west-2
```

---

## Notes

- All SSM parameters are **encrypted** using AWS managed keys (SecureString type)
- Parameter names use **hyphens** (not underscores) but App Runner converts them to underscores for environment variables
  - Example: `/app-runtime/ansari-whatsapp/staging/meta-api-version` → `META_API_VERSION`
- Changes to SSM parameters require **redeployment** of the App Runner service to take effect
- The `CustomAppRunnerInstanceRole` must have permission to read parameters from `/app-runtime/ansari-whatsapp/*` paths
