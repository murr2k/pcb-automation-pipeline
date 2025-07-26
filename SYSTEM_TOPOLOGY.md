# PCB Automation Pipeline - System Topology

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                   LOCAL DEVELOPMENT                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                            Developer Machine                                │   │
│  │                                                                             │   │
│  │  ┌───────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │   │
│  │  │   Python Files    │     │   Test Scripts   │     │  Demo Server     │    │   │
│  │  │                   │     │                  │     │                  │    │   │
│  │  │ • pipeline.py     │     │ • test_*.py      │     │ • demo_server.py │    │   │
│  │  │ • component_      │     │ • simple_demo.py │     │   (port 8765)    │    │   │
│  │  │   mapper.py       │     │                  │     │                  │    │   │
│  │  │ • web_api.py      │     └──────────────────┘     └──────────────────┘    │   │
│  │  │ • simple_app.py   │                                                      │   │
│  │  └───────────────────┘                                                      │   │
│  │           │                                                                 │   │
│  │           ▼                                                                 │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐      │   │
│  │  │                    Docker Environment (Local)                     │      │   │
│  │  │  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐  │      │   │
│  │  │  │ KiCad Container │    │  Pipeline API    │    │   Database   │  │      │   │
│  │  │  │                 │◄───│                  │    │              │  │      │   │
│  │  │  │ • Schematic Gen │    │ • FastAPI        │    │ • Component  │  │      │   │
│  │  │  │ • PCB Layout    │    │ • Port 8000      │    │   Cache      │  │      │   │
│  │  │  │ • Auto-routing  │    │ • Full Pipeline  │    │ • 89+ parts  │  │      │   │
│  │  │  └─────────────────┘    └──────────────────┘    └──────────────┘  │      │   │
│  │  └───────────────────────────────────────────────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ HTTPS
                                            ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                    FLY.IO CLOUD                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                     pcb-automation-pipeline.fly.dev                        │   │
│  │                                                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐      │   │
│  │  │              Simplified API Container (ACTIVE)                   │      │   │
│  │  │                                                                  │      │   │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐   │      │   │
│  │  │  │   simple_app.py │    │   Static Files  │    │   Endpoints │   │      │   │
│  │  │  │                 │    │                 │    │             │   │      │   │
│  │  │  │ • FastAPI       │    │ • index.html    │    │ • /health   │   │      │   │
│  │  │  │ • Port 8000     │    │ • demo.yaml     │    │ • /docs     │   │      │   │
│  │  │  │ • Health checks │    │                 │    │ • /api      │   │      │   │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────┘   │      │   │
│  │  │                                                                  │      │   │
│  │  │  Status: ✅ DEPLOYED & RUNNING                                   │      │   │
│  │  └──────────────────────────────────────────────────────────────────┘      │   │
│  │                                                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐      │   │
│  │  │          Full Pipeline Container (PENDING DEPLOYMENT)            │      │   │
│  │  │                                                                  │      │   │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐   │      │   │
│  │  │  │ Full Pipeline   │    │ KiCad Engine    │    │  Component  │   │      │   │
│  │  │  │                 │    │   (Docker)      │    │   Mapper    │   │      │   │
│  │  │  │ • web_api.py    │    │                 │    │             │   │      │   │
│  │  │  │ • All features  │    │ • ~2.5GB image  │    │ • LCSC API  │   │      │   │
│  │  │  │ • /designs/*    │    │ • PCB generation│    │ • Octopart  │   │      │   │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────┘   │      │   │
│  │  │                                                                  │      │   │
│  │  │  Status: ❌ BLOCKED (Docker PYTHONPATH issue)                    │      │   │
│  │  └──────────────────────────────────────────────────────────────────┘      │   │
│  │                                                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐      │   │
│  │  │                    Persistent Storage (10GB)                     │      │   │
│  │  │  • /data/output - Generated PCB files                            │      │   │
│  │  │  • /cache/components - Component mapping cache                   │      │   │
│  │  └──────────────────────────────────────────────────────────────────┘      │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │ API Calls
                                            ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   MacroFab   │  │     LCSC     │  │   Octopart   │  │    PCBWay    │          │
│  │     API      │  │     API      │  │     API      │  │     API      │          │
│  │              │  │              │  │              │  │              │          │
│  │ ✅ Key Set   │  │ 🔧 Planned  │  │ 🔧 Planned   │  │ 🔧 Planned   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────────────────────┘

## Connection Flow:

1. **Local Development** → **Fly.io**
   - Deploy via: `fly deploy --dockerfile Dockerfile.fly.staged`
   - Git push triggers CI/CD pipeline

2. **User Request** → **Fly.io API**
   - HTTPS requests to pcb-automation-pipeline.fly.dev
   - Currently: Simple API responds
   - Future: Full pipeline processes YAML → PCB

3. **Fly.io** → **External APIs**
   - Component lookup (LCSC, Octopart)
   - Manufacturing quotes (MacroFab, PCBWay)
   - Real-time pricing and availability

## Current State:
- ✅ Simple API: Live and healthy
- ❌ Full Pipeline: Deployment blocked by Docker module path issue
- 🔧 Fix Required: Update PYTHONPATH in Dockerfile.fly.full