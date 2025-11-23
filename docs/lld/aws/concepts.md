# AWS Deployment Concepts

This document explains the AWS-specific concepts and architecture used in ansari-whatsapp deployment.

***TOC:***

- [AWS Deployment Concepts](#aws-deployment-concepts)
  - [Architecture Overview](#architecture-overview)
    - [Deployment Pipeline](#deployment-pipeline)
    - [Service Architecture](#service-architecture)
  - [AWS Services Used](#aws-services-used)
    - [Amazon ECR (Elastic Container Registry)](#amazon-ecr-elastic-container-registry)
    - [AWS App Runner](#aws-app-runner)
    - [AWS Systems Manager Parameter Store (SSM)](#aws-systems-manager-parameter-store-ssm)
    - [IAM (Identity and Access Management)](#iam-identity-and-access-management)
  - [IAM Roles](#iam-roles)
    - [CustomAppRunnerServiceRole](#customapprunnerservicerole)
    - [CustomAppRunnerInstanceRole](#customapprunnerinstancerole)
    - [app-runner-github-actions-user](#app-runner-github-actions-user)
  - [Environment Variable Management](#environment-variable-management)
    - [SSM Parameter Store Structure](#ssm-parameter-store-structure)
    - [How App Runner Resolves Environment Variables](#how-app-runner-resolves-environment-variables)
    - [copy-env-vars vs copy-secret-env-vars](#copy-env-vars-vs-copy-secret-env-vars)
  - [Docker Image Strategy](#docker-image-strategy)
    - [SHA-Based Tagging](#sha-based-tagging)
    - [Benefits](#benefits)
  - [Resource Specifications](#resource-specifications)
    - [App Runner Configuration](#app-runner-configuration)
    - [Why These Specs?](#why-these-specs)
  - [AWS Resources](#aws-resources)
    - [Reused Resources (from ansari-backend)](#reused-resources-from-ansari-backend)
    - [New Resources (ansari-whatsapp)](#new-resources-ansari-whatsapp)


---

## Architecture Overview

### Deployment Pipeline

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

---

## AWS Services Used

### Amazon ECR (Elastic Container Registry)

**What it is:** A Docker container registry where we store Docker images.

**In this project:**
- Repository name: `ansari-whatsapp`
- Images tagged with git commit SHA: `ansari-whatsapp:a1b2c3d4`
- GitHub Actions pushes images here after building

**Analogy:** Like Docker Hub, but private and integrated with AWS services.

### AWS App Runner

**What it is:** A fully managed service that builds and runs containerized web applications and APIs at scale.

**In this project:**
- Two services: `ansari-staging-whatsapp` and `ansari-production-whatsapp`
- Pulls Docker images from ECR
- Automatically handles load balancing, scaling, and health checks
- Provides HTTPS endpoints: `<service-id>.us-west-2.awsapprunner.com`

**Analogy:** Like Heroku or Railway, but AWS-native.

**Key Features:**
- Zero-downtime deployments (old version runs until new version is healthy)
- Auto-scaling (1-25 instances based on load)
- Built-in health checks
- CloudWatch logging integration

### AWS Systems Manager Parameter Store (SSM)

**What it is:** Secure, hierarchical storage for configuration data and secrets.

**In this project:**
- Stores environment variables as encrypted parameters
- Path structure: `/app-runtime/ansari-whatsapp/{staging|production}/*`
- App Runner reads these at startup and injects as environment variables

**Analogy:** Like a secure key-value store for secrets (similar to Vault or Doppler).

**Why use SSM instead of GitHub Secrets?**
- Secrets can be updated without redeploying code
- Centralized management across multiple services
- Encrypted at rest with AWS KMS
- Fine-grained IAM access control

### IAM (Identity and Access Management)

**What it is:** AWS's permission system for controlling who can do what with AWS resources.

**In this project:**
- Defines roles that grant specific permissions
- Three key roles: Service Role, Instance Role, GitHub Actions User
- Follows principle of least privilege (minimum necessary permissions)

---

## IAM Roles

### CustomAppRunnerServiceRole

**Purpose:** Allows App Runner to pull Docker images from ECR.

**Permissions:**
- Read access to ECR repository `ansari-whatsapp`
- Allows: `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`

**When it's used:** During deployment when App Runner needs to pull the Docker image.

### CustomAppRunnerInstanceRole

**Purpose:** Allows your running application to read secrets from SSM Parameter Store.

**Permissions:**
- Read access to SSM parameters under `/app-runtime/ansari-whatsapp/*`
- Allows: `ssm:GetParameters`, `ssm:GetParameter`

**When it's used:** At runtime when the application starts and needs environment variables.

### app-runner-github-actions-user

**Purpose:** IAM user credentials used by GitHub Actions to deploy.

**Permissions:**
- Push images to ECR repository
- Update App Runner services
- Allows: `ecr:PutImage`, `apprunner:UpdateService`, etc.

**When it's used:** During GitHub Actions workflow execution.

---

## Environment Variable Management

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
├── meta-app-secret
├── whatsapp-service-api-key
├── whatsapp-chat-retention-hours
├── whatsapp-message-age-threshold-seconds
├── whatsapp-under-maintenance
├── always-return-ok-to-meta
├── logging-level
└── origins
```

**Production Environment:**
```
/app-runtime/ansari-whatsapp/production/
├── (same structure as staging)
```

**Note:** Parameter names use hyphens (not underscores) in SSM paths, but App Runner converts them to underscores for environment variables.

Example: `/app-runtime/ansari-whatsapp/staging/backend-server-url` → `BACKEND_SERVER_URL`

### SSM Parameter Paths vs ARNs

SSM parameters have two formats depending on the context:

**1. Parameter Path** (used in AWS CLI commands):
```
/app-runtime/ansari-whatsapp/staging/backend-server-url
```

**2. Parameter ARN** (used in GitHub Actions `SSM_ROOT` variable):
```
arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/staging/
```

**Why the difference?**
- AWS CLI commands operate within AWS and use relative paths
- GitHub Actions workflows need the full ARN because they reference parameters from outside AWS
- The `SSM_ROOT` variable in GitHub stores the ARN prefix, which gets concatenated with parameter names

**Example workflow usage:**
```yaml
env:
  # SSM_ROOT = "arn:aws:ssm:us-west-2:123456789:parameter/app-runtime/ansari-whatsapp/staging/"
  BACKEND_SERVER_URL: ${{ format('{0}{1}', vars.SSM_ROOT, 'backend-server-url') }}
  # Results in: arn:aws:ssm:us-west-2:123456789:parameter/app-runtime/ansari-whatsapp/staging/backend-server-url
```

### How App Runner Resolves Environment Variables

1. GitHub Actions workflow defines environment variables with SSM parameter ARNs
2. These ARNs are passed to the App Runner deploy action
3. App Runner uses the `CustomAppRunnerInstanceRole` to fetch actual values from SSM
4. Values are injected as environment variables into the running container
5. Your application reads them via `os.environ['VAR_NAME']` or Pydantic settings

**Flow:**
```
GitHub Actions → SSM ARN → App Runner → Fetch from SSM → Container ENV
```

### Why Environment Variables Exist in Multiple Locations

You'll notice environment variables are stored in three places:

1. **Local development** (`.env` file): Used when running the service locally
2. **GitHub Secrets/Variables**: Used by test workflows (`perform-tests.yml`) to run tests without connecting to AWS
3. **AWS SSM Parameter Store**: Used by deployment workflows and the running App Runner service at runtime

**Why the duplication?**
- **Test workflows** run on GitHub Actions runners that don't have AWS access, so they pull env vars from GitHub Secrets/Variables
- **Deployment workflows** inject SSM parameter ARNs into App Runner, which fetches the actual values at runtime using the Instance IAM Role
- This separation allows tests to run independently without AWS dependencies while keeping production secrets securely in AWS

**Flow:**
```
Push to develop → Test workflow (uses GitHub env vars) → Tests pass → Deploy workflow (uses SSM ARNs) → App Runner (fetches from SSM)
```

### copy-env-vars vs copy-secret-env-vars

The GitHub Actions deployment workflow uses two sections for environment variables:

**`copy-env-vars`**: Literal values (e.g., `DEPLOYMENT_TYPE: staging`)
- AWS passes these as-is to the container
- Use for: Non-sensitive config that's hardcoded in the workflow
- Examples that could be set to `copy-env-vars`: `DEPLOYMENT_TYPE`, `LOGGING_LEVEL`

**`copy-secret-env-vars`**: SSM parameter ARNs (e.g., `arn:aws:ssm:...`)
- AWS App Runner resolves these by fetching the actual values from SSM Parameter Store before passing them to the container
- Use for: Secrets, sensitive config, or values that change independently
- Example: `BACKEND_SERVER_URL`, `META_ACCESS_TOKEN_FROM_SYS_USER`

**Example in workflow:**
```yaml
env:
  DEPLOYMENT_TYPE: staging  # Literal value
  BACKEND_SERVER_URL: ${{ format('{0}{1}', vars.SSM_ROOT, 'backend-server-url') }}  # SSM ARN

with:
  copy-env-vars: |
    DEPLOYMENT_TYPE  # Passed as literal "staging"
  copy-secret-env-vars: |
    BACKEND_SERVER_URL  # App Runner fetches from SSM and passes the actual URL
```

**Important:** If you put an SSM ARN in `copy-env-vars`, your app will receive the ARN string instead of the resolved value, causing validation errors.

See [GitHub Actions Concepts](../github_actions/concepts.md) for general GitHub Actions workflow information.

---

## Docker Image Strategy

### SHA-Based Tagging

Every Docker image is tagged with the git commit SHA:

```
<account-id>.dkr.ecr.us-west-2.amazonaws.com/ansari-whatsapp:a1b2c3d4
```

**How it works:**
1. Developer commits code (commit SHA: `a1b2c3d4`)
2. GitHub Actions builds image
3. Tags image: `ansari-whatsapp:a1b2c3d4`
4. Pushes to ECR
5. Deploys to App Runner with that specific tag

### Benefits

- **Exact version tracking:** Know exactly which git commit is deployed
- **Easy rollbacks:** Just redeploy an older SHA
- **No "latest" confusion:** Every deployment has a unique, immutable tag
- **Audit trail:** Image tags match git history

**Example rollback:**
```bash
# Find previous successful commit SHA from git history
git log --oneline

# Manually trigger deployment with that commit's image
# (or revert the commit and push)
```

---

## Resource Specifications

### App Runner Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **Region** | `us-west-2` (Oregon) | Same as ansari-backend for low latency |
| **CPU** | 1 vCPU | Lightweight webhook handling |
| **Memory** | 2 GB | Sufficient for Python/FastAPI |
| **Port** | 8001 | Distinguishes from ansari-backend (8000) |
| **Health Check** | `GET /` | Returns `{"status": "ok"}` |
| **Auto-scaling** | Enabled | Default behavior |
| **Min Instances** | 1 | Always one instance ready |
| **Max Instances** | 25 | Can scale up under load |

### Why These Specs?

**1 vCPU + 2GB Memory:**
- ansari-whatsapp is lightweight - just webhook handling and HTTP forwarding
- No heavy computations or large data processing
- Most requests are <100ms (forward to backend and return)

**Port 8001:**
- Distinguishes from ansari-backend (port 8000)
- Easier debugging when both services run locally

**us-west-2 (Oregon):**
- Same region as ansari-backend
- Low latency for service-to-service communication (~1-2ms)
- Same region as shared resources (IAM roles, etc.)

---

## AWS Resources

### Reused Resources (from ansari-backend)

These IAM roles already exist and are shared:

| Resource | Purpose | Notes |
|----------|---------|-------|
| `CustomAppRunnerServiceRole` | Allows App Runner to pull Docker images from ECR | Already has ECR access policy attached |
| `CustomAppRunnerInstanceRole` | Allows your app to read secrets from SSM | Already has Parameter Store access |
| `app-runner-github-actions-user` | GitHub Actions credentials for AWS | Already has ECR push and App Runner deploy permissions |

### New Resources (ansari-whatsapp)

| Resource | Name | Purpose |
|----------|------|---------|
| ECR Repository | `ansari-whatsapp` | Store Docker images |
| App Runner Service (Staging) | `ansari-staging-whatsapp` | Staging environment |
| App Runner Service (Production) | `ansari-production-whatsapp` | Production environment |
| SSM Parameters | `/app-runtime/ansari-whatsapp/staging/*` | Staging environment variables |
| SSM Parameters | `/app-runtime/ansari-whatsapp/production/*` | Production environment variables |

---

**Related Documentation:**
- [Setup History](./setup_history.md) - Commands to replicate this setup
- [GitHub Actions Concepts](../github_actions/concepts.md) - Understanding CI/CD workflows
