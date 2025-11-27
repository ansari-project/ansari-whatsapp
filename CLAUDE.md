# Claude Code Instructions for ansari-whatsapp

## Project Context
This is the `ansari-whatsapp` microservice that handles WhatsApp webhook requests and communicates with the `ansari-backend` service.

## Important Project-Specific Instructions

### Package Management
**CRITICAL: This project uses `uv` for package management, NOT `pip`!**

- ✅ **Correct:** `uv add package-name`
- ✅ **Correct:** `uv remove package-name`
- ✅ **Correct:** `uv sync`
- ❌ **Wrong:** `pip install package-name`
- ❌ **Wrong:** `pip uninstall package-name`

### Dependencies Installation
- **Add new dependencies:** `uv add pytest` (not `pip install pytest`)
- **Add dev dependencies:** `uv add --dev pytest`
- **Sync dependencies:** `uv sync`

### Virtual Environment
- The project uses `.venv` created by `uv`
- Activation: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Unix)

### Running the Application
- **Development mode**:
  - Use ansari-whatsapp's OWN venv python: `.venv/Scripts/python.exe src/ansari_whatsapp/app/main.py` (Windows) or `.venv/bin/python src/ansari_whatsapp/app/main.py` (Unix)
  - Alternative: `python -m src.ansari_whatsapp.app.main`
  - **IMPORTANT:** Use ansari-whatsapp's own .venv, NOT ansari-backend's .venv!
  - **Testing changes:** ansari-whatsapp boots up quickly, so auto-reload works reliably. You can test immediately after making changes.
- **Docker**: `docker build -t ansari-whatsapp . && docker run -p 8001:8001 --env-file .env ansari-whatsapp`
- **WhatsApp Webhook Proxy** (for local testing with Meta):
  1. In separate terminal, activate environment and cd to ansari-whatsapp root
  2. Run: `zrok reserve public localhost:8001 -n ZROK_SHARE_TOKEN` (using ZROK_SHARE_TOKEN from .env)
  3. This creates a public URL that Meta can reach to send webhook requests to your local server

### Code Quality
- **Linting**: `ruff check .` - Uses Ruff with line length 127, targeting Python 3.10+
- **Formatting**: `ruff format .` - Auto-formats code with double quotes and 4-space indentation
- **Fix issues**: `ruff check --fix .` - Auto-fixes linting issues

### Utilities
- **Clean logs**: `./clean_logs.sh [minutes]` - Removes log entries older than specified minutes (0 = all)

### Test Framework
- **Framework:** pytest (not unittest)
- **Pattern:** pytest + TestClient + fixtures
- **Installation:** `uv add pytest`
- **Run tests:** `pytest tests/ -v`
- **Logging Modes:**
  - `pytest tests/ -v -s` → all logs from all files to console
  - `LOG_TEST_FILES_ONLY=True pytest tests/ -v -s` → only test file logs to console + `logs/test_run.log`

**Backend Availability Requirements:**
The test suite checks if the ansari-backend is available based on `MOCK_ANSARI_CLIENT` setting:
- If `MOCK_ANSARI_CLIENT=True`: Tests use mock client (no backend needed)
- If `MOCK_ANSARI_CLIENT=False`: Tests require backend to be running

If backend is not available and mock mode is disabled, tests will fail with clear error messages explaining:
- **Option 1:** Set `MOCK_ANSARI_CLIENT=True` in `.env` to use mock mode
- **Option 2:** Verify `BACKEND_SERVER_URL` is correct in `.env`
- **Option 3:** Start the ansari-backend service on the configured URL

**Required Test Environment Variables:**
Tests that simulate WhatsApp webhook messages require:
- `META_BUSINESS_PHONE_NUMBER_ID`: Your Meta business phone number ID
- `WHATSAPP_DEV_PHONE_NUM`: A valid WhatsApp phone number for testing
- `WHATSAPP_DEV_MESSAGE_ID`: A valid message ID for testing

If these are not set, tests will fail with clear instructions. See `.env.example` for details.

**CI/CD Test Commands:**
When running tests in CI/CD pipelines, set `ALWAYS_RETURN_OK_TO_META=False` to get proper HTTP status codes for test assertions:
```bash
# Linux/Mac
ALWAYS_RETURN_OK_TO_META=False pytest tests/ -v

# Windows PowerShell
$env:ALWAYS_RETURN_OK_TO_META="False"; pytest tests/ -v

# Windows CMD
set ALWAYS_RETURN_OK_TO_META=False && pytest tests/ -v
```

### Test Structure
- `tests/test_whatsapp_service.py` - WhatsApp service webhook tests (no external dependencies)
- `tests/test_utils.py` - Secure logging utilities
- `pytest.ini` - pytest configuration

### Streaming Endpoint Testing
The `/whatsapp/v2/messages/process` endpoint streams responses. Tests should:
- Collect the **complete** streaming response (not just first chunk)
- Validate streaming performance, timing, and content
- Test timeout scenarios and error handling

### Environment Variables Required
Key environment variables (see `.env.example` for full list):
```env
# Meta/WhatsApp settings
META_WEBHOOK_VERIFY_TOKEN=your_verify_token
META_BUSINESS_PHONE_NUMBER_ID=your_phone_id

# Test behavior settings
ALWAYS_RETURN_OK_TO_META=True  # Set to False in CI/CD for proper status codes
LOG_TEST_FILES_ONLY=False      # Set to True to only log from test files
```

### Services Dependencies
- **ansari-backend:** Must be running on `http://localhost:8000`
- **ansari-whatsapp:** Must be running on `http://localhost:8001`

## Common Commands
```bash
# Install dependencies
uv add package-name

# Run WhatsApp service tests (this repo)
pytest tests/ -v
pytest tests/test_whatsapp_service.py -v

# Run servers
.venv/Scripts/python.exe src/ansari_whatsapp/app/main.py  # Windows
.venv/bin/python src/ansari_whatsapp/app/main.py          # Linux/Mac
```

## Architecture

### Directory Structure
```
src/ansari_whatsapp/
├── app/                    # FastAPI application and endpoints
│   └── main.py            # Main FastAPI app with webhook endpoints
├── services/              # Service layer (business logic)
│   ├── whatsapp_conversation_manager.py  # Orchestrates workflows
│   ├── ansari_client_{base,real,mock}.py # Backend API client
│   ├── meta_api_service_{base,real,mock}.py # WhatsApp API client
│   └── service_provider.py              # Dependency injection
├── presenters/            # Presentation layer
│   └── whatsapp_message_formatter.py    # Message formatting for WhatsApp
└── utils/                 # Utility modules
    ├── config.py          # Pydantic settings and configuration
    ├── whatsapp_webhook_parser.py  # Webhook JSON extraction
    ├── whatsapp_message_splitter.py # 4K character splitting
    ├── app_logger.py      # Custom logging with sensitive data masking
    ├── language_utils.py  # RTL language support
    ├── time_utils.py      # Timezone handling
    └── general_helpers.py # CORS middleware and utilities
```

### Key Components

**FastAPI Application** (`app/main.py`):
- Health check endpoint: `GET /`
- Webhook verification: `GET /whatsapp/v2`
- Message processing: `POST /whatsapp/v2`
- Uses BackgroundTasks for async message processing to prevent WhatsApp timeouts

**WhatsApp Conversation Manager** (`services/whatsapp_conversation_manager.py`):
- Orchestrates user registration, thread management, and message processing
- Manages typing indicators and chat retention (24 hours default)
- Coordinates between Ansari backend and Meta API services

**WhatsApp Message Formatter** (`presenters/whatsapp_message_formatter.py`):
- Formats AI responses for WhatsApp (4K character limit)
- Markdown to plain text conversion
- RTL language support (Arabic, Hebrew)
- Smart message splitting at sentence boundaries

**Configuration** (`utils/config.py`):
- Pydantic Settings with environment variable support
- Validates deployment type (local/staging/production)
- Auto-configures CORS origins based on deployment environment
- Manages WhatsApp API credentials and backend URL

**Service Layer**:
- **Ansari Client** (`services/ansari_client_*.py`): HTTP client for communicating with the main Ansari backend (base/real/mock)
- **Meta API Service** (`services/meta_api_service_*.py`): WhatsApp Business API client for sending messages (base/real/mock)
- **Service Provider** (`services/service_provider.py`): Dependency injection container for service selection

### Integration Points

The service acts as a bridge between WhatsApp Business API and the Ansari backend:
1. Receives webhooks from WhatsApp at `/whatsapp/v2`
2. Validates and processes incoming messages
3. Makes API calls to Ansari backend endpoints:
   - `/whatsapp/v2/users/register` - User registration
   - `/whatsapp/v2/users/exists` - Check user existence
   - `/whatsapp/v2/threads` - Create new threads
   - `/whatsapp/v2/threads/last` - Get last thread info
   - `/whatsapp/v2/threads/{thread_id}/history` - Get thread history
   - `/whatsapp/v2/messages/process` - Process messages (streaming)
4. Sends responses back to WhatsApp users via Graph API

### Environment Configuration

Key environment variables (see `.env.example`):
- `BACKEND_SERVER_URL` - **Base URL only** of the Ansari backend API (without `/api/v2` suffix)
  - Local: `http://localhost:8000`
  - Staging: `https://staging-api.ansari.chat`
  - Production: `https://api.ansari.chat`
  - The `/whatsapp/v2/*` endpoints are appended to this base URL by the Ansari client
- `META_BUSINESS_PHONE_NUMBER_ID` - WhatsApp Business phone number ID
- `META_ACCESS_TOKEN_FROM_SYS_USER` - WhatsApp API access token
- `META_WEBHOOK_VERIFY_TOKEN` - Webhook verification token
- `DEPLOYMENT_TYPE` - Environment type (local/staging/production)
- `WHATSAPP_CHAT_RETENTION_HOURS` - Chat history retention (default: 3)

### Development Notes

- Uses Python 3.10+ with modern async/await patterns
- Implements proper error handling with Loguru decorators
- CORS middleware automatically includes backend URL and deployment-specific origins
- Local development uses zrok for webhook tunneling
- Logging configured with Rich formatting and file rotation
- Comprehensive test suite with mock clients for CI/CD

## AWS Deployment

**AWS Region:** `us-west-2` (Oregon)
**AWS Account ID:** `AWS_ACCOUNT_ID`

For complete deployment instructions, see the [AWS Deployment Documentation](./docs/lld/aws/):

## ⚠️ CRITICAL SAFETY RULES

**Git Push Permissions:**
- **NEVER push directly to `ansari-project/ansari-backend`** without EXPLICIT user approval
- **You MAY push to `ansari-project/ansari-whatsapp`** (this repository) as needed
- **For ansari-backend changes, ALWAYS prompt the user first:**
  - **Simple, non-breaking changes** (docs, `__init__.py`, comments, typos, formatting, config examples):
    - Suggest pushing directly to `develop` branch for faster deployment
    - Wait for user approval before executing
  - **Complex or breaking changes** (code logic, API changes, dependencies, schema changes):
    - Suggest creating a PR for review and testing
    - Explain why a PR is recommended
    - Wait for user's decision (PR vs direct push)
- This is critical because ansari-backend is the main production service serving all users
- When in doubt, ask the user which approach they prefer

**AWS Resource Deletion:**
- **NEVER execute any commands that delete AWS resources** (ECR repositories, App Runner services, SSM parameters, S3 buckets, databases, etc.) without EXPLICIT user approval
- **ALWAYS ask the user first** before running any `delete`, `remove`, `destroy`, or destructive commands
- Examples of commands that require explicit approval:
  - `aws ecr delete-repository`
  - `aws apprunner delete-service`
  - `aws ssm delete-parameter`
  - `aws s3 rm` or `aws s3 rb`
  - Any command with `--force` flag
- When suggesting destructive operations, present them as options but DO NOT execute them
- If the user asks to delete a resource, confirm which specific resource and get explicit "ok" or "yes" confirmation


## Quick Links
- **[Deployment Guide](./docs/lld/aws/deployment_guide.md)** - Complete deployment walkthrough
- **[AWS CLI Commands](./docs/lld/aws/aws-cli.md)** - All AWS CLI commands for setup
- **[GitHub Actions Setup](./docs/lld/aws/github_actions_setup.md)** - CI/CD configuration

## Quick Reference

**Deployment:**
- Staging: Push to `develop` branch (or manually trigger workflow)
- Production: Push to `main` branch (or manually trigger workflow)

**GitHub Actions CLI Workflow Management:**
```bash
# Set default repository (your fork or upstream)
gh repo set-default <username>/<repo-name>  # e.g., OdyAsh/ansari-whatsapp

# List available workflows
gh workflow list

# Trigger workflow manually
gh workflow run <workflow-file>.yml --ref <branch>  # e.g., deploy-staging.yml --ref develop

# Monitor workflow runs
gh run list --workflow="<workflow-file>.yml"       # List recent runs
gh run view <run-id>                               # View run details
gh run view --job=<job-id>                          # View job details
```

**Get App Runner URL (for Cloudflare CNAME):**
```bash
# List all App Runner services
aws apprunner list-services --region us-west-2

# Get specific service URL
aws apprunner describe-service \
  --service-arn YOUR_SERVICE_ARN \
  --query 'Service.ServiceUrl' \
  --output text \
  --region us-west-2
```

**Fetch App Runner Logs (Windows/MSYS2):**
```bash
# Get logs from App Runner service (last 30 minutes)
# Note: MSYS2_ARG_CONV_EXCL prevents Windows path conversion on log group name
MSYS2_ARG_CONV_EXCL="*" aws logs tail "/aws/apprunner/SERVICE_NAME/SERVICE_ID/service" --region us-west-2 --since 30m

# Example for staging:
MSYS2_ARG_CONV_EXCL="*" aws logs tail "/aws/apprunner/ansari-staging-whatsapp/b0e5aa8e713c48a0845e676f4f60e048/service" --region us-west-2 --since 30m

# Adjust time window as needed: --since 1h, --since 2h, --since 1d
```

**Get App Runner Service Status:**
```bash
# Check service status
aws apprunner describe-service \
  --service-arn YOUR_SERVICE_ARN \
  --region us-west-2 \
  --query 'Service.Status' \
  --output text

# List recent operations to find failure reasons
aws apprunner list-operations \
  --service-arn YOUR_SERVICE_ARN \
  --region us-west-2
```

**Key Resources:**
- ECR: `AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/ansari-whatsapp`
- App Runner Staging: `ansari-staging-whatsapp`
- App Runner Production: `ansari-production-whatsapp`

## Recent Changes
- Refactored all tests to use pytest + TestClient pattern
- Added comprehensive streaming endpoint testing
- Implemented secure logging with sensitive data masking
- Added proper environment variable handling
- All security issues resolved (no hardcoded secrets)
- Added `ALWAYS_RETURN_OK_TO_META` setting for controlling webhook response behavior
- Added `LOG_TEST_FILES_ONLY` setting for filtering test logs
- Migrated to service layer architecture (base/real/mock pattern)
- Added WhatsApp conversation manager for workflow orchestration

**Remember: Always use `uv` for package management in this project!**