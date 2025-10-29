# Current GitHub Actions Setup

This document describes the current GitHub Actions configuration for the ansari-whatsapp repository.

***TOC:***

- [Current GitHub Actions Setup](#current-github-actions-setup)
  - [CI/CD Architecture](#cicd-architecture)
    - [Current Pipeline](#current-pipeline)
    - [Current Setup](#current-setup)
  - [Environments](#environments)
    - [Configured Environments](#configured-environments)
  - [Secrets \& Variables Distribution](#secrets--variables-distribution)
    - [Architecture: Two Levels](#architecture-two-levels)
    - [Distribution Strategy](#distribution-strategy)
    - [Current Distribution Table](#current-distribution-table)
    - [Precedence Rules](#precedence-rules)
  - [Workflows](#workflows)
    - [Current Workflows](#current-workflows)
      - [1. Ansari WhatsApp Tests (`perform-tests.yml`)](#1-ansari-whatsapp-tests-perform-testsyml)
  - [Related Documentation](#related-documentation)


---

## CI/CD Architecture

### Current Pipeline

```
Developer commits to GitHub
        ↓
GitHub Actions Workflow Triggers
        ↓
Run Tests (pytest)
        ↓
Upload Test Results as Artifacts
        ↓
(Future: Deploy to AWS App Runner)
```

### Current Setup

- **Test Workflow**: Runs on every push/PR to `main` or `develop` branches
- **Test Framework**: pytest with FastAPI TestClient (no external dependencies needed)
- **Environment**: Python 3.10 container
- **Package Manager**: uv (modern Python package installer)
- **Mock Mode**: Tests can run with mock clients (no real Meta API or backend calls required)

---

## Environments

GitHub environments are used to scope secrets and variables to specific deployment targets.

### Configured Environments

| Environment Name | Purpose | Used By |
|------------------|---------|---------|
| `gh-actions-staging-env` | Staging deployment configuration | Future staging deployment workflow |
| `gh-actions-production-env` | Production deployment configuration | Future production deployment workflow |

**Note:** Currently, the test workflow doesn't use specific environments since tests use mock mode. Environments are prepared for future deployment workflows.

---

## Secrets & Variables Distribution

### Architecture: Two Levels

GitHub supports two levels for storing secrets and variables:

1. **Repository-level**: Accessible by all workflows in the repository
2. **Environment-level**: Scoped to specific environments (staging, production)

### Distribution Strategy

*Why Repository-Level?*

Use repository-level for values that:
- Are the same across all environments
  - I.e., don't change between staging and production, etc.
- Or, you aren't sure will differ in the future (better to start general)

*Why Environment-Level?*

Use environment-level for values that:
- Differ between staging and production, etc.

### Current Distribution Table

| Setting | Type | Level | Staging Value | Production Value |
|---------|------|-------|---------------|------------------|
| `META_WEBHOOK_VERIFY_TOKEN` | Secret | Repository | (same) | (same) |
| `WHATSAPP_DEV_PHONE_NUM` | Secret | Repository | (same) | (same) |
| `WHATSAPP_DEV_MESSAGE_ID` | Secret | Repository | (same) | (same) |
| `META_BUSINESS_PHONE_NUMBER_ID` | Secret | Environment | staging_phone_id | production_phone_id |
| `META_ACCESS_TOKEN_FROM_SYS_USER` | Secret | Environment | staging_token | production_token |
| `BACKEND_SERVER_URL` | Variable | Environment | staging URL | production URL |
| `MOCK_META_API` | Variable | Repository | `false` | `false` |
| `MOCK_ANSARI_CLIENT` | Variable | Repository | `false` | `false` |

### Precedence Rules

**IMPORTANT:** If a key is defined in multiple places, GitHub Actions follows this precedence:

1. **Environment-level** takes precedence over **repository-level**
   - If `MY_VAR` exists in both environment and repository, environment value is used
2. **Secrets** take precedence over **variables** (if same name)
   - If `MY_VAR` exists as both secret and variable, secret value is used

**Example:**
```yaml
jobs:
  deploy:
    environment: gh-actions-staging-env
    env:
      # This uses the staging environment's value if it exists,
      # otherwise falls back to repository-level value
      API_KEY: ${{ secrets.API_KEY }}
```

---

## Workflows

### Current Workflows

#### 1. Ansari WhatsApp Tests (`perform-tests.yml`)

**File location:** `.github/workflows/perform-tests.yml`

**Trigger conditions:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**What it does:**
```
Push/PR to main or develop
        ↓
Checkout repository code
        ↓
Install uv package manager
        ↓
Install dependencies (uv pip install -e .)
        ↓
Run pytest tests
        ↓
Upload test results (always, even if tests fail)
```


## Related Documentation

- [AWS Deployment Guide](../aws/deployment_guide.md) - Deploying ansari-whatsapp to AWS
- [Project CLAUDE.md](../../../CLAUDE.md) - Development environment and commands
