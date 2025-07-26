# Visual Design Review Options for PCB Automation Pipeline

## Can KiCad GUI Run in Docker?

**Yes**, the KiCad Docker image can run the native GUI, but with important caveats:

### ✅ GUI via X11 Forwarding (Linux/macOS)

The docker-compose.yml already includes display settings:
```yaml
environment:
  - DISPLAY=${DISPLAY}
  - QT_X11_NO_MITSHM=1
```

#### Linux Setup:
```bash
# Allow X11 connections
xhost +local:docker

# Run KiCad GUI from Docker
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  kicad

# Open generated files
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  kicad /output/project_name/project_name.kicad_pro
```

#### macOS Setup (requires XQuartz):
```bash
# Install XQuartz
brew install --cask xquartz

# Start XQuartz and enable connections
open -a XQuartz
# In XQuartz preferences: Security → Allow connections from network clients

# Get IP and set DISPLAY
IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
export DISPLAY=$IP:0

# Run with additional settings
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  kicad
```

#### Windows Setup (WSL2 + WSLg):
```bash
# WSL2 with WSLg supports GUI apps natively
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -e WAYLAND_DISPLAY=$WAYLAND_DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /mnt/wslg:/mnt/wslg \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  kicad
```

## Alternative Visual Review Methods

### 1. 🖼️ **3D Render Export** (Recommended)
Generate static 3D views and 2D plots automatically:

```python
# Add to pipeline.py
def export_visual_review(pcb_path, output_dir):
    """Export visual review files"""
    import pcbnew
    
    board = pcbnew.LoadBoard(pcb_path)
    
    # Export 3D view (VRML)
    vrml_path = os.path.join(output_dir, "board_3d.wrl")
    board.Export3DModel(vrml_path)
    
    # Export PDF plots
    plot_controller = pcbnew.PLOT_CONTROLLER(board)
    plot_options = plot_controller.GetPlotOptions()
    
    # Configure plot settings
    plot_options.SetOutputDirectory(output_dir)
    plot_options.SetPlotFrameRef(False)
    plot_options.SetPlotValue(True)
    plot_options.SetPlotReference(True)
    plot_options.SetPlotInvisibleText(False)
    plot_options.SetPlotViaOnMaskLayer(False)
    plot_options.SetExcludeEdgeLayer(True)
    plot_options.SetMirror(False)
    plot_options.SetUseAuxOrigin(False)
    plot_options.SetScale(1)
    plot_options.SetAutoScale(True)
    plot_options.SetPlotMode(pcbnew.PLOT_MODE_FILLED)
    
    # Plot all copper layers
    for layer_info in board.GetEnabledLayers().CuStack():
        plot_controller.SetLayer(layer_info)
        plot_controller.OpenPlotfile(
            board.GetLayerName(layer_info),
            pcbnew.PLOT_FORMAT_PDF,
            "PCB Layer"
        )
        plot_controller.PlotLayer()
    
    plot_controller.ClosePlot()
    
    # Export assembly drawings
    plot_options.SetPlotReference(True)
    plot_options.SetPlotValue(True)
    plot_controller.SetLayer(pcbnew.F_Fab)
    plot_controller.OpenPlotfile("Assembly_Top", pcbnew.PLOT_FORMAT_PDF, "Assembly")
    plot_controller.PlotLayer()
    
    return {
        "3d_model": vrml_path,
        "pdf_plots": glob.glob(os.path.join(output_dir, "*.pdf"))
    }
```

### 2. 🌐 **Web-Based Viewer**
Implement an interactive web viewer:

```python
# web_viewer.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import three_js_pcb_viewer  # Custom module

@app.get("/view/{job_id}")
async def view_pcb(job_id: str):
    """Interactive 3D PCB viewer"""
    vrml_path = f"/output/{job_id}/board_3d.wrl"
    
    return HTMLResponse(f"""
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/three@0.150.0/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.150.0/examples/js/loaders/VRMLLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.150.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="viewer" style="width: 100%; height: 100vh;"></div>
        <script>
            // Three.js PCB viewer implementation
            const viewer = new PCBViewer('viewer');
            viewer.loadVRML('{vrml_path}');
        </script>
    </body>
    </html>
    """)
```

### 3. 📸 **Automated Screenshots**
Generate review images without GUI:

```python
# screenshot_generator.py
def generate_pcb_screenshots(kicad_pcb_path):
    """Generate PCB screenshots using KiCad Python API"""
    import pcbnew
    from PIL import Image
    
    board = pcbnew.LoadBoard(kicad_pcb_path)
    
    # Configure plot controller for image export
    pctl = pcbnew.PLOT_CONTROLLER(board)
    popt = pctl.GetPlotOptions()
    
    # Set image parameters
    popt.SetOutputDirectory("./screenshots/")
    popt.SetPlotFrameRef(False)
    popt.SetScale(2)  # 2x resolution
    popt.SetMirror(False)
    popt.SetUseAuxOrigin(False)
    
    screenshots = []
    
    # Top view
    popt.SetDrillMarksType(pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE)
    pctl.SetColorMode(True)
    
    for layer_name, layer_id in [
        ("Top", pcbnew.F_Cu),
        ("Bottom", pcbnew.B_Cu),
        ("Top_Assembly", pcbnew.F_Fab),
        ("3D_Top", None),  # Special handling for 3D
        ("3D_Bottom", None)
    ]:
        if layer_id is not None:
            pctl.SetLayer(layer_id)
            pctl.OpenPlotfile(layer_name, pcbnew.PLOT_FORMAT_SVG, layer_name)
            pctl.PlotLayer()
            pctl.ClosePlot()
            
            # Convert SVG to PNG
            svg_path = f"./screenshots/{layer_name}.svg"
            png_path = f"./screenshots/{layer_name}.png"
            # Use cairosvg or similar to convert
            screenshots.append(png_path)
    
    return screenshots
```

### 4. 🔍 **KiCad Viewer Mode** (Lightweight)
Use KiCad's built-in viewers without full GUI:

```bash
# Create viewer script
cat > view_design.sh << 'EOF'
#!/bin/bash
DESIGN_PATH=$1

# Use pcbnew in scripting mode to export views
docker run -it --rm \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  python3 -c "
import pcbnew
board = pcbnew.LoadBoard('/output/${DESIGN_PATH}')
# Export to various formats for review
"

# Use gerbv for Gerber preview (lightweight)
docker run -it --rm \
  -v $(pwd)/output:/output \
  gerbv:latest \
  gerbv /output/${DESIGN_PATH}/gerbers/*.gbr

# Use KiCad's built-in 3D viewer in standalone mode
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/output:/output \
  kicad/kicad:nightly-full-trixie \
  pcbnew --frame 3d_viewer /output/${DESIGN_PATH}/board.kicad_pcb
EOF
chmod +x view_design.sh
```

### 5. 📄 **Automated Review Reports**
Generate comprehensive PDF reports:

```python
# review_report_generator.py
def generate_review_report(job_id):
    """Create PDF review report with all design aspects"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Image, Table
    
    doc = SimpleDocTemplate(f"output/{job_id}/review_report.pdf")
    story = []
    
    # Add screenshots
    for img in ["top_copper.png", "bottom_copper.png", "3d_view.png"]:
        story.append(Image(f"output/{job_id}/{img}", width=400, height=300))
    
    # Add component table
    components = load_bom(f"output/{job_id}/bom.csv")
    story.append(Table(components))
    
    # Add design stats
    stats = calculate_board_stats(f"output/{job_id}/board.kicad_pcb")
    story.append(Table([
        ["Board Size", f"{stats['width']}mm x {stats['height']}mm"],
        ["Layer Count", stats['layers']],
        ["Component Count", stats['components']],
        ["Track Count", stats['tracks']],
        ["Via Count", stats['vias']]
    ]))
    
    doc.build(story)
    return f"output/{job_id}/review_report.pdf"
```

## Recommended Workflow

### 1. **Development Phase**
- Use Docker with X11 forwarding for full KiCad GUI
- Iterate on designs with visual feedback

### 2. **CI/CD Pipeline**
- Generate automated screenshots
- Export 3D models and PDF plots
- Create review reports

### 3. **Pre-Production Review**
- Web-based 3D viewer for stakeholders
- PDF reports for documentation
- Gerber viewers for final verification

### 4. **Implementation Priority**
1. **Immediate**: Add PDF plot generation to pipeline
2. **Short-term**: Implement web-based 3D viewer
3. **Medium-term**: Create automated screenshot generation
4. **Long-term**: Build comprehensive review dashboard

## Docker Commands for GUI Access

```bash
# Helper script for KiCad GUI
cat > kicad-gui.sh << 'EOF'
#!/bin/bash
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd)/output:/output:rw \
  -v $(pwd)/designs:/designs:ro \
  --name kicad-gui \
  kicad/kicad:nightly-full-trixie \
  kicad $1
EOF
chmod +x kicad-gui.sh

# Usage
./kicad-gui.sh  # Open KiCad
./kicad-gui.sh /output/my_project/my_project.kicad_pro  # Open specific project
```

## Conclusion

While the KiCad Docker image **can** run the GUI through X11 forwarding, the most practical approach for production is to:

1. Use automated visual exports (PDF, 3D models, screenshots)
2. Implement a web-based viewer for easy access
3. Reserve GUI access for development/debugging
4. Focus on automated review reports for stakeholder approval

This provides the best balance of functionality, accessibility, and automation.