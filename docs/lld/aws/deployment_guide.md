# ansari-whatsapp AWS Deployment Guide

This guide walks you through deploying the ansari-whatsapp microservice to AWS using the same infrastructure pattern as ansari-backend.

***TOC:***

- [ansari-whatsapp AWS Deployment Guide](#ansari-whatsapp-aws-deployment-guide)
  - [Architecture Overview](#architecture-overview)
    - [The Deployment Pipeline](#the-deployment-pipeline)
    - [Service Architecture](#service-architecture)
  - [AWS Resources](#aws-resources)
    - [Resources We'll Reuse from ansari-backend](#resources-well-reuse-from-ansari-backend)
    - [New Resources We'll Create](#new-resources-well-create)
    - [Resource Specifications](#resource-specifications)
  - [Prerequisites](#prerequisites)
  - [Deployment Steps](#deployment-steps)
    - [Step 1: Create AWS Resources](#step-1-create-aws-resources)
    - [Step 2: Configure GitHub Secrets](#step-2-configure-github-secrets)
    - [Step 3: First Deployment](#step-3-first-deployment)
    - [Step 4: Update Meta Webhook URL](#step-4-update-meta-webhook-url)
  - [Environment Configuration](#environment-configuration)
    - [Environment Variables by Category](#environment-variables-by-category)
      - [Backend Integration](#backend-integration)
      - [Meta/WhatsApp Credentials](#metawhatsapp-credentials)
      - [Application Settings](#application-settings)
      - [Operational Settings](#operational-settings)
    - [SSM Parameter Store Structure](#ssm-parameter-store-structure)
  - [Validation](#validation)
    - [Pre-Deployment Checklist](#pre-deployment-checklist)


---

## Architecture Overview

### The Deployment Pipeline

```
Developer pushes to GitHub (main/develop)
            ↓
    GitHub Actions Workflow triggers
            ↓
    Build Docker image with uv
            ↓
    Tag with git commit SHA
            ↓
    Push to Amazon ECR
            ↓
    Deploy to AWS App Runner
            ↓
    Load secrets from SSM Parameter Store
            ↓
    Service goes live! 🚀
```

### Service Architecture

```
Meta WhatsApp API
        ↓
    [Webhook Request]
        ↓
AWS App Runner (ansari-whatsapp)
        ↓
    [API Calls]
        ↓
AWS App Runner (ansari-backend)
        ↓
    [MongoDB, Claude API, etc.]
```

**Key Points:**
- ansari-whatsapp is a **client service** - it doesn't need its own database
- It communicates with ansari-backend via HTTP API calls
- Both services deployed independently on AWS App Runner
- Secrets managed via AWS Systems Manager Parameter Store
- **AWS Region**: us-west-2 (Oregon)
- **AWS Account ID**: AWS_ACCOUNT_ID

---

## AWS Resources

### Resources We'll Reuse from ansari-backend

These IAM roles already exist and we'll use them:

| Resource | Purpose | Notes |
|----------|---------|-------|
| `CustomAppRunnerServiceRole` | Allows App Runner to pull Docker images from ECR | Already has ECR access policy attached |
| `CustomAppRunnerInstanceRole` | Allows your app to read secrets from SSM | Already has Parameter Store access |
| `app-runner-github-actions-user` | GitHub Actions credentials for AWS | Already has ECR push and App Runner deploy permissions |

### New Resources We'll Create

| Resource | Name | Purpose |
|----------|------|---------|
| ECR Repository | `ansari-whatsapp` | Store Docker images |
| App Runner Service (Staging) | `ansari-staging-whatsapp` | Staging environment |
| App Runner Service (Production) | `ansari-production-whatsapp` | Production environment |
| SSM Parameters | `/app-runtime/ansari-whatsapp/staging/*` | Staging environment variables |
| SSM Parameters | `/app-runtime/ansari-whatsapp/production/*` | Production environment variables |

### Resource Specifications

**App Runner Configuration:**
- **Region**: us-west-2 (Oregon) - same as ansari-backend
- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Port**: 8001
- **Health Check**: `GET /` (returns `{"status": "ok"}`)
- **Auto-scaling**: Enabled (default)
- **Min/Max Instances**: 1/25 (default)

**Why These Specs?**
- **1 vCPU + 2GB**: ansari-whatsapp is lightweight - just webhook handling and HTTP forwarding
- **Port 8001**: Distinguishes from ansari-backend (8000)
- **us-west-2**: Same region as backend for low latency communication

---

## Prerequisites

Before you begin, ensure you have:

- [x] AWS CLI installed and configured (`aws --version`)
- [x] AWS credentials with admin access (or permissions for ECR, App Runner, SSM, IAM)
- [x] AWS profile named `ansari` configured (or adjust commands to use your profile)
- [x] Access to the ansari-project GitHub organization
- [x] Admin access to the ansari-whatsapp repository settings (to add secrets)
- [x] The existing IAM role ARNs from ansari-backend:
  - `CustomAppRunnerServiceRole` ARN
  - `CustomAppRunnerInstanceRole` ARN
  - `app-runner-github-actions-user` access keys

**To Get Existing Role ARNs:**
```bash
# Get Service Role ARN
aws iam get-role --role-name CustomAppRunnerServiceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2

# Get Instance Role ARN
aws iam get-role --role-name CustomAppRunnerInstanceRole \
  --query 'Role.Arn' --output text \
  --profile ansari --region us-west-2
```

---

## Deployment Steps

### Step 1: Create AWS Resources

Follow the detailed commands in [aws-cli.md](./aws-cli.md) to create:
1. ECR repository for ansari-whatsapp
2. SSM parameters for staging environment
3. SSM parameters for production environment

**Quick Summary:**
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name ansari-whatsapp \
  --profile ansari --region us-west-2

# 2. Add SSM parameters (see aws-cli.md for complete list)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/backend-server-url" \
  --value "https://staging-api.ansari.chat" \
  --type SecureString \
  --profile ansari --region us-west-2
```

### Step 2: Configure GitHub Secrets

Follow the detailed instructions in [github_actions_setup.md](./github_actions_setup.md) to add:
- AWS credentials (reuse from ansari-backend)
- ECR registry URL
- App Runner service names
- IAM role ARNs
- Environment-specific settings

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `SERVICE_ROLE_ARN`
- `INSTANCE_ROLE_ARN`

**Required Variables:**
- `SSM_ROOT`

### Step 3: First Deployment

**For Staging:**
1. Push to `develop` branch (or merge a PR to develop)
2. GitHub Actions will automatically trigger `deploy-staging.yml`
3. Monitor the workflow in GitHub Actions tab
4. Wait for deployment to complete (~5-10 minutes)
5. App Runner URL will be output in the workflow logs

**For Production:**
1. Push to `main` branch (or manually trigger workflow)
2. GitHub Actions will automatically trigger `deploy-production.yml`
3. Monitor and wait for completion
4. Note the production App Runner URL

### Step 4: Get App Runner URL for Cloudflare

After successful deployment, you need to get the App Runner URL to configure Cloudflare CNAME records.

**Method 1: From AWS Console**
1. Go to: https://console.aws.amazon.com/apprunner/home?region=us-west-2
2. Click on `ansari-staging-whatsapp` or `ansari-production-whatsapp`
3. Copy the **Default domain** (e.g., `xxxxxxxxxx.us-west-2.awsapprunner.com`)

**Method 2: From AWS CLI**
```bash
# For staging
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-staging-whatsapp/YOUR_SERVICE_ID \
  --query 'Service.ServiceUrl' \
  --output text \
  --region us-west-2

# For production
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-production-whatsapp/YOUR_SERVICE_ID \
  --query 'Service.ServiceUrl' \
  --output text \
  --region us-west-2
```

**Method 3: From GitHub Actions Logs**
After deployment workflow completes, check the final step "App Runner URL" in the logs.

**Send to Your Co-Developer:**
```
App Runner URL: xxxxxxxxxx.us-west-2.awsapprunner.com
Subdomain: whatsapp (or your preferred subdomain)
Environment: staging (or production)
Port: 8001
```

They will configure Cloudflare CNAME record:
```
Type: CNAME
Name: whatsapp
Target: xxxxxxxxxx.us-west-2.awsapprunner.com
Proxy: Enabled (orange cloud in Cloudflare)
```

### Step 5: Update Meta Webhook URL

Once Cloudflare is configured, update Meta to use the custom domain:

**Current Setup (Local Development):**
- Webhook URL: `https://<ZROK_TOKEN>.share.zrok.io/whatsapp/v2`

**New Setup (Production via Cloudflare):**
- Webhook URL: `https://whatsapp.ansari.chat/whatsapp/v2`
- Webhook URL for staging: `https://staging-whatsapp.ansari.chat/whatsapp/v2`

**How to Update:**
1. Go to [Meta App Dashboard](https://developers.facebook.com/apps/)
2. Select your WhatsApp app
3. Navigate to WhatsApp → Configuration
4. Update Callback URL to: `https://whatsapp.ansari.chat/whatsapp/v2`
5. Verify token should remain the same (stored in SSM)
6. Click "Verify and Save"

**Testing:**
- Send a WhatsApp message to your business number
- Check App Runner logs in AWS Console
- Verify response is sent back to WhatsApp

---

## Environment Configuration

### Environment Variables by Category

The ansari-whatsapp service needs these environment variables, all stored in AWS SSM Parameter Store:

#### Backend Integration
| Variable | Staging Value | Production Value |
|----------|---------------|------------------|
| `BACKEND_SERVER_URL` | `https://staging-api.ansari.chat` | `https://api.ansari.chat` |
| `DEPLOYMENT_TYPE` | `staging` | `production` |

#### Meta/WhatsApp Credentials
| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `META_ACCESS_TOKEN_FROM_SYS_USER` | System user access token | Meta Business Dashboard |
| `META_BUSINESS_PHONE_NUMBER_ID` | WhatsApp business phone ID | Meta WhatsApp Settings |
| `META_WEBHOOK_VERIFY_TOKEN` | Webhook verification token | You generate this (secure random string) |
| `META_API_VERSION` | WhatsApp API version | Currently `v22.0` |

#### Application Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_CHAT_RETENTION_HOURS` | `3` | How long to keep chat history |
| `WHATSAPP_MESSAGE_AGE_THRESHOLD_SECONDS` | `86400` | Reject messages older than 24 hours |
| `WHATSAPP_UNDER_MAINTENANCE` | `False` | Enable maintenance mode |

#### Operational Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `ALWAYS_RETURN_OK_TO_META` | `True` | Always return HTTP 200 to Meta (required!) |
| `LOGGING_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `ORIGINS` | Auto-configured | CORS allowed origins |

### SSM Parameter Store Structure

**Staging Environment:**
```
/app-runtime/ansari-whatsapp/staging/
├── backend-server-url
├── deployment-type
├── meta-access-token-from-sys-user
├── meta-business-phone-number-id
├── meta-webhook-verify-token
├── meta-api-version
├── whatsapp-chat-retention-hours
├── whatsapp-message-age-threshold-seconds
├── whatsapp-under-maintenance
├── always-return-ok-to-meta
└── logging-level
```

**Production Environment:**
```
/app-runtime/ansari-whatsapp/production/
├── (same structure as staging)
```

**Note:** Parameter names use hyphens (not underscores) in SSM paths, but App Runner converts them to underscores for environment variables.

---

## Validation

### Pre-Deployment Checklist

Before deploying to production, verify:

- [ ] All SSM parameters are set correctly
- [ ] GitHub secrets are configured
- [ ] Staging deployment successful and tested
- [ ] App Runner service health checks passing
- [ ] Test messages sent and received in staging
- [ ] ansari-backend is accessible from App Runner
- [ ] Meta webhook URL updated (staging)
- [ ] No hardcoded secrets in code

