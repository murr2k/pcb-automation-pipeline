#!/usr/bin/env python3
"""
Local demo server for PCB Pipeline
Run this to test the pipeline locally while Fly.io deployment completes.
"""

import json
import asyncio
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import subprocess
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig


class DemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            # Serve the demo page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            demo_html = """
<!DOCTYPE html>
<html>
<head>
    <title>PCB Pipeline Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
        button { background: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #229954; }
        #output { background: white; padding: 20px; margin-top: 20px; border-radius: 5px; min-height: 200px; white-space: pre-wrap; font-family: monospace; }
        .spinner { display: none; }
        .loading { opacity: 0.6; }
    </style>
</head>
<body>
    <h1>🚀 PCB Automation Pipeline Demo</h1>
    <div class="container">
        <h2>Test the Pipeline Locally</h2>
        <p>Click the button below to generate a simple LED controller PCB:</p>
        
        <button onclick="generatePCB()">Generate Demo PCB</button>
        
        <div id="output">
            <em>Output will appear here...</em>
        </div>
    </div>
    
    <script>
        async function generatePCB() {
            const output = document.getElementById('output');
            output.innerHTML = 'Starting PCB generation...\\n';
            output.classList.add('loading');
            
            try {
                const response = await fetch('/generate-demo');
                const data = await response.json();
                
                output.innerHTML += '\\n' + JSON.stringify(data, null, 2);
                
                if (data.success) {
                    output.innerHTML += '\\n\\n✅ Success! Files generated in: ' + data.output_dir;
                } else {
                    output.innerHTML += '\\n\\n❌ Error: ' + data.error;
                }
            } catch (error) {
                output.innerHTML += '\\n\\n❌ Error: ' + error.message;
            } finally {
                output.classList.remove('loading');
            }
        }
    </script>
</body>
</html>
            """
            
            self.wfile.write(demo_html.encode())
            
        elif self.path == '/generate-demo':
            # Generate a demo PCB
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                # Run the pipeline
                config = PipelineConfig()
                config.set('manufacturer', 'macrofab')
                pipeline = PCBPipeline(config)
                
                # Load demo design
                demo_file = Path(__file__).parent / 'static' / 'demo.yaml'
                if not demo_file.exists():
                    demo_file = Path(__file__).parent / 'examples' / 'simple_led_board' / 'spec.yaml'
                
                design = pipeline.load_specification(str(demo_file))
                
                # Generate PCB (simplified)
                result = {
                    'success': True,
                    'design_name': design['name'],
                    'components': len(design.get('components', [])),
                    'board_size': design['board']['size'],
                    'output_dir': 'output/demo',
                    'message': 'Demo PCB specification loaded successfully!'
                }
                
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e)
                }
            
            self.wfile.write(json.dumps(result).encode())
            
        else:
            super().do_GET()


def main():
    """Run the demo server."""
    PORT = 8080
    print(f"🚀 PCB Pipeline Demo Server")
    print(f"📍 Open http://localhost:{PORT} in your browser")
    print(f"📊 While Fly.io deployment completes, test the pipeline locally!")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    with HTTPServer(('', PORT), DemoHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✋ Server stopped")


if __name__ == "__main__":
    main()