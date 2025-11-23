# AWS Deployment Documentation

This directory contains documentation for deploying ansari-whatsapp to AWS App Runner.

***TOC:***

- [AWS Deployment Documentation](#aws-deployment-documentation)
  - [📚 Documentation Files](#-documentation-files)
    - [concepts.md](#conceptsmd)
    - [setup\_history.md](#setup_historymd)
  - [🚀 Quick Start](#-quick-start)
  - [🔍 Environment Variable Tracking](#-environment-variable-tracking)
  - [💡 Key Resources](#-key-resources)
  - [📋 Quick Reference](#-quick-reference)


## 📚 Documentation Files

### [concepts.md](./concepts.md)
**Start here to understand AWS deployment architecture.**

Learn about:
- Deployment pipeline and service architecture
- AWS services used (ECR, App Runner, SSM, IAM)
- IAM roles and permissions
- Environment variable management (`copy-env-vars` vs `copy-secret-env-vars`)
- Docker image tagging strategy
- Resource specifications

**Read this if:** You're new to the project or want to understand how AWS deployment works.

---

### [setup_history.md](./setup_history.md)
**Step-by-step commands to replicate the entire AWS deployment setup.**

Includes:
- Prerequisites (AWS CLI, GitHub CLI installation)
- Phase 1: AWS Infrastructure (ECR, SSM, IAM)
- Phase 2: GitHub Actions Configuration (secrets, variables, environments)
- Phase 3: First Deployment (staging and production)
- Phase 4: Ongoing Operations (updates, monitoring, rollbacks)
- Cleanup commands

**Read this if:** You need to set up AWS deployment from scratch or troubleshoot an existing setup.

---

## 🚀 Quick Start

**For Newcomers:**
1. Read [concepts.md](./concepts.md) to understand the architecture
2. Review [setup_history.md](./setup_history.md) to see how everything was configured

**For Setup/Deployment:**
1. Follow [setup_history.md](./setup_history.md) Phase 1-2 to create AWS resources
2. Follow Phase 3 to deploy
3. Use Phase 4 for ongoing operations

**For GitHub Actions Integration:**
- See [../github_actions/concepts.md](../github_actions/concepts.md) for general CI/CD workflows
- See [../github_actions/setup_history.md](../github_actions/setup_history.md) for GitHub-specific configuration

---

## 🔍 Environment Variable Tracking

Environment variables are defined in multiple locations. To track where a specific env var is set:

1. **Check `src/ansari_whatsapp/utils/config.py`**: See field definitions, `@field_validator` modifications, and `@property` derivations
2. **Check deployment workflows** (`.github/workflows/deploy-*.yml`): See if hardcoded (e.g., `DEPLOYMENT_TYPE: staging`) or fetched from SSM (e.g., `BACKEND_SERVER_URL: ${{ format(...) }}`)
3. **Check runtime modifications**: Search codebase for `os.environ["VAR_NAME"]` assignments

See [concepts.md - Environment Variable Management](./concepts.md#environment-variable-management) for details on how SSM parameters are resolved.

---

## 💡 Key Resources

**AWS Resources:**
- Region: `us-west-2` (Oregon)
- ECR Repository: `ansari-whatsapp`
- App Runner Services: `ansari-staging-whatsapp`, `ansari-production-whatsapp`
- SSM Paths: `/app-runtime/ansari-whatsapp/staging/*`, `/app-runtime/ansari-whatsapp/production/*`

**Reused IAM Roles (from ansari-backend):**
- `CustomAppRunnerServiceRole` - ECR access
- `CustomAppRunnerInstanceRole` - SSM access
- `app-runner-github-actions-user` - CI/CD credentials

---

## 📋 Quick Reference

**Common AWS CLI Commands:**
```bash
# List all App Runner services (to find service ARNs for subsequent commands)
aws apprunner list-services --region us-west-2

# Get service URL
aws apprunner describe-service --service-arn <arn> --query 'Service.ServiceUrl' --output text --region us-west-2

# View logs (Windows/MSYS2)
MSYS2_ARG_CONV_EXCL="*" aws logs tail "/aws/apprunner/SERVICE_NAME/SERVICE_ID/service" --region us-west-2 --since 30m

# Update SSM parameter
aws ssm put-parameter --name "<path>" --value "<new-value>" --overwrite --region us-west-2

# Check service status
aws apprunner describe-service --service-arn <arn> --query 'Service.Status' --output text --region us-west-2
```

See [setup_history.md - Quick Reference](./setup_history.md#quick-reference) for more commands.
