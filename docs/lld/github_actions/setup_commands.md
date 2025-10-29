# GitHub Actions Setup Commands

This guide provides all the commands used to set up GitHub Actions for ansari-whatsapp. Use these commands to replicate the setup or make modifications.

***TOC:***

- [GitHub Actions Setup Commands](#github-actions-setup-commands)
  - [Prerequisites](#prerequisites)
    - [Install GitHub CLI](#install-github-cli)
    - [Authenticate with GitHub](#authenticate-with-github)
  - [Step-by-Step Setup](#step-by-step-setup)
    - [Step 1: Create Environments](#step-1-create-environments)
    - [Step 2: Set Repository-Level Secrets](#step-2-set-repository-level-secrets)
    - [Step 3: Set Environment-Level Secrets](#step-3-set-environment-level-secrets)
    - [Step 4: Set Environment-Level Variables](#step-4-set-environment-level-variables)
    - [Step 5: Set Repository-Level Variables](#step-5-set-repository-level-variables)
  - [Related Documentation](#related-documentation)


---

## Prerequisites

### Install GitHub CLI

**Windows (Chocolatey):**
```bash
choco install gh
```

**macOS (Homebrew):**
```bash
brew install gh
```

**Linux (apt):**
```bash
sudo apt install gh
```

### Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account. You'll need:
- GitHub account with access to the ansari-whatsapp repository
- Permissions to manage repository settings and secrets

---

## Step-by-Step Setup

Follow these steps in order to replicate the current GitHub Actions setup.

### Step 1: Create Environments

Environments allow you to scope secrets and variables to specific deployment targets (staging, production).

```bash
# Create staging environment
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-staging-env --method PUT

# Create production environment
gh api repos/ansari-project/ansari-whatsapp/environments/gh-actions-production-env --method PUT
```

**Note about owner:**
- Replace `ansari-project` with your username if you forked the repository
- Format: `repos/:owner/:repo/environments/:environment-name`
- After creating and testing, you can transfer to the organization

**Verify environments were created:**
1. Go to repository Settings → Environments
2. You should see both `gh-actions-staging-env` and `gh-actions-production-env`

---

### Step 2: Set Repository-Level Secrets

Repository-level secrets are accessible by all workflows and all environments.

```bash
# Meta webhook verification token (same for all environments)
gh secret set META_WEBHOOK_VERIFY_TOKEN --body "your_webhook_verify_token"

# Test phone number (used in CI tests)
gh secret set WHATSAPP_DEV_PHONE_NUM --body "201234567899"

# Test message ID (used in CI tests)
gh secret set WHATSAPP_DEV_MESSAGE_ID --body "wamid.seventy_two_char_hash"
```

**What to replace:**
- `your_webhook_verify_token` - Your Meta webhook verification token
- `201234567899` - A test phone number in international format (no + or leading zeros)
- `wamid.seventy_two_char_hash` - A real WhatsApp message ID (72 characters after "wamid.")

---

### Step 3: Set Environment-Level Secrets

Environment-level secrets are scoped to specific environments (staging or production).

**For staging environment:**
```bash
gh secret set META_BUSINESS_PHONE_NUMBER_ID --env gh-actions-staging-env --body "staging_phone_id"
gh secret set META_ACCESS_TOKEN_FROM_SYS_USER --env gh-actions-staging-env --body "staging_access_token"
```

**For production environment:**
```bash
gh secret set META_BUSINESS_PHONE_NUMBER_ID --env gh-actions-production-env --body "production_phone_id"
gh secret set META_ACCESS_TOKEN_FROM_SYS_USER --env gh-actions-production-env --body "production_access_token"
```

**What to replace:**
- `staging_phone_id` / `production_phone_id` - Meta business phone number IDs for each environment
- `staging_access_token` / `production_access_token` - System user access tokens from Meta for each environment

---

### Step 4: Set Environment-Level Variables

Variables are for non-sensitive configuration (they're visible in logs).

**For staging environment:**
```bash
gh variable set BACKEND_SERVER_URL --env gh-actions-staging-env --body "https://staging-api.ansari.chat"
```

**For production environment:**
```bash
gh variable set BACKEND_SERVER_URL --env gh-actions-production-env --body "https://api.ansari.chat"
```

**What to replace:**
- Backend URLs with your actual staging and production API endpoints

---

### Step 5: Set Repository-Level Variables

Repository-level variables are accessible by all workflows.

```bash
# Mock mode settings (used in tests)
gh variable set MOCK_META_API --body "false"
gh variable set MOCK_ANSARI_CLIENT --body "false"
```

**Mock mode values:**
- `"true"` - Tests use mock clients (no real API calls)
- `"false"` - Tests make real API calls (requires valid credentials)

---


## Related Documentation

**External Resources:**
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [GitHub Secrets API](https://docs.github.com/en/rest/actions/secrets)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
