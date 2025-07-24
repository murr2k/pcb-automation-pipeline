# 🚀 Fly.io Deployment Guide

This guide covers deploying the PCB Automation Pipeline to Fly.io for global, scalable hosting.

## 🌍 Why Fly.io?

- **Global Edge Deployment**: Deploy close to users and PCB manufacturers
- **Persistent Storage**: Store generated PCB files and designs
- **Auto-scaling**: Handle traffic spikes automatically
- **WebSocket Support**: Real-time PCB generation updates
- **Docker Native**: Your existing Docker image works perfectly
- **Cost-Effective**: Free tier handles ~1000 PCB generations/month

## 📋 Prerequisites

1. Fly.io account (free at [fly.io](https://fly.io))
2. Fly CLI installed:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```
3. Your Fly.io auth token (already provided)

## 🚀 Quick Deployment

### 1. Initialize the App

```bash
# Set your auth token
export FLY_API_TOKEN="FlyV1 fm2_lJPECA..."

# Initialize the app
./scripts/fly_deploy.sh init
```

This creates:
- Fly.io app named `pcb-automation-pipeline`
- 10GB persistent volume for file storage
- Optional Postgres database for job tracking

### 2. Set API Keys

```bash
# Set your API keys as secrets
./scripts/fly_deploy.sh secrets

# Or manually:
flyctl secrets set PCB_MACROFAB_API_KEY="k2TlSRhDC41lKLdP5QxeTDP3v4AcnCO"
flyctl secrets set PCB_JLCPCB_API_KEY="your-key"  # Optional
flyctl secrets set PCB_OCTOPART_API_KEY="your-key"  # Optional
```

### 3. Deploy

```bash
# Deploy the application
./scripts/fly_deploy.sh deploy

# Your app will be available at:
# https://pcb-automation-pipeline.fly.dev
```

## 🏗️ Architecture on Fly.io

```
┌─────────────────────────────────────────────────┐
│             Fly.io Global Network               │
├─────────────────────────────────────────────────┤
│   ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│   │   DFW   │  │   AMS   │  │   NRT   │       │
│   │ (Texas) │  │(Europe) │  │ (Asia)  │       │
│   └────┬────┘  └────┬────┘  └────┬────┘       │
│        │            │            │              │
│        └────────────┴────────────┘              │
│                     │                           │
│         ┌──────────┴──────────┐                │
│         │   Load Balancer     │                │
│         └──────────┬──────────┘                │
│                    │                            │
│    ┌───────────────┴───────────────┐          │
│    │       PCB Pipeline App        │          │
│    │  ┌────────┐    ┌──────────┐  │          │
│    │  │ Web API│    │  Worker  │  │          │
│    │  └────────┘    └──────────┘  │          │
│    │         │          │          │          │
│    │    ┌────┴──────────┴────┐    │          │
│    │    │ Persistent Volume  │    │          │
│    │    │   /data (10GB)     │    │          │
│    │    └────────────────────┘    │          │
│    └───────────────────────────────┘          │
└─────────────────────────────────────────────────┘
```

## 📦 What Gets Deployed

1. **Docker Container**: Your KiCad-enabled Docker image
2. **Web API**: FastAPI server on port 8000
3. **Persistent Storage**: 10GB volume for generated files
4. **Auto-scaling**: 1-5 instances based on load
5. **Health Checks**: Automatic monitoring and restarts

## 🔧 Configuration Details

### fly.toml Overview

```toml
app = "pcb-automation-pipeline"
primary_region = "dfw"  # Dallas - near MacroFab!

[env]
  PCB_USE_DOCKER = "true"
  PCB_OUTPUT_DIR = "/data/output"

[mounts]
  source = "pcb_data"
  destination = "/data"

[[services]]
  internal_port = 8000
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Scaling Configuration

```bash
# Manual scaling
./scripts/fly_deploy.sh scale 3

# Or use flyctl directly
flyctl scale count 3
flyctl scale vm shared-cpu-2x  # Upgrade VM size
```

## 📊 Monitoring & Management

### View Logs

```bash
# Real-time logs
./scripts/fly_deploy.sh logs

# Or with flyctl
flyctl logs --tail
```

### Check Status

```bash
# App status
./scripts/fly_deploy.sh status

# Detailed metrics
flyctl status --all
```

### SSH Access

```bash
# SSH into running instance
./scripts/fly_deploy.sh ssh

# Run commands
flyctl ssh console -C "ls -la /data/output"
```

## 💰 Cost Optimization

### Free Tier (Hobby)
- **Resources**: 3 shared VMs, 3GB storage
- **Usage**: ~1000 PCB generations/month
- **Cost**: $0

### Scale Plan ($25/month)
- **Resources**: Dedicated VMs, 50GB storage
- **Usage**: ~10,000 PCB generations/month
- **Features**: Auto-scaling, multi-region

### Pro Tips for Cost Savings:
1. Use shared VMs for development
2. Scale down during off-hours
3. Enable auto-stop for idle instances
4. Use CDN for static file delivery

## 🌐 Multi-Region Deployment

Deploy to multiple regions for global coverage:

```bash
# Add regions
flyctl regions add ams nrt  # Amsterdam, Tokyo

# Set backup regions
flyctl regions backup dfw ams

# View current regions
flyctl regions list
```

## 🔒 Security

### Secrets Management

```bash
# List secrets
flyctl secrets list

# Update a secret
flyctl secrets set API_KEY="new-value"

# Remove a secret
flyctl secrets unset OLD_KEY
```

### Network Security

- All traffic encrypted with TLS
- Secrets never exposed in logs
- Private networking between services
- DDoS protection built-in

## 🔄 CI/CD Integration

### GitHub Actions

The included workflow (`.github/workflows/fly-deploy.yml`) automatically:
1. Builds Docker image
2. Deploys to Fly.io on push to main
3. Runs health checks
4. Reports deployment status

Setup:
```bash
# Add Fly token to GitHub secrets
# Go to: Settings → Secrets → Actions
# Add: FLY_API_TOKEN = your-token
```

## 🆘 Troubleshooting

### Common Issues

#### App Won't Start
```bash
# Check logs
flyctl logs --tail

# Common fixes:
# 1. Check PORT environment variable
# 2. Verify Docker image builds
# 3. Check memory limits
```

#### Storage Issues
```bash
# Check volume
flyctl volumes list

# Extend volume
flyctl volumes extend pcb_data --size 20
```

#### Performance Issues
```bash
# Scale up
flyctl scale vm performance-2x

# Add more instances
flyctl scale count 3
```

## 📚 Advanced Features

### Custom Domains

```bash
# Add custom domain
flyctl certs add pcb.yourdomain.com

# View certificate status
flyctl certs show pcb.yourdomain.com
```

### Database Integration

```bash
# Create Postgres cluster
flyctl postgres create --name pcb-db

# Connect to database
flyctl postgres connect -a pcb-db
```

### Scheduled Jobs

Add to fly.toml:
```toml
[processes]
  web = "python -m pcb_pipeline.web_api"
  worker = "python -m pcb_pipeline.scheduled_jobs"
```

## 🎯 Next Steps

1. **Monitor Usage**: Check metrics dashboard
2. **Set Alerts**: Configure uptime monitoring
3. **Optimize Performance**: Tune auto-scaling
4. **Add CDN**: Use Fly's edge caching
5. **Enable Analytics**: Track API usage

## 📞 Support Resources

- **Fly.io Docs**: [fly.io/docs](https://fly.io/docs)
- **Community**: [community.fly.io](https://community.fly.io)
- **Status Page**: [status.fly.io](https://status.fly.io)
- **PCB Pipeline Issues**: [GitHub Issues](https://github.com/murr2k/pcb-automation-pipeline/issues)

---

**Your PCB Pipeline is now globally deployed!** 🚀

Access your API at: https://pcb-automation-pipeline.fly.dev

API Documentation: https://pcb-automation-pipeline.fly.dev/docs