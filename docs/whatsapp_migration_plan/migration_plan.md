# WhatsApp Migration Plan

- [WhatsApp Migration Plan](#whatsapp-migration-plan)
  - [Current Migration Status](#current-migration-status)
    - [✅ What's Already Migrated to ansari-whatsapp:](#-whats-already-migrated-to-ansari-whatsapp)
    - [✅ Cleaned Up from ansari-backend (Completed):](#-cleaned-up-from-ansari-backend-completed)
    - [✅ Backend API Endpoints (Completed):](#-backend-api-endpoints-completed)
    - [🔧 What Needs Enhancement in ansari-whatsapp:](#-what-needs-enhancement-in-ansari-whatsapp)
  - [Migration Plan](#migration-plan)
    - [✅ Phase 1: Create Missing Backend API Endpoints (COMPLETED)](#-phase-1-create-missing-backend-api-endpoints-completed)
    - [✅ Phase 2: Clean Up ansari-backend (COMPLETED)](#-phase-2-clean-up-ansari-backend-completed)
    - [✅ Phase 3: Complete ansari-whatsapp Implementation (COMPLETED)](#-phase-3-complete-ansari-whatsapp-implementation-completed)
    - [Phase 4: AWS Deployment \& Production Release](#phase-4-aws-deployment--production-release)
      - [4.1 AWS Resources Setup](#41-aws-resources-setup)
      - [4.2 GitHub Configuration](#42-github-configuration)
      - [4.3 Code \& Configuration](#43-code--configuration)
      - [4.4 Environment Variables Configuration](#44-environment-variables-configuration)
      - [4.5 Deployment Validation \& Go-Live](#45-deployment-validation--go-live)
  - [Migration Progress](#migration-progress)


## Current Migration Status

### ✅ What's Already Migrated to ansari-whatsapp:
1. **Core webhook endpoints** - Both GET/POST `/whatsapp/v2` endpoints
2. **FastAPI application structure** - Independent FastAPI app with proper CORS middleware
3. **WhatsApp message extraction logic** - `extract_relevant_whatsapp_message_details()` function
4. **WhatsApp presenter** - Core message handling logic with typing indicators and markdown formatting
5. **Backend API client** - HTTP client to communicate with ansari-backend (`AnsariClient`)
6. **Configuration management** - Pydantic settings with env var support
7. **Logging system** - Loguru-based logging with Rich formatting
8. **Language utilities** - Text direction and language detection helpers
9. **Message splitting** - WhatsApp 4K character limit handling
10. **Background task processing** - Async message processing to prevent webhook timeouts

### ✅ Cleaned Up from ansari-backend (Completed):
1. ✅ **main_whatsapp.py** - Removed (old webhook implementation)
2. ✅ **whatsapp_presenter.py** - Removed (moved to ansari-whatsapp)
3. ✅ **Old WhatsApp router** - Replaced with new whatsapp_router.py for backend endpoints only
4. ✅ **WhatsApp environment variables** - Removed legacy WhatsApp config vars from backend (no longer needed)

### ✅ Backend API Endpoints (Completed):
The ansari-whatsapp service communicates with these backend endpoints:

1. ✅ `POST /whatsapp/v2/users/register` - Register WhatsApp users
2. ✅ `GET /whatsapp/v2/users/exists` - Get user ID for phone number (404 if not found)
3. ✅ ~~`PUT /whatsapp/v2/users/location` - Update user location~~ (Removed for privacy)
4. ✅ `POST /whatsapp/v2/threads` - Create new message threads
5. ✅ `GET /whatsapp/v2/threads/last` - Get last thread info
6. ✅ `GET /whatsapp/v2/threads/{thread_id}/history` - Get thread history
7. ✅ `POST /whatsapp/v2/messages/process` - Process messages (with streaming support)

### 🔧 What Needs Enhancement in ansari-whatsapp:
1. **Message too old logic** - Currently commented out in main.py:218
2. **Error handling improvements** - Some TODO comments for better error handling
3. **Environment variable cleanup** - Remove any unused legacy vars

## Migration Plan

### ✅ Phase 1: Create Missing Backend API Endpoints (COMPLETED)
- ✅ Create `whatsapp_router.py` in ansari-backend
- ✅ Implement all 7 API endpoints with proper database integration
- ✅ Add streaming support for message processing endpoint
- ✅ Include router in main_api.py
- ✅ Remove location endpoint from ansari-whatsapp (privacy improvement)

### ✅ Phase 2: Clean Up ansari-backend (COMPLETED)
- ✅ Remove `main_whatsapp.py` file
- ✅ Remove `presenters/whatsapp_presenter.py` file
- ✅ Remove old WhatsApp router import from main_api.py
- ✅ Remove legacy WhatsApp environment variables from backend config (were unused)
- ✅ Update documentation to reflect separation

### ✅ Phase 3: Complete ansari-whatsapp Implementation (COMPLETED)
- ✅ Test all endpoints thoroughly with both services running
- ✅ Update environment variable configuration
- ✅ Implement mock clients for testing without external dependencies
- ✅ CI/CD testing workflow configured (perform-tests-app.yml)
- ✅ All integration tests passing

### Phase 4: AWS Deployment & Production Release

This phase covers deploying ansari-whatsapp to AWS App Runner using the same infrastructure pattern as ansari-backend.

**📚 Detailed Documentation:**
- **[Complete Deployment Guide](../aws/deployment_guide.md)** - Step-by-step walkthrough with architecture overview, troubleshooting, and validation procedures
- **[AWS CLI Commands](../aws/aws-cli.md)** - All commands to create ECR repositories, SSM parameters, and verify resources
- **[GitHub Actions Setup](../aws/github_actions_setup.md)** - GitHub Secrets configuration and workflow explanations

#### 4.1 AWS Resources Setup

**Resources We'll Reuse:**
- ✅ `CustomAppRunnerServiceRole` - Allows App Runner to pull Docker images from ECR
- ✅ `CustomAppRunnerInstanceRole` - Allows containers to read SSM Parameter Store
- ✅ `app-runner-github-actions-user` - GitHub Actions AWS credentials

**New Resources to Create:**
- [ ] ECR Repository: `ansari-whatsapp`
- [ ] SSM Parameters: `/app-runtime/ansari-whatsapp/staging/*`
- [ ] SSM Parameters: `/app-runtime/ansari-whatsapp/production/*`
- [ ] App Runner Service: `ansari-staging-whatsapp`
- [ ] App Runner Service: `ansari-production-whatsapp`

**Specifications:**
- Region: `us-west-2` (Oregon)
- CPU: 1 vCPU
- Memory: 2 GB
- Port: 8001
- Health Check: `GET /`

See [aws/aws-cli.md](../aws/aws-cli.md) for detailed creation commands.

#### 4.2 GitHub Configuration

**Secrets to Add** (see [github_actions_setup.md](../aws/github_actions_setup.md)):
- [ ] `AWS_ACCESS_KEY_ID` (reuse from ansari-backend)
- [ ] `AWS_SECRET_ACCESS_KEY` (reuse from ansari-backend)
- [ ] `AWS_REGION` = `us-west-2`
- [ ] `SERVICE_ROLE_ARN` (CustomAppRunnerServiceRole ARN)
- [ ] `INSTANCE_ROLE_ARN` (CustomAppRunnerInstanceRole ARN)
- [ ] `SSM_ROOT` = `/app-runtime/ansari-whatsapp/staging/` or `/app-runtime/ansari-whatsapp/production/` (based on the environment)

**Deployment Workflows:**
- ✅ `.github/workflows/deploy-staging.yml` - Auto-deploy on push to `develop`
- ✅ `.github/workflows/deploy-production.yml` - Auto-deploy on push to `main`

#### 4.3 Code & Configuration

**Completed:**
- ✅ Dockerfile updated to use `uv` (multi-stage build for efficiency)
- ✅ Environment variables mapped for staging vs production
- ✅ Health check endpoint implemented (`GET /`)
- ✅ CORS origins auto-configured per environment

**Deployment Pipeline:**
```
Push to GitHub (develop/main)
    ↓
GitHub Actions builds Docker image
    ↓
Push to Amazon ECR
    ↓
Deploy to AWS App Runner
    ↓
Load secrets from SSM Parameter Store
    ↓
Service goes live! 🚀
```

#### 4.4 Environment Variables Configuration

**Key Variables by Category:**

| Category | Variables | Storage Location |
|----------|-----------|------------------|
| **Backend Integration** | `BACKEND_SERVER_URL`, `DEPLOYMENT_TYPE` | SSM Parameter Store |
| **WhatsApp Credentials** | `META_ACCESS_TOKEN_FROM_SYS_USER`, `META_BUSINESS_PHONE_NUMBER_ID`, `META_WEBHOOK_VERIFY_TOKEN`, `META_API_VERSION` | SSM Parameter Store |
| **Application Settings** | `WHATSAPP_CHAT_RETENTION_HOURS`, `WHATSAPP_MESSAGE_AGE_THRESHOLD_SECONDS` | SSM Parameter Store |
| **Operational** | `ALWAYS_RETURN_OK_TO_META`, `LOGGING_LEVEL`, `ORIGINS` | SSM Parameter Store |

**SSM Parameter Store Structure:**
```
/app-runtime/ansari-whatsapp/
├── staging/
│   ├── backend-server-url
│   ├── meta-access-token-from-sys-user
│   ├── meta-business-phone-number-id
│   └── ... (all environment variables)
└── production/
    ├── backend-server-url
    ├── meta-access-token-from-sys-user
    ├── meta-business-phone-number-id
    └── ... (all environment variables)
```

See [aws/aws-cli.md](../aws/aws-cli.md) for complete parameter list and creation commands.

#### 4.5 Deployment Validation & Go-Live

**Pre-Deployment Checklist:**
- [ ] All SSM parameters created and verified
- [ ] GitHub secrets configured
- [ ] IAM role ARNs obtained
- [ ] ECR repository created
- [ ] Dockerfile builds successfully locally
- [ ] All tests passing

**Deployment Steps:**
1. [ ] Create AWS resources (ECR, SSM parameters)
2. [ ] Configure GitHub Secrets
3. [ ] Deploy to staging (`git push origin develop`)
4. [ ] Monitor deployment in GitHub Actions (~8-10 minutes)
5. [ ] Verify staging health check and logs
6. [ ] Send test WhatsApp message to staging
7. [ ] Deploy to production (`git push origin main`)
8. [ ] Update Meta webhook URL to production App Runner URL
9. [ ] Send production test message
10. [ ] Monitor CloudWatch metrics

**Post-Deployment Validation:**
- [ ] Health check returns `{"status": "ok"}`
- [ ] Webhook verification works (Meta's GET request)
- [ ] Test WhatsApp message received and responded
- [ ] App Runner logs show no errors
- [ ] Backend communication working (check backend logs)

See [deployment_guide.md](../aws/deployment_guide.md) for detailed validation procedures and troubleshooting.

## Migration Progress

**Current Status: Phase 3 Complete ✅ | Phase 4 Ready for Execution 🚀**

✅ **Phase 1 & 2**: Backend separation complete
✅ **Phase 3**: ansari-whatsapp implementation and testing complete
🔄 **Phase 4**: AWS deployment infrastructure prepared, ready for execution

**Architecture Status:**
- **ansari-whatsapp**: Independent microservice handling WhatsApp webhooks ✅
- **ansari-backend**: Provides API endpoints for ansari-whatsapp ✅
- **Deployment Infrastructure**: AWS resources defined, workflows created ✅
- **Documentation**: Complete deployment guides with troubleshooting ✅

**Recent Improvements:**
- Removed all location tracking functionality for improved user privacy
- Both old webhook implementations removed from backend
- Clean separation of concerns between services
- Comprehensive AWS deployment documentation created
- GitHub Actions workflows for staging and production deployment
- Dockerfile optimized to use uv with multi-stage builds

**Next Steps:**
1. Execute Phase 4.1: Create AWS resources (see [aws/aws-cli.md](../aws/aws-cli.md))
2. Execute Phase 4.2: Configure GitHub Secrets (see [aws/github_actions_setup.md](../aws/github_actions_setup.md))
3. Execute Phase 4.3-4.5: Deploy and validate (see [aws/deployment_guide.md](../aws/deployment_guide.md))