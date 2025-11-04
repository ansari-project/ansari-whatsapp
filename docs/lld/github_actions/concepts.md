# GitHub Actions Concepts

This guide explains the fundamental concepts of GitHub Actions that you need to understand for working with the ansari-whatsapp CI/CD pipeline.

***TOC:***

- [GitHub Actions Concepts](#github-actions-concepts)
  - [What is GitHub Actions?](#what-is-github-actions)
  - [Key Concepts](#key-concepts)
    - [Workflow](#workflow)
    - [Job](#job)
    - [Step](#step)
    - [Runner](#runner)
    - [Action](#action)
  - [Workflow Structure](#workflow-structure)
    - [Common Triggers](#common-triggers)
  - [Environment Variables](#environment-variables)
    - [Accessing Secrets](#accessing-secrets)
    - [Accessing Variables](#accessing-variables)
    - [Fallback Values](#fallback-values)
    - [Repository vs Environment-Level](#repository-vs-environment-level)
  - [Artifacts](#artifacts)
    - [Uploading Artifacts](#uploading-artifacts)
    - [Downloading Artifacts](#downloading-artifacts)


---

## What is GitHub Actions?

GitHub Actions is a CI/CD (Continuous Integration/Continuous Deployment) platform that allows you to automate your build, test, and deployment pipeline. It runs workflows in response to events in your repository (like pushes, pull requests, etc.).

**Why use GitHub Actions?**
- Automate testing on every commit
- Deploy automatically when code is merged
- Run workflows on GitHub's servers (no need to maintain your own CI/CD infrastructure)
- Integrate directly with GitHub repositories

---

## Key Concepts

### Workflow
A configurable automated process defined in `.github/workflows/*.yml` files.

**Example:**
```yaml
name: Run Tests
on: [push, pull_request]
```

**Key points:**
- Workflows are triggered by events (push, PR, schedule, manual)
- Each repository can have multiple workflows
- Workflows are defined in YAML format

### Job
A set of steps that execute on the same runner. Multiple jobs can run in parallel or sequentially.

**Example:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest
```

**Key points:**
- Jobs run in fresh virtual environments
- By default, jobs run in parallel
- Use `needs:` to create dependencies between jobs

### Step
An individual task that runs commands or uses actions. Steps run sequentially within a job.

**Example:**
```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Run custom command
    run: echo "Hello World"
```

**Key points:**
- Steps in a job share the same filesystem
- Can run shell commands or use pre-built actions

### Runner
A server that runs workflows. GitHub provides hosted runners (ubuntu-latest, windows-latest, macos-latest).

**Example:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest  # GitHub-hosted Ubuntu runner
```

**Key points:**
- GitHub-hosted runners are free for public repositories
- Can also use self-hosted runners for custom environments

### Action
A reusable unit of code that performs a common task. Actions can be from GitHub, the community, or custom-built.

**Example:**
```yaml
- uses: actions/checkout@v4        # Official GitHub action
- uses: actions/upload-artifact@v4  # Upload files as artifacts
```

**Key points:**
- Actions save time by reusing common functionality
- Format: `owner/repo@version`
- Browse actions at [GitHub Marketplace](https://github.com/marketplace?type=actions)

**AWS App Runner Deploy Action Example:**

The `awslabs/amazon-app-runner-deploy@main` action supports passing environment variables to your deployed service:

```yaml
- name: Deploy to App Runner
  uses: awslabs/amazon-app-runner-deploy@main
  env:
    # Regular environment variable
    BACKEND_URL: https://api.example.com
    # SSM Parameter Store path for secrets
    API_TOKEN_SSM: /myapp/prod/api-token
  with:
    service: my-service
    image: my-image:latest
    access-role-arn: ${{ secrets.ROLE_ARN }}
    copy-env-vars: |
      BACKEND_URL
    copy-secret-env-vars: |
      API_TOKEN_SSM
```

- **`copy-env-vars`**: Lists environment variable names (defined in the `env:` block) to pass as regular environment variables to the App Runner service. These values are visible in logs.
- **`copy-secret-env-vars`**: Lists environment variable names whose **values must be AWS Systems Manager Parameter Store paths** (e.g., `/myapp/stage/secret-name`). App Runner will retrieve the actual secret values from SSM at runtime. These are masked in logs for security.
  - Source: [action-configuration.ts](https://github.com/awslabs/amazon-app-runner-deploy/blob/main/src/action-configuration.ts#L189-L213) - `getEnvironmentVariables()` function
  - Source: [index.test.ts](https://github.com/awslabs/amazon-app-runner-deploy/blob/main/src/index.test.ts#L269-L300) - Test showing `TEST_SECRET_ENV_VAR: '/test/secret_env'` as SSM path
  - Source: [client-apprunner-commands.ts](https://github.com/awslabs/amazon-app-runner-deploy/blob/main/src/client-apprunner-commands.ts#L70-L96) - How `RuntimeEnvironmentSecrets` are passed to App Runner

---

## Workflow Structure

A complete workflow file has this anatomy:

```yaml
name: Workflow Name                    # Human-readable name

on:                                    # Trigger conditions
  push:
    branches: ["main", "develop"]
  pull_request:
    branches: ["main", "develop"]

permissions:                           # Repository permissions
  contents: read

jobs:                                  # One or more jobs
  test-job:
    runs-on: ubuntu-latest            # Runner environment
    environment: staging-env           # (Optional) Use environment-level secrets

    env:                              # Environment variables
      VAR_NAME: ${{ secrets.SECRET_NAME }}

    steps:                            # Sequential tasks
      - name: Checkout code
        uses: actions/checkout@v4     # Use a reusable action

      - name: Run command
        run: echo "Hello World"       # Run shell commands
```

### Common Triggers

**Push to specific branches:**
```yaml
on:
  push:
    branches: ["main", "develop"]
```

**Pull requests:**
```yaml
on:
  pull_request:
    branches: ["main"]
```

**Manual trigger:**
```yaml
on:
  workflow_dispatch:  # Allows manual triggering from GitHub UI
```

**Scheduled (cron):**
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
```

---

## Environment Variables

### Accessing Secrets

Secrets are encrypted values stored in GitHub Settings.

**Syntax:**
```yaml
env:
  MY_SECRET: ${{ secrets.MY_SECRET }}
```

**Example:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      API_TOKEN: ${{ secrets.API_TOKEN }}
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

**Key points:**
- Secrets are masked in logs (never printed in plain text)
- Set in: Repository Settings → Secrets and variables → Actions

### Accessing Variables

Variables are non-sensitive configuration values.

**Syntax:**
```yaml
env:
  MY_VAR: ${{ vars.MY_VAR }}
```

**Example:**
```yaml
env:
  BACKEND_URL: ${{ vars.BACKEND_URL }}
  ENVIRONMENT: ${{ vars.ENVIRONMENT }}
```

**Key points:**
- Variables are visible in logs (not encrypted)
- Use for non-sensitive configuration (URLs, feature flags, etc.)

### Fallback Values

Provide default values when a variable/secret might not exist:

```yaml
env:
  MY_VAR: ${{ vars.MY_VAR || 'default_value' }}
  LOG_LEVEL: ${{ vars.LOG_LEVEL || 'INFO' }}
```

### Repository vs Environment-Level

**Repository-level:** Accessible by all workflows
```yaml
env:
  REPO_SECRET: ${{ secrets.REPO_SECRET }}
```

**Environment-level:** Scoped to specific environments (staging, production)
```yaml
jobs:
  deploy:
    environment: production  # Specify environment
    env:
      # This secret comes from the 'production' environment
      API_KEY: ${{ secrets.API_KEY }}
```

**Precedence rules:**
1. Environment-level secrets/variables override repository-level
2. Secrets take precedence over variables (if same name)

---

## Artifacts

Artifacts are files produced by workflow runs that you want to save and access later.

**What are artifacts?**
- Test results (JSON, XML reports)
- Build outputs (binaries, packages)
- Log files
- Coverage reports

**Retention:**
- Default: 90 days
- Configurable: 1-90 days
- Can be downloaded from GitHub UI

### Uploading Artifacts

**Basic example:**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-output/
```

**Multiple files:**
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: my-artifacts
    path: |
      logs/*.log
      reports/*.json
      coverage/
    retention-days: 30
```

**Always upload (even on failure):**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  if: always()  # Run even if previous steps failed
  with:
    name: test-results
    path: test-output/
```

### Downloading Artifacts

**From GitHub UI:**
1. Go to Actions tab → Click workflow run
2. Scroll to "Artifacts" section at bottom
3. Click artifact name to download ZIP file

**In another job:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: results/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Download test results
        uses: actions/download-artifact@v4
        with:
          name: test-results
```

---

**External Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
