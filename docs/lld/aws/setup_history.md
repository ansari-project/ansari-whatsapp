# AWS Deployment Setup History

This document provides step-by-step commands to replicate the AWS deployment setup for ansari-whatsapp. Follow these steps in order to set up a new environment from scratch.

***TOC:***

- [AWS Deployment Setup History](#aws-deployment-setup-history)
  - [Prerequisites](#prerequisites)
    - [Tools Required](#tools-required)
    - [Access Required](#access-required)
    - [Important Note for Windows Users (MSYS2/Git Bash)](#important-note-for-windows-users-msys2git-bash)
  - [Phase 1: AWS Infrastructure Setup](#phase-1-aws-infrastructure-setup)
    - [Step 1: Create ECR Repository](#step-1-create-ecr-repository)
    - [Step 2: Get Existing IAM Role ARNs](#step-2-get-existing-iam-role-arns)
    - [Step 3: Verify IAM Policies (Optional)](#step-3-verify-iam-policies-optional)
    - [Step 4: Create Staging SSM Parameters](#step-4-create-staging-ssm-parameters)
    - [Step 5: Create Production SSM Parameters](#step-5-create-production-ssm-parameters)
    - [Step 6: Verify SSM Parameters](#step-6-verify-ssm-parameters)
  - [Phase 2: GitHub Actions Configuration](#phase-2-github-actions-configuration)
    - [Step 7: Create GitHub Environments](#step-7-create-github-environments)
    - [Step 8: Add GitHub Secrets](#step-8-add-github-secrets)
    - [Step 9: Add GitHub Variables](#step-9-add-github-variables)
  - [Phase 3: First Deployment](#phase-3-first-deployment)
    - [Step 10: Deploy to Staging](#step-10-deploy-to-staging)
    - [Step 11: Get App Runner URL](#step-11-get-app-runner-url)
    - [Step 12: Monitor Deployment](#step-12-monitor-deployment)
    - [Step 13: Test Staging Service](#step-13-test-staging-service)
    - [Step 14: Deploy to Production](#step-14-deploy-to-production)
  - [Phase 4: Ongoing Operations](#phase-4-ongoing-operations)
    - [Update SSM Parameters](#update-ssm-parameters)
    - [Manual Deployment Trigger](#manual-deployment-trigger)
    - [View App Runner Logs](#view-app-runner-logs)
      - [Step 1: Get Current Service ID](#step-1-get-current-service-id)
      - [Step 2: View Logs](#step-2-view-logs)
      - [Step 3: Filter Logs](#step-3-filter-logs)
    - [Check Service Status](#check-service-status)
    - [Rollback Deployment](#rollback-deployment)
  - [Cleanup Commands (⚠️ Danger Zone)](#cleanup-commands-️-danger-zone)
    - [Delete ECR Repository](#delete-ecr-repository)
    - [Delete SSM Parameters](#delete-ssm-parameters)
    - [Delete App Runner Service](#delete-app-runner-service)
  - [Quick Reference](#quick-reference)
    - [Common AWS CLI Commands](#common-aws-cli-commands)
    - [Common GitHub CLI Commands](#common-github-cli-commands)


---

## Prerequisites

### Tools Required

**Install AWS CLI:**
```bash
# macOS
brew install awscli

# Linux
sudo apt install awscli

# Windows
choco install awscli

# Verify installation
aws --version
```

**Configure AWS Profile:**
```bash
aws configure --profile ansari
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-west-2
# - Default output format: json
```

**Install GitHub CLI:**
```bash
# macOS
brew install gh

# Linux
sudo apt install gh

# Windows
choco install gh

# Authenticate
gh auth login
```

### Access Required

- [x] AWS CLI installed and configured
- [x] AWS profile named `ansari` (or adjust commands)
- [x] AWS credentials with permissions for ECR, App Runner, SSM, IAM
- [x] Access to ansari-project GitHub organization
- [x] Admin access to ansari-whatsapp repository settings
- [x] GitHub CLI authenticated
- [x] IAM role ARNs from ansari-backend setup

### Important Note for Windows Users (MSYS2/Git Bash)

**If you're using MSYS2 or Git Bash on Windows**, you'll need to prefix AWS CLI commands that include CloudWatch log group names (paths starting with `/`) with `MSYS2_ARG_CONV_EXCL="*"`:

```bash
# Example (MSYS2/Git Bash on Windows)
MSYS2_ARG_CONV_EXCL="*" aws logs tail "/aws/apprunner/SERVICE_NAME/SERVICE_ID/service" --region us-west-2
```

**Why?** MSYS2/Git Bash automatically converts Unix-style paths (like `/aws/apprunner/...`) to Windows paths (like `C:/Program Files/Git/aws/apprunner/...`), which breaks AWS CLI commands since `/aws/apprunner/...` is a log group name, not a file path.

**Solution:** `MSYS2_ARG_CONV_EXCL="*"` tells MSYS2 to exclude all arguments from path conversion.

**Alternatives:**
- Use PowerShell or CMD (no path conversion issues)
- Use WSL (Windows Subsystem for Linux)
- Set globally in `~/.bashrc`: `export MSYS2_ARG_CONV_EXCL="*"`

**References:**
- [MSYS2 Filesystem Paths Documentation](https://www.msys2.org/docs/filesystem-paths/)
- [Docker and Git Bash Path Conversion Workaround](https://gist.github.com/borekb/cb1536a3685ca6fc0ad9a028e6a959e3)
- [Stack Overflow: How to stop MinGW/MSYS from mangling paths](https://stackoverflow.com/questions/7250130/how-to-stop-mingw-and-msys-from-mangling-path-names-given-at-the-command-line)

---

## Phase 1: AWS Infrastructure Setup

### Step 1: Create ECR Repository

Create a Docker container registry for storing ansari-whatsapp images.

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
        "repositoryName": "ansari-whatsapp",
        "repositoryUri": "AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/ansari-whatsapp"
    }
}
```

**Save the `repositoryUri`** - you'll need it later!

**Verify Creation:**
```bash
aws ecr describe-repositories \
  --repository-names ansari-whatsapp \
  --region us-west-2 \
  --profile ansari
```

---

### Step 2: Get Existing IAM Role ARNs

These roles were created for ansari-backend and are reused for ansari-whatsapp.

**Get Service Role ARN:**
```bash
aws iam get-role --role-name CustomAppRunnerServiceRole \
  --query 'Role.Arn' --output text \
  --profile ansari
```

**Expected Output:**
```
arn:aws:iam::AWS_ACCOUNT_ID:role/CustomAppRunnerServiceRole
```

**Get Instance Role ARN:**
```bash
aws iam get-role --role-name CustomAppRunnerInstanceRole \
  --query 'Role.Arn' --output text \
  --profile ansari
```

**Expected Output:**
```
arn:aws:iam::AWS_ACCOUNT_ID:role/CustomAppRunnerInstanceRole
```

**Save both ARNs** - you'll need them for GitHub Secrets!

---

### Step 3: Verify IAM Policies (Optional)

Check that the instance role has SSM Parameter Store access.

```bash
# List policies attached to the role
aws iam list-role-policies --role-name CustomAppRunnerInstanceRole \
  --profile ansari

# View specific policy
aws iam get-role-policy \
  --role-name CustomAppRunnerInstanceRole \
  --policy-name CustomAccessParameters \
  --profile ansari
```

The policy should allow `ssm:GetParameters` and `ssm:GetParameter` actions on the parameter paths.

---

### Step 4: Create Staging SSM Parameters

These environment variables are stored in AWS Systems Manager Parameter Store.

**Backend Integration:**
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

**Meta/WhatsApp Credentials:**
```bash
# Meta Access Token (from Meta Business Settings → System Users)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
  --value "EAAC..." \
  --type SecureString \
  --profile ansari --region us-west-2

# Meta Business Phone Number ID (from WhatsApp Business Dashboard)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-business-phone-number-id" \
  --value "123456789012345" \
  --type SecureString \
  --profile ansari --region us-west-2

# Meta Webhook Verify Token (YOU create this - secure random string)
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

# Meta App Secret (from Meta App Dashboard → Settings → Basic)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-app-secret" \
  --value "your-meta-app-secret" \
  --type SecureString \
  --profile ansari --region us-west-2
```

**Service-to-Service Authentication:**
```bash
# WhatsApp Service API Key (for backend to call whatsapp service)
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/whatsapp-service-api-key" \
  --value "your-api-key-here" \
  --type SecureString \
  --profile ansari --region us-west-2
```

**Application Settings:**
```bash
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

**Operational Settings:**
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
  --value "DEBUG" \
  --type String \
  --profile ansari --region us-west-2

# CORS origins
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/origins" \
  --value "https://staging.ansari.chat,https://web.whatsapp.com" \
  --type String \
  --profile ansari --region us-west-2
```

---

### Step 5: Create Production SSM Parameters

Same structure as staging, but with production values.

**Backend Integration:**
```bash
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
```

**Meta/WhatsApp Credentials (use PRODUCTION credentials!):**
```bash
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

aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/meta-app-secret" \
  --value "your-production-meta-app-secret" \
  --type SecureString \
  --profile ansari --region us-west-2
```

**Service-to-Service Authentication:**
```bash
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/production/whatsapp-service-api-key" \
  --value "your-production-api-key" \
  --type SecureString \
  --profile ansari --region us-west-2
```

**Application Settings (same as staging):**
```bash
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
```

**Operational Settings:**
```bash
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

### Step 6: Verify SSM Parameters

**List All Staging Parameters:**
```bash
aws ssm get-parameters-by-path \
  --path "/app-runtime/ansari-whatsapp/staging" \
  --profile ansari --region us-west-2
```

**List All Production Parameters:**
```bash
aws ssm get-parameters-by-path \
  --path "/app-runtime/ansari-whatsapp/production" \
  --profile ansari --region us-west-2
```

**View Specific Parameter (with decryption):**
```bash
aws ssm get-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
  --with-decryption \
  --profile ansari --region us-west-2
```

---

## Phase 2: GitHub Actions Configuration

### Step 7: Create GitHub Environments

Environments allow you to scope secrets and variables to specific deployment targets.

```bash
# Create staging environment
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-staging-env --method PUT

# Create production environment
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-production-env --method PUT
```

**Verify:**
1. Go to repository Settings → Environments
2. You should see both `gh-actions-staging-env` and `gh-actions-production-env`

---

### Step 8: Add GitHub Secrets

**Repository-Level Secrets (shared across all environments):**
```bash
# AWS Credentials (from ansari-backend setup)
gh secret set AWS_ACCESS_KEY_ID --body "AKIA..." --repo ansari-project/ansari-whatsapp
gh secret set AWS_SECRET_ACCESS_KEY --body "..." --repo ansari-project/ansari-whatsapp
gh secret set AWS_REGION --body "us-west-2" --repo ansari-project/ansari-whatsapp

# IAM Role ARNs (from Step 2)
gh secret set SERVICE_ROLE_ARN --body "arn:aws:iam::AWS_ACCOUNT_ID:role/CustomAppRunnerServiceRole" --repo ansari-project/ansari-whatsapp
gh secret set INSTANCE_ROLE_ARN --body "arn:aws:iam::AWS_ACCOUNT_ID:role/CustomAppRunnerInstanceRole" --repo ansari-project/ansari-whatsapp
```

**Environment-Level Variables (for SSM paths):**
```bash
# Staging SSM root path
gh variable set SSM_ROOT --env gh-actions-staging-env --body "arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/staging/" --repo ansari-project/ansari-whatsapp

# Production SSM root path
gh variable set SSM_ROOT --env gh-actions-production-env --body "arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/production/" --repo ansari-project/ansari-whatsapp
```

---

### Step 9: Add GitHub Variables

**Important: SSM_ROOT Format**

The `SSM_ROOT` variable must be the **full ARN format**, not just the path:
- ❌ Wrong: `/app-runtime/ansari-whatsapp/staging/`
- ✅ Correct: `arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/staging/`

The ARN format is required because GitHub Actions workflows concatenate `SSM_ROOT` with parameter names to form complete ARN references. See [AWS Concepts - SSM Parameter Paths vs ARNs](../aws/concepts.md#ssm-parameter-paths-vs-arns) for details.

**Set environment-level variables:**
```bash
# Staging SSM root path (FULL ARN FORMAT!)
gh variable set SSM_ROOT --env gh-actions-staging-env --body "arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/staging/" --repo ansari-project/ansari-whatsapp

# Production SSM root path (FULL ARN FORMAT!)
gh variable set SSM_ROOT --env gh-actions-production-env --body "arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/production/" --repo ansari-project/ansari-whatsapp
```

**Set repository-level variables for test configuration:**

```bash
gh variable set MOCK_META_API --body "false" --repo ansari-project/ansari-whatsapp
gh variable set MOCK_ANSARI_CLIENT --body "false" --repo ansari-project/ansari-whatsapp
```

**Verify Configuration:**
```bash
# List all secrets (names only, values are hidden)
gh secret list --repo ansari-project/ansari-whatsapp

# List all variables
gh variable list --repo ansari-project/ansari-whatsapp
```

---

## Phase 3: First Deployment

### Step 10: Deploy to Staging

**Option A: Push to develop branch**
```bash
# Make a commit or merge a PR to develop branch
git checkout develop
git pull origin develop
git push origin develop
```

GitHub Actions will automatically trigger `.github/workflows/deploy-staging.yml`.

**Option B: Manual trigger**
1. Go to GitHub → Actions tab
2. Select "Staging Deployment (AWS App Runner)" workflow
3. Click "Run workflow" → Select `develop` branch
4. Click "Run workflow"

---

### Step 11: Get App Runner URL

After successful deployment, get the App Runner URL.

**Method 1: From GitHub Actions Logs**
- Check the final step "App Runner URL" in the workflow logs

**Method 2: From AWS CLI**
```bash
# List all App Runner services
aws apprunner list-services --region us-west-2 --profile ansari

# Get specific service URL
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-staging-whatsapp/SERVICE_ID \
  --query 'Service.ServiceUrl' \
  --output text \
  --region us-west-2 \
  --profile ansari
```

**Method 3: From AWS Console**
1. Go to https://console.aws.amazon.com/apprunner/home?region=us-west-2
2. Click on `ansari-staging-whatsapp`
3. Copy the **Default domain**

---

### Step 12: Monitor Deployment

**View GitHub Actions Logs:**
1. Go to Actions tab → Click on the running workflow
2. Expand steps to see detailed logs
3. Look for errors in red

**Key steps to monitor:**
- ✅ Build, tag, and push image to ECR
- ✅ Deploy to App Runner
- ✅ App Runner URL output

**Deployment Timing:**
- Build time: ~2-3 minutes
- Push to ECR: ~30 seconds
- App Runner deployment: ~5-7 minutes
- **Total: ~8-10 minutes**

---

### Step 13: Test Staging Service

**Health Check:**
```bash
curl https://<app-runner-url>/
# Expected: {"status": "ok"}
```

**Webhook Verification (Meta will call this):**
```bash
curl "https://<app-runner-url>/whatsapp/v2?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test123"
# Expected: test123
```

**Send Test WhatsApp Message:**
- Send a message to your WhatsApp business number
- Check App Runner logs to see if webhook was received

---

### Step 14: Deploy to Production

Once staging is tested and verified:

**Option A: Push to main branch**
```bash
# Merge develop into main
git checkout main
git pull origin main
git merge develop
git push origin main
```

**Option B: Manual trigger**
1. Go to GitHub → Actions tab
2. Select "Production Deployment (AWS App Runner)" workflow
3. Click "Run workflow" → Select `main` branch
4. Click "Run workflow"

**Important:** Update Meta webhook URL to production after deployment.

---

## Phase 4: Ongoing Operations

### Update SSM Parameters

When you need to change a configuration value:

```bash
# Update parameter
aws ssm put-parameter \
  --name "/app-runtime/ansari-whatsapp/staging/logging-level" \
  --value "DEBUG" \
  --type String \
  --overwrite \
  --profile ansari --region us-west-2
```

**Note:** After updating a parameter, you must redeploy the service for changes to take effect.

**Quick redeploy:**
- Manually trigger the deployment workflow from GitHub Actions

---

### Manual Deployment Trigger

Manually trigger deployment without pushing code:

**From GitHub UI:**
1. Go to Actions tab
2. Select workflow (Staging or Production Deployment)
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

**Use cases:**
- Environment variable updated (SSM parameter changed)
- Emergency rollback
- Testing a feature branch
- Hotfix deployment

---

### View App Runner Logs

#### Step 1: Get Current Service ID

First, get the service ID (instance ID) of the running App Runner service:

```bash
# Get staging service ID
aws apprunner list-services --region us-west-2 --profile ansari \
  --query "ServiceSummaryList[?ServiceName=='ansari-staging-whatsapp'].ServiceId" \
  --output text

# Get production service ID
aws apprunner list-services --region us-west-2 --profile ansari \
  --query "ServiceSummaryList[?ServiceName=='ansari-production-whatsapp'].ServiceId" \
  --output text

# Example output: 0d84da396de44c698f1866e70529ee3e
```

**Save this ID** - you'll need it for log commands below.

#### Step 2: View Logs

**Application Logs** (use `/application` for app stdout/stderr):

```bash
# Staging application logs (last 30 minutes) - (if on Windows' MSYS2/bash/etc, prefix with MSYS2_ARG_CONV_EXCL)
MSYS2_ARG_CONV_EXCL="*" aws logs tail \
  "/aws/apprunner/ansari-staging-whatsapp/<SERVICE_ID>/application" \
  --region us-west-2 --since 30m --profile ansari
```

```powershell
# Production application logs (last 1 hour) - (if on powershell, enter a backtick ` before line breaks)
aws logs tail `
  "/aws/apprunner/ansari-production-whatsapp/<SERVICE_ID>/application" `
  --region us-west-2 --since 1h --profile ansari

aws logs tail "/aws/apprunner/ansari-staging-whatsapp/<SERVICE_ID>/application" --region us-west-2 --since 30m --profile ansari
```

**Service Logs** (use `/service` for App Runner platform logs):

```bash
# View App Runner platform logs
MSYS2_ARG_CONV_EXCL="*" aws logs tail \
  "/aws/apprunner/ansari-staging-whatsapp/<SERVICE_ID>/service" \
  --region us-west-2 --since 30m --profile ansari
```

**Note:** Replace `<SERVICE_ID>` with the actual ID from Step 1.

#### Step 3: Filter Logs

**Simple text search** (case-sensitive substring match):

```bash
# Find logs containing "error" (simple text match)
MSYS2_ARG_CONV_EXCL="*" aws logs filter-log-events \
  --log-group-name "/aws/apprunner/ansari-staging-whatsapp/<SERVICE_ID>/application" \
  --region us-west-2 \
  --start-time $(($(date +%s) - 3600))000 \
  --filter-pattern "error" \
  --profile ansari
```

**For JSON logs with special characters** (like "Status: 403"):

CloudWatch's `--filter-pattern` has [strict syntax requirements](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html). For complex patterns with colons or special characters, **use CloudWatch Logs Insights instead**:

```bash
# Start a Logs Insights query
QUERY_ID=$(MSYS2_ARG_CONV_EXCL="*" aws logs start-query \
  --log-group-name "/aws/apprunner/ansari-staging-whatsapp/<SERVICE_ID>/application" \
  --region us-west-2 \
  --start-time $(($(date +%s) - 3600)) \
  --end-time $(date +%s) \
  --query-string 'fields text, file, line, time.iso | filter text like /Status: 403/ | sort time.timestamp desc | limit 50' \
  --query 'queryId' \
  --output text \
  --profile ansari)

echo "Query ID: $QUERY_ID"
sleep 3  # Wait for query to complete

# Get query results
MSYS2_ARG_CONV_EXCL="*" aws logs get-query-results \
  --query-id "$QUERY_ID" \
  --region us-west-2 \
  --profile ansari
```

**Common Logs Insights Queries:**

```sql
# Find all CORS errors
fields text, file, line, time.iso
| filter text like /CORS Origin Error/
| sort time.timestamp desc

# Find errors with Status: 403
fields text, file, line, time.iso
| filter text like /Status: 403/
| sort time.timestamp desc

# Find exceptions
fields text, file, line, exception.type, exception.value, time.iso
| filter ispresent(exception.type)
| sort time.timestamp desc
```

**From AWS Console:**
1. Go to App Runner → Select service
2. Click "Logs" tab
3. View real-time logs

**References:**
- [CloudWatch Filter Pattern Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [Stack Overflow: CloudWatch JSON Filter with Special Characters](https://stackoverflow.com/questions/69561586/cloudwatch-json-filter-patern-with-special-character)

---

### Check Service Status

```bash
# Check service status
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-staging-whatsapp/SERVICE_ID \
  --region us-west-2 \
  --profile ansari \
  --query 'Service.Status' \
  --output text

# List recent operations (to find failure reasons)
aws apprunner list-operations \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-staging-whatsapp/SERVICE_ID \
  --region us-west-2 \
  --profile ansari
```

**Deployment statuses:**
- 🔵 **OPERATION_IN_PROGRESS**: Deployment is running
- 🟢 **RUNNING**: Service is healthy
- 🔴 **CREATE_FAILED** / **UPDATE_FAILED**: Deployment failed
- 🟡 **ROLLED_BACK**: Deployment failed and was automatically rolled back

---

### Rollback Deployment

**Option 1: Revert Git Commit**
```bash
# Find the last good commit
git log --oneline

# Revert to that commit
git revert <bad-commit-sha>
git push origin develop  # or main
```

**Option 2: Manual Trigger with Old Image**
- Find the old commit SHA from git history
- Manually trigger deployment workflow
- GitHub Actions will deploy that specific image tag

---

## Cleanup Commands (⚠️ Danger Zone)

**Only use these if you want to completely remove ansari-whatsapp infrastructure!**

### Delete ECR Repository

```bash
# Delete all images and repository
aws ecr delete-repository \
  --repository-name ansari-whatsapp \
  --force \
  --profile ansari --region us-west-2
```

---

### Delete SSM Parameters

```bash
# Delete all staging parameters (list all names)
aws ssm delete-parameters \
  --names \
    "/app-runtime/ansari-whatsapp/staging/backend-server-url" \
    "/app-runtime/ansari-whatsapp/staging/deployment-type" \
    "/app-runtime/ansari-whatsapp/staging/meta-access-token-from-sys-user" \
    "/app-runtime/ansari-whatsapp/staging/meta-business-phone-number-id" \
    "/app-runtime/ansari-whatsapp/staging/meta-webhook-verify-token" \
    "/app-runtime/ansari-whatsapp/staging/meta-api-version" \
    "/app-runtime/ansari-whatsapp/staging/meta-app-secret" \
    "/app-runtime/ansari-whatsapp/staging/whatsapp-service-api-key" \
    "/app-runtime/ansari-whatsapp/staging/whatsapp-chat-retention-hours" \
    "/app-runtime/ansari-whatsapp/staging/whatsapp-message-age-threshold-seconds" \
    "/app-runtime/ansari-whatsapp/staging/whatsapp-under-maintenance" \
    "/app-runtime/ansari-whatsapp/staging/always-return-ok-to-meta" \
    "/app-runtime/ansari-whatsapp/staging/logging-level" \
    "/app-runtime/ansari-whatsapp/staging/origins" \
  --profile ansari --region us-west-2

# Repeat for production...
```

---

### Delete App Runner Service

```bash
# Get service ARN
aws apprunner list-services --profile ansari --region us-west-2

# Delete service
aws apprunner delete-service \
  --service-arn arn:aws:apprunner:us-west-2:AWS_ACCOUNT_ID:service/ansari-staging-whatsapp/SERVICE_ID \
  --profile ansari --region us-west-2
```

---

## Quick Reference

### Common AWS CLI Commands

**Update a secret:**
```bash
aws ssm put-parameter --name "<path>" --value "<new-value>" --overwrite --profile ansari --region us-west-2
```

**Check current value:**
```bash
aws ssm get-parameter --name "<path>" --with-decryption --profile ansari --region us-west-2
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

### Common GitHub CLI Commands

**Set repository secret:**
```bash
gh secret set SECRET_NAME --body "value" --repo ansari-project/ansari-whatsapp
```

**Set environment variable:**
```bash
gh variable set VAR_NAME --env gh-actions-staging-env --body "value" --repo ansari-project/ansari-whatsapp
```

**List secrets:**
```bash
gh secret list --repo ansari-project/ansari-whatsapp
```

---

**Related Documentation:**
- [AWS Concepts](./concepts.md) - Understanding AWS services used
- [GitHub Actions Setup History](../github_actions/setup_history.md) - GitHub-specific setup commands
