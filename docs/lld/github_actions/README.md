# GitHub Actions Documentation

This directory contains documentation for the GitHub Actions CI/CD setup in ansari-whatsapp.

## 📚 Documentation Files

### [concepts.md](./concepts.md)
**Start here to understand GitHub Actions fundamentals.**

Learn about:
- Workflows, jobs, steps, runners, and actions
- Triggers (push, PR, workflow_run, manual)
- Environment variables (secrets vs variables, precedence rules)
- Artifacts (uploading and downloading test results)
- Deployment workflows (test → staging → production)
- workflow_run trigger (wait for tests before deploying)

**Read this if:** You're new to GitHub Actions or want to understand how CI/CD workflows work.

---

### [setup_history.md](./setup_history.md)
**Step-by-step commands to replicate GitHub Actions configuration.**

Includes:
- Prerequisites (GitHub CLI installation)
- Create GitHub Environments
- Set repository-level and environment-level secrets
- Set repository-level and environment-level variables
- Deployment workflows overview
- Manual deployment triggers

**Read this if:** You need to configure GitHub Actions from scratch or troubleshoot existing configuration.

---

## 🚀 Quick Start

**For Newcomers:**
1. Read [concepts.md](./concepts.md) to understand GitHub Actions basics
2. Review [setup_history.md](./setup_history.md) to see how it's configured

**For Setup/Configuration:**
1. Install GitHub CLI and authenticate (see [setup_history.md - Prerequisites](./setup_history.md#prerequisites))
2. Follow [setup_history.md](./setup_history.md) step-by-step to create environments, secrets, and variables
3. Verify workflows are configured (`.github/workflows/`)

**For AWS Deployment Integration:**
- See [../aws/concepts.md](../aws/concepts.md) for AWS-specific deployment architecture
- See [../aws/setup_history.md](../aws/setup_history.md) for AWS infrastructure setup

---

## 🔄 Workflow Overview

**Current Workflows:**

1. **Test Workflow** (`perform-tests.yml`)
   - Triggers: Push/PR to `main` or `develop`
   - Runs pytest tests
   - Uploads test results

2. **Staging Deployment** (`deploy-staging.yml`)
   - Triggers: After tests pass on `develop` OR manual
   - Deploys to `ansari-staging-whatsapp` (AWS App Runner)

3. **Production Deployment** (`deploy-production.yml`)
   - Triggers: After tests pass on `main` OR manual
   - Deploys to `ansari-production-whatsapp` (AWS App Runner)

See [concepts.md - Deployment Workflows](./concepts.md#deployment-workflows) for details.

---

## 🔒 Secrets & Variables

**Repository-Level (shared across all environments):**
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `SERVICE_ROLE_ARN`, `INSTANCE_ROLE_ARN`
- `META_WEBHOOK_VERIFY_TOKEN`
- `MOCK_META_API` (default: `true`), `MOCK_ANSARI_CLIENT` (default: `true`)

**Environment-Level (staging/production):**
- `gh-actions-staging-env`: `SSM_ROOT` variable (full ARN format: `arn:aws:ssm:us-west-2:AWS_ACCOUNT_ID:parameter/app-runtime/ansari-whatsapp/staging/`)
- `gh-actions-production-env`: `SSM_ROOT` variable (full ARN format for production)

**Important:** `SSM_ROOT` must be the full ARN, not just the path. See [AWS Concepts - SSM Parameter Paths vs ARNs](../aws/concepts.md#ssm-parameter-paths-vs-arns) for details.

**Precedence:** Environment-level overrides repository-level.

See [concepts.md - Environment Variables](./concepts.md#environment-variables) for details.

---

## 📋 Quick Reference

**Common GitHub CLI Commands:**
```bash
# Authenticate
gh auth login

# Create environment
gh api repos/ansari-project/ansari-whatsapp/environments/ENV_NAME --method PUT

# Set repository secret
gh secret set SECRET_NAME --body "value" --repo ansari-project/ansari-whatsapp

# Set environment variable
gh variable set VAR_NAME --env ENV_NAME --body "value" --repo ansari-project/ansari-whatsapp

# List secrets
gh secret list --repo ansari-project/ansari-whatsapp

# List variables
gh variable list --repo ansari-project/ansari-whatsapp
```

See [setup_history.md](./setup_history.md) for complete setup commands.