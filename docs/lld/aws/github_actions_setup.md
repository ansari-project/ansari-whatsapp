# GitHub Actions Setup for ansari-whatsapp

This guide explains how to configure GitHub Secrets and understand the deployment workflows.

***TOC:***

- [GitHub Actions Setup for ansari-whatsapp](#github-actions-setup-for-ansari-whatsapp)
  - [GitHub Secrets Configuration](#github-secrets-configuration)
    - [Where to Add Secrets](#where-to-add-secrets)
    - [Required Secrets](#required-secrets)
      - [AWS Credentials (Reuse from ansari-backend)](#aws-credentials-reuse-from-ansari-backend)
      - [IAM Role ARNs](#iam-role-arns)
      - [SSM Parameter Store Paths](#ssm-parameter-store-paths)
  - [Workflow Overview](#workflow-overview)
    - [1. Staging Deployment (`.github/workflows/deploy-staging.yml`)](#1-staging-deployment-githubworkflowsdeploy-stagingyml)
    - [2. Production Deployment (`.github/workflows/deploy-production.yml`)](#2-production-deployment-githubworkflowsdeploy-productionyml)
  - [How Deployments Work](#how-deployments-work)
    - [The Deployment Pipeline](#the-deployment-pipeline)
    - [Environment Variable Injection](#environment-variable-injection)
    - [Docker Image Tagging Strategy](#docker-image-tagging-strategy)
    - [Deployment Timing](#deployment-timing)
  - [Workflow File Structure](#workflow-file-structure)
    - [Staging Workflow Highlights](#staging-workflow-highlights)
    - [Key Workflow Parameters](#key-workflow-parameters)
  - [Manual Deployment Trigger](#manual-deployment-trigger)
    - [From GitHub UI](#from-github-ui)
    - [Use Cases for Manual Triggers](#use-cases-for-manual-triggers)
  - [Monitoring Deployments](#monitoring-deployments)
    - [GitHub Actions UI](#github-actions-ui)
    - [AWS Console](#aws-console)
    - [CloudWatch Logs](#cloudwatch-logs)


---

## GitHub Secrets Configuration

GitHub Secrets store sensitive credentials that the CI/CD workflows use to deploy to AWS.

### Where to Add Secrets

1. Go to your repository: `https://github.com/ansari-project/ansari-whatsapp`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### Required Secrets

#### AWS Credentials (Reuse from ansari-backend)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AWS_ACCESS_KEY_ID` | Access key for `app-runner-github-actions-user` | From ansari-backend GitHub Secrets (or AWS IAM Console) |
| `AWS_SECRET_ACCESS_KEY` | Secret key for `app-runner-github-actions-user` | From ansari-backend GitHub Secrets (or AWS IAM Console) |
| `AWS_REGION` | AWS region where resources are deployed | `us-west-2` |

**Note:** These credentials are from the IAM user `app-runner-github-actions-user` created for ansari-backend. The user has permissions for ECR push and App Runner deployments.

#### IAM Role ARNs

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `SERVICE_ROLE_ARN` | ARN of `CustomAppRunnerServiceRole` | `aws iam get-role --role-name CustomAppRunnerServiceRole --query 'Role.Arn' --output text` |
| `INSTANCE_ROLE_ARN` | ARN of `CustomAppRunnerInstanceRole` | `aws iam get-role --role-name CustomAppRunnerInstanceRole --query 'Role.Arn' --output text` |

**Example ARN format:**
- Service Role: `arn:aws:iam::123456789012:role/CustomAppRunnerServiceRole`
- Instance Role: `arn:aws:iam::123456789012:role/CustomAppRunnerInstanceRole`

#### SSM Parameter Store Paths

| Secret Name | GitHub Environment | Value | Description |
|-------------|-------------------|-------|-------------|
| `SSM_ROOT` | `gh-actions-staging-env` | `/app-runtime/ansari-whatsapp/staging/` | Path prefix for staging environment variables |
| `SSM_ROOT` | `gh-actions-production-env` | `/app-runtime/ansari-whatsapp/production/` | Path prefix for production environment variables |

**Important:** Include the trailing slash!

**Note:** The same secret `SSM_ROOT` is used, but the value differs based on the GitHub Actions environment (`gh-actions-staging-env` or `gh-actions-production-env`). Set the appropriate value for each environment in GitHub repository settings.

---

## Workflow Overview

Two GitHub Actions workflows handle deployments:

### 1. Staging Deployment (`.github/workflows/deploy-staging.yml`)

**Triggers:**
- Automatic: Push to `develop` branch
- Manual: Workflow dispatch from GitHub Actions UI

**What it does:**
1. Builds Docker image with uv
2. Tags image with git commit SHA
3. Pushes to ECR `ansari-whatsapp` repository
4. Deploys to `ansari-staging-whatsapp` App Runner service
5. Injects environment variables from SSM path: `/app-runtime/ansari-whatsapp/staging/*`

**Typical use case:**
- Merge a PR to `develop` branch
- Automatically deploys to staging
- Test the changes before promoting to production

### 2. Production Deployment (`.github/workflows/deploy-production.yml`)

**Triggers:**
- Automatic: Push to `main` branch
- Manual: Workflow dispatch from GitHub Actions UI

**What it does:**
1. Same build and push process as staging
2. Deploys to `ansari-production-whatsapp` App Runner service
3. Injects environment variables from SSM path: `/app-runtime/ansari-whatsapp/production/*`

**Typical use case:**
- Merge `develop` into `main` after testing
- Automatically deploys to production
- Real users receive the update

---

## How Deployments Work

### The Deployment Pipeline

```
1. Developer pushes to develop/main
            ↓
2. GitHub Actions workflow triggers
            ↓
3. Checkout repository code
            ↓
4. Configure AWS credentials (using secrets)
            ↓
5. Login to Amazon ECR
            ↓
6. Build Docker image
   - Uses Dockerfile with uv
   - Tags with git SHA: <ecr-url>/ansari-whatsapp:<sha>
            ↓
7. Push image to ECR
            ↓
8. Deploy to App Runner
   - Uses awslabs/amazon-app-runner-deploy action
   - References SSM parameters for env vars
   - Waits up to 20 minutes for deployment
            ↓
9. Output App Runner URL
```

### Environment Variable Injection

The workflows use a clever pattern to inject environment variables from SSM:

```yaml
env:
  BACKEND_SERVER_URL: ${{ format('{0}{1}', secrets.SSM_ROOT, 'backend-server-url') }}
```

This concatenates:
- `SSM_ROOT` = `/app-runtime/ansari-whatsapp/staging/` (if we're in the staging environment)
- `'backend-server-url'` = parameter name

Result: `/app-runtime/ansari-whatsapp/staging/backend-server-url`

App Runner reads this path from SSM and injects the value as `BACKEND_SERVER_URL` environment variable.

### Docker Image Tagging Strategy

Images are tagged with the git commit SHA:

```
<account-id>.dkr.ecr.us-west-2.amazonaws.com/ansari-whatsapp:a1b2c3d4
```

**Benefits:**
- Exact version tracking (which git commit is deployed)
- Easy rollbacks (just redeploy an older SHA)
- No "latest" tag confusion

### Deployment Timing

**Staging deployment:**
- Build time: ~2-3 minutes
- Push to ECR: ~30 seconds
- App Runner deployment: ~5-7 minutes
- **Total: ~8-10 minutes**

**Production deployment:**
- Same timing as staging
- **Total: ~8-10 minutes**

**Why so long?**
- App Runner provisions new instances
- Health checks must pass before switching traffic
- Zero-downtime deployment (old version runs until new version is healthy)

---

## Workflow File Structure

### Staging Workflow Highlights

```yaml
name: Staging Deployment (AWS App Runner)

on:
  push:
    branches:
      - develop
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: staging-aws  # GitHub Environment for approval gates (optional)

    steps:
      # ... build and push steps ...

      - name: Deploy to App Runner
        uses: awslabs/amazon-app-runner-deploy@main
        with:
          service: ansari-staging-whatsapp
          image: ${{ steps.build-image.outputs.image }}
          access-role-arn: ${{ secrets.SERVICE_ROLE_ARN }}
          instance-role-arn: ${{ secrets.INSTANCE_ROLE_ARN }}
          region: ${{ secrets.AWS_REGION }}
          cpu: 1
          memory: 2
          port: 8001
          wait-for-service-stability-seconds: 1200
```

### Key Workflow Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `service` | `ansari-staging-whatsapp` or `ansari-production-whatsapp` | App Runner service name |
| `cpu` | `1` | Number of vCPUs (1 = 1 vCPU) |
| `memory` | `2` | Memory in GB |
| `port` | `8001` | Container port (must match Dockerfile EXPOSE) |
| `wait-for-service-stability-seconds` | `1200` | Max wait time (20 minutes) |
| `access-role-arn` | From `SERVICE_ROLE_ARN` secret | Allows App Runner to pull from ECR |
| `instance-role-arn` | From `INSTANCE_ROLE_ARN` secret | Allows container to read SSM |

---

## Manual Deployment Trigger

You can manually trigger deployments without pushing code:

### From GitHub UI

1. Go to **Actions** tab in the repository
2. Select the workflow (Staging or Production Deployment)
3. Click **Run workflow**
4. Select the branch
5. Click **Run workflow** button

### Use Cases for Manual Triggers

- **Environment variable update**: You changed an SSM parameter and want to redeploy
- **Emergency rollback**: Manually trigger an older commit
- **Testing**: Deploy a feature branch to staging without merging
- **Hotfix**: Deploy directly to production (use with caution!)

---

## Monitoring Deployments

### GitHub Actions UI

1. Go to **Actions** tab
2. Click on the running workflow
3. Expand steps to see detailed logs
4. Look for errors in red

**Key steps to monitor:**
- ✅ Build, tag, and push image to ECR
- ✅ Deploy to App Runner
- ✅ App Runner URL output

### AWS Console

1. Go to AWS Console → App Runner
2. Select your service (`ansari-staging-whatsapp` or `ansari-production-whatsapp`)
3. Click **Deployments** tab
4. See deployment status and history

**Deployment statuses:**
- 🔵 **In progress**: Deployment is running
- 🟢 **Successful**: Deployment completed, service is healthy
- 🔴 **Failed**: Deployment failed (check logs)
- 🟡 **Rolled back**: Deployment failed and was automatically rolled back

### CloudWatch Logs

1. AWS Console → App Runner → Your Service
2. Click **Logs** tab
3. See application logs in real-time

**Log groups:**
- `/aws/apprunner/ansari-whatsapp/staging/service`
- `/aws/apprunner/ansari-whatsapp/production/service`

