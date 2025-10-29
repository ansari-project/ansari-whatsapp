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
- `BACKEND_SERVER_URL` - URL of the Ansari backend API
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