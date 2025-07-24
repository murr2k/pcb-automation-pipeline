# 🔑 API Keys & Registration Guide

This guide covers all external services and API keys required to unlock the full potential of the PCB Automation Pipeline.

## 📊 Quick Reference Table

| Service | Required For | Free Tier | Documentation |
|---------|-------------|-----------|---------------|
| **JLCPCB API** | PCB Ordering | ❌ Apply Required | [Details](#jlcpcb-api) |
| **MacroFab API** | PCB Ordering | ✅ Full API Access | [Details](#macrofab-api) |
| **PCBWay API** | PCB Ordering | ❌ Business Only | [Details](#pcbway-api) |
| **OSH Park** | PCB Ordering | ❌ No API | [Details](#osh-park) |
| **Seeed Studio** | PCB Ordering | ❌ Business Only | [Details](#seeed-studio-api) |
| **GitHub Actions** | CI/CD | ✅ 2000 min/month | [Details](#github-actions) |
| **Docker Hub** | Container Registry | ✅ Public repos | [Details](#docker-hub) |
| **Cloud Providers** | Web Hosting | ✅ Free tiers | [Details](#cloud-providers) |
| **Octopart API** | Component Data | ✅ 1000 calls/month | [Details](#octopart-api) |

## 🏭 PCB Manufacturer APIs

### JLCPCB API

**Purpose**: Automated PCB ordering, real-time quotes, order tracking

**Registration Process**:
1. Create business account at [JLCPCB](https://jlcpcb.com)
2. Build order history (minimum monthly volume required)
3. Apply for API access: https://forms.gle/gtrdpFnrc43Qy4uv9
4. Wait for approval (typically 5-10 business days)

**API Keys Required**:
```bash
PCB_JLCPCB_API_KEY="your-api-key"
PCB_JLCPCB_API_SECRET="your-api-secret"
```

**Requirements**:
- Regular monthly order volume
- Business/company account
- Previous order history
- Website developers on staff

**Cost**: Free API access (pay only for PCBs ordered)

**Limitations**:
- Cannot use JLCPCB trademark on your site
- Cannot include 'JLC' in your domain
- Violation results in immediate suspension

### PCBWay API

**Purpose**: High-end PCB manufacturing, up to 32 layers

**Registration Process**:
1. Create business account at [PCBWay](https://www.pcbway.com)
2. Contact sales team for API access
3. Negotiate enterprise agreement

**API Keys Required**:
```bash
PCB_PCBWAY_API_KEY="custom-integration-key"
PCB_PCBWAY_API_SECRET="custom-integration-secret"
```

**Requirements**:
- Enterprise/business partnership
- Custom integration agreement
- Direct sales contact

**Cost**: Negotiated based on volume

**Status**: Limited availability, not publicly documented

### MacroFab API

**Purpose**: Full-service PCB manufacturing, assembly, inventory, and fulfillment

**Registration Process**:
1. Sign up at [MacroFab Platform](https://platform.macrofab.com)
2. API key provided upon account creation
3. Full documentation at https://api.macrofab.com/api/v3/docs

**API Keys Required**:
```bash
PCB_MACROFAB_API_KEY="your-api-key"
```

**Requirements**:
- Valid MacroFab account
- No minimum order requirements
- Instant API access

**Cost**: 
- Free API access
- Pay only for manufacturing
- No setup fees for standard orders

**Features**:
- Full REST API with comprehensive documentation
- Real-time quotes and order tracking
- Inventory management
- Product fulfillment services
- File upload and validation
- Component sourcing

**API Endpoints**:
- `POST /api/v3/pcbs` - Create PCB projects
- `POST /api/v3/quotes` - Get instant quotes
- `POST /api/v3/placements` - Submit orders
- `GET /api/v3/placements/{id}` - Track orders
- `POST /api/v3/files` - Upload manufacturing files
- `GET /api/v3/inventory` - Manage inventory

### OSH Park

**Purpose**: Premium quality PCBs made in USA

**Registration**: Currently no public API available

**Workarounds**:
- Web automation (Selenium)
- Manual order submission
- Community reverse-engineered APIs

**Cost**: N/A (no official API)

### Seeed Studio API

**Purpose**: Fast turnaround, maker-friendly options

**Registration Process**:
1. Create account at [Seeed Studio](https://www.seeedstudio.com)
2. Contact business team for API access
3. Provide use case and volume estimates

**API Keys Required**:
```bash
PCB_SEEED_API_KEY="your-seeed-key"
PCB_SEEED_API_TOKEN="your-seeed-token"
```

**Requirements**:
- Business account
- Volume commitments
- Use case approval

**Cost**: Free API, pay for orders

## ⚙️ Development & CI/CD Services

### GitHub Actions

**Purpose**: Automated testing, validation, and deployment

**Registration**: Automatic with GitHub account

**Configuration**:
1. No explicit API key needed
2. Uses `GITHUB_TOKEN` automatically
3. Configure secrets in repository settings

**Free Tier**:
- Public repos: 2,000 minutes/month
- Private repos: 500 minutes/month

**Cost**: 
- Public repos: Free unlimited
- Private repos: $4/month for additional minutes

### Docker Hub

**Purpose**: Store and distribute KiCad Docker images

**Registration**: https://hub.docker.com/signup

**API Keys Required** (for CI/CD):
```bash
DOCKER_USERNAME="your-username"
DOCKER_PASSWORD="your-password"
```

**Free Tier**:
- Unlimited public repositories
- 1 private repository
- 200 pulls/6 hours (anonymous)

**Cost**: $5/month for unlimited private repos

## 🌐 Cloud Providers

### AWS (Amazon Web Services)

**Purpose**: Host FastAPI web interface

**Registration**: https://aws.amazon.com/free/

**API Keys Required**:
```bash
AWS_ACCESS_KEY_ID="your-access-key"
AWS_SECRET_ACCESS_KEY="your-secret-key"
AWS_DEFAULT_REGION="us-east-1"
```

**Free Tier** (12 months):
- EC2: 750 hours/month t2.micro
- S3: 5GB storage
- RDS: 750 hours db.t2.micro

**Cost**: Pay-as-you-go after free tier

### Google Cloud Platform (GCP)

**Purpose**: Alternative cloud hosting

**Registration**: https://cloud.google.com/free

**API Keys Required**:
```bash
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**Free Tier**:
- $300 credit for 90 days
- Always free products
- Cloud Run: 2 million requests/month

**Cost**: Pay-as-you-go after credits

### Microsoft Azure

**Purpose**: Enterprise cloud hosting

**Registration**: https://azure.microsoft.com/free/

**API Keys Required**:
```bash
AZURE_SUBSCRIPTION_ID="your-subscription-id"
AZURE_TENANT_ID="your-tenant-id"
AZURE_CLIENT_ID="your-client-id"
AZURE_CLIENT_SECRET="your-client-secret"
```

**Free Tier**:
- $200 credit for 30 days
- 12 months free services
- Always free services

**Cost**: Pay-as-you-go after credits

## 📊 Component Data Services

### Octopart API

**Purpose**: Real-time component pricing and availability

**Registration**: https://octopart.com/api/register

**API Keys Required**:
```bash
PCB_OCTOPART_API_KEY="your-octopart-key"
```

**Free Tier**:
- 1,000 API calls/month
- Access to pricing data
- Basic search functionality

**Paid Plans**:
- Starter: $50/month (10k calls)
- Professional: $500/month (100k calls)
- Enterprise: Custom pricing

### LCSC Parts Database

**Purpose**: JLCPCB component availability

**Status**: No official API, uses web scraping

**Alternative Sources**:
- Community databases
- Cached component lists
- Manual updates

## 🔧 Configuration Methods

### Method 1: Environment Variables

Create a `.env` file in project root:
```bash
# PCB Manufacturers
PCB_JLCPCB_API_KEY="your-key"
PCB_JLCPCB_API_SECRET="your-secret"
PCB_MACROFAB_API_KEY="your-key"  # Full API access available

# Component Data
PCB_OCTOPART_API_KEY="your-key"

# Cloud Services
AWS_ACCESS_KEY_ID="your-key"
AWS_SECRET_ACCESS_KEY="your-secret"

# Container Registry
DOCKER_USERNAME="your-username"
DOCKER_PASSWORD="your-password"
```

### Method 2: Configuration File

Update `configs/production_config.yaml`:
```yaml
# API Keys (DO NOT COMMIT!)
jlcpcb_api_key: "your-key"
jlcpcb_api_secret: "your-secret"
macrofab_api_key: "your-key"  # Recommended: Full API access
octopart_api_key: "your-key"

# Cloud Configuration
aws_region: "us-east-1"
docker_registry: "docker.io/yourusername"
```

### Method 3: GitHub Secrets

For CI/CD, add secrets in repository settings:
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `JLCPCB_API_KEY`
   - `JLCPCB_API_SECRET`
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - `SLACK_WEBHOOK_URL`

## 🚀 Getting Started Without API Keys

The pipeline works great in simulation mode without any API keys:

```bash
# Clone repository
git clone https://github.com/murr2k/pcb-automation-pipeline.git
cd pcb-automation-pipeline

# Install dependencies
pip install -r requirements.txt

# Run in simulation mode (no API keys needed)
python scripts/run_pipeline.py

# Features available without APIs:
# ✅ Schematic generation
# ✅ PCB layout
# ✅ Design validation
# ✅ Gerber export
# ✅ Simulated quotes
# ❌ Real ordering
# ❌ Live pricing
```

## 🔒 Security Best Practices

### 1. Never Commit Secrets
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "configs/production_config.yaml" >> .gitignore
echo "**/secrets.json" >> .gitignore
```

### 2. Use Environment Variables
```python
import os
api_key = os.environ.get('PCB_JLCPCB_API_KEY')
if not api_key:
    logger.warning("Running in simulation mode")
```

### 3. Rotate Keys Regularly
- Set calendar reminders
- Use key versioning
- Monitor usage logs

### 4. Least Privilege Access
- Create service accounts
- Limit scope of API keys
- Use read-only where possible

### 5. Secure Storage
- Use secrets management services
- Encrypt configuration files
- Audit access logs

## 📈 Cost Optimization Tips

### Development Phase
- Use all free tiers
- Run locally without cloud
- Test with simulation mode

### Production Phase
- Monitor API usage
- Set up billing alerts
- Use caching to reduce API calls
- Batch operations when possible

### Enterprise Deployment
- Negotiate volume pricing
- Use reserved instances
- Implement cost allocation tags
- Regular usage reviews

## 🆘 Troubleshooting

### JLCPCB API Not Working
```bash
# Check API status
curl -H "API-Key: your-key" https://api.jlcpcb.com/v1/status

# Common issues:
# - API key not activated
# - Rate limits exceeded
# - Incorrect endpoint URL
```

### Cloud Authentication Failing
```bash
# AWS
aws configure list
aws sts get-caller-identity

# GCP
gcloud auth list
gcloud config list

# Azure
az account show
```

### Docker Push Failing
```bash
# Re-authenticate
docker logout
docker login

# Check credentials
docker info
```

## 📞 Support Contacts

- **JLCPCB API**: api@jlcpcb.com
- **PCBWay Business**: sales@pcbway.com
- **Octopart API**: support@octopart.com
- **GitHub Support**: https://support.github.com
- **Docker Support**: https://docker.com/support

## 🔄 Updates

This documentation is maintained as part of the PCB Automation Pipeline project.
Last updated: January 2025

For the latest information, check:
- [GitHub Repository](https://github.com/murr2k/pcb-automation-pipeline)
- [API Documentation](API.md)
- [Setup Guide](SETUP.md)