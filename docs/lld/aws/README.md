# AWS Deployment Documentation

This directory contains all documentation and configuration files needed to deploy ansari-whatsapp to AWS App Runner.

## 📚 Documentation Files

### [deployment_guide.md](./deployment_guide.md)
**Start here!** Complete deployment walkthrough including:
- Architecture overview and service specifications
- Prerequisites and resource inventory
- Step-by-step deployment instructions
- Environment configuration details
- Validation procedures and testing
- Troubleshooting common issues

### [aws-cli.md](./aws-cli.md)
All AWS CLI commands you'll need:
- Create ECR repository
- Set up SSM parameters (staging & production)
- Verify resources
- Update parameters
- Get IAM role ARNs

### [github_actions_setup.md](./github_actions_setup.md)
GitHub configuration guide:
- Required GitHub Secrets
- Workflow explanations
- How deployments work
- Monitoring and troubleshooting

### [instance-role-parameters-access.json](./instance-role-parameters-access.json)
IAM policy document for App Runner instance role to access SSM Parameter Store.

## 🚀 Quick Start

1. **Read the deployment guide**: Start with [deployment_guide.md](./deployment_guide.md) for context
2. **Run AWS CLI commands**: Follow [aws-cli.md](./aws-cli.md) to create resources
3. **Configure GitHub**: Follow [github_actions_setup.md](./github_actions_setup.md) to add secrets
4. **Deploy**: Push to `develop` branch for staging, `main` for production

## 🏗️ Architecture Summary

```
GitHub (develop/main branch)
        ↓
GitHub Actions Workflow
        ↓
Docker Build (with uv)
        ↓
Amazon ECR
        ↓
AWS App Runner
        ↓
Running Service (with SSM secrets injected)
```

## 📋 Deployment Checklist

### Phase 4.1: AWS Resources
- [ ] Create ECR repository `ansari-whatsapp`
- [ ] Add SSM parameters for staging
- [ ] Add SSM parameters for production
- [ ] Verify IAM roles exist

### Phase 4.2: GitHub Configuration
- [ ] Add AWS credentials to GitHub Secrets
- [ ] Add IAM role ARNs to secrets
- [ ] Add SSM root paths to secrets
- [ ] Verify deployment workflows exist

### Phase 4.3: Deployment
- [ ] Push to `develop` → triggers staging deployment
- [ ] Test staging service
- [ ] Push to `main` → triggers production deployment
- [ ] Update Meta webhook URL
- [ ] Test production service


## 💡 Key Resources

**AWS Resources:**
- Region: `us-west-2` (Oregon)
- ECR Repository: `ansari-whatsapp`
- App Runner Services: `ansari-whatsapp-staging`, `ansari-whatsapp-production`
- SSM Paths: `/app-runtime/ansari-whatsapp/staging/*`, `/app-runtime/ansari-whatsapp/production/*`

**Reused IAM Roles (from ansari-backend):**
- `CustomAppRunnerServiceRole` - ECR access
- `CustomAppRunnerInstanceRole` - SSM access
- `app-runner-github-actions-user` - CI/CD credentials

---

**Ready to deploy? Start with [deployment_guide.md](./deployment_guide.md)! 🚀**
