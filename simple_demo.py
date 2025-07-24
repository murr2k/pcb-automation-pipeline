#!/usr/bin/env python3
"""
Simple demo server for PCB Pipeline - no dependencies required
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os

class SimpleDemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PCB Pipeline Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
        h1 { margin: 0 0 1rem 0; }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .demo-button {
            background: #27ae60;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .demo-button:hover {
            background: #229954;
            transform: translateY(-2px);
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        .feature {
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        #output {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-top: 1rem;
            font-family: monospace;
            white-space: pre-wrap;
            min-height: 100px;
        }
        .api-status {
            padding: 1rem;
            background: #e8f5e9;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 PCB Automation Pipeline</h1>
        <p style="font-size: 1.2rem; margin: 0;">Transform YAML specifications into production-ready PCBs in minutes</p>
    </div>

    <div class="container">
        <h2>Live Demo</h2>
        <p>Experience the power of automated PCB design. Click below to see how a simple YAML specification becomes a complete circuit board design.</p>
        
        <div style="text-align: center; margin: 2rem 0;">
            <button class="demo-button" onclick="runDemo()">Generate Demo PCB</button>
        </div>
        
        <div id="output">Ready to generate PCB...</div>
    </div>

    <div class="container">
        <h2>How It Works</h2>
        <div class="feature-grid">
            <div class="feature">
                <div class="feature-icon">📝</div>
                <h3>1. Define YAML</h3>
                <p>Simple component and connection definitions</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <h3>2. AI Optimization</h3>
                <p>Smart placement and routing algorithms</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🏭</div>
                <h3>3. Multi-Manufacturer</h3>
                <p>Instant quotes from 5+ PCB fabs</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📦</div>
                <h3>4. Ready to Order</h3>
                <p>Complete manufacturing files generated</p>
            </div>
        </div>
    </div>

    <div class="container">
        <h2>Example YAML Input</h2>
        <pre>name: LED Controller
board:
  size: [50, 40]  # mm
  layers: 2

components:
  - type: microcontroller
    value: ATmega328P
    package: TQFP-32
    
  - type: led
    value: LED_RED
    package: LED_0805
    
  - type: resistor
    value: 330R
    package: R_0805

connections:
  - net: VCC
    connect: ["U1.VCC", "C1.1", "J1.VBUS"]
    
  - net: LED1
    connect: ["U1.PB0", "R1.1"]</pre>
    </div>

    <div class="container">
        <h2>API Status</h2>
        <div class="api-status">
            <strong>🌐 Fly.io Deployment:</strong> <span id="deploy-status">Building Docker image...</span><br>
            <strong>📍 Local Demo:</strong> <span style="color: green;">Running on port 8765</span><br>
            <strong>🔗 Production URL:</strong> <a href="https://pcb-automation-pipeline.fly.dev" target="_blank">https://pcb-automation-pipeline.fly.dev</a>
        </div>
    </div>

    <script>
        function runDemo() {
            const output = document.getElementById('output');
            output.textContent = 'Starting PCB generation...\\n\\n';
            
            // Simulate the pipeline stages
            const stages = [
                { delay: 500, message: '📝 Loading YAML specification...' },
                { delay: 1000, message: '✅ Design validated: LED Controller (50x40mm, 2 layers)' },
                { delay: 1500, message: '🔧 Generating schematic...' },
                { delay: 2000, message: '✅ Schematic complete: 3 components, 5 nets' },
                { delay: 2500, message: '🤖 Running AI placement optimizer...' },
                { delay: 3000, message: '✅ Optimal placement found (thermal score: 95/100)' },
                { delay: 3500, message: '🔀 Auto-routing PCB...' },
                { delay: 4000, message: '✅ Routing complete: 100% success, 0 vias' },
                { delay: 4500, message: '🏭 Getting manufacturer quotes...' },
                { delay: 5000, message: '💰 MacroFab: $12.50 (5 days)' },
                { delay: 5200, message: '💰 JLCPCB: $8.90 (7 days)' },
                { delay: 5400, message: '💰 PCBWay: $15.00 (5 days)' },
                { delay: 6000, message: '\\n✨ PCB generation complete!' },
                { delay: 6100, message: 'Files ready: gerbers.zip, bom.csv, pick_place.csv' }
            ];
            
            stages.forEach(stage => {
                setTimeout(() => {
                    output.textContent += stage.message + '\\n';
                    output.scrollTop = output.scrollHeight;
                }, stage.delay);
            });
        }
        
        // Check deployment status
        async function checkDeployment() {
            try {
                const response = await fetch('https://pcb-automation-pipeline.fly.dev/health');
                if (response.ok) {
                    document.getElementById('deploy-status').innerHTML = '<span style="color: green;">✅ Deployed and running!</span>';
                }
            } catch (e) {
                // Still building
            }
        }
        
        // Check every 30 seconds
        checkDeployment();
        setInterval(checkDeployment, 30000);
    </script>
</body>
</html>
            """
            
            self.wfile.write(html.encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "server": "local_demo"}).encode())
            
        else:
            self.send_error(404)

def main():
    PORT = 8765
    print(f"🚀 PCB Pipeline Demo Server")
    print(f"📍 Open http://localhost:{PORT} in your browser")
    print(f"✨ Simple demo - no dependencies required!")
    print(f"\nPress Ctrl+C to stop\n")
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with HTTPServer(('', PORT), SimpleDemoHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n✋ Server stopped")

if __name__ == "__main__":
    main()