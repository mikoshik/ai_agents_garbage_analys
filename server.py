import os
import json
import http.server
import socketserver
from datetime import datetime

PORT = 8060
SCANS_DIR = "scans"
ASSETS_DIR = "assets"

# Ensure directories exist
os.makedirs(SCANS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/scans":
            scans = []
            if os.path.exists(SCANS_DIR):
                for filename in os.listdir(SCANS_DIR):
                    if filename.endswith(".json"):
                        try:
                            with open(os.path.join(SCANS_DIR, filename), "r", encoding="utf-8") as f:
                                data = json.load(f)
                                scans.append(data)
                        except Exception as e:
                            print(f"Error loading {filename}: {e}")
            
            scans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(scans).encode('utf-8'))
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.render_dashboard().encode('utf-8'))
        else:
            # Check if file exists to avoid 404 error page from my side
            # SimpleHTTPRequestHandler will handle the file serving correctly
            return super().do_GET()

    def render_dashboard(self):
        # Load all scans
        scans = []
        if os.path.exists(SCANS_DIR):
            for filename in os.listdir(SCANS_DIR):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(SCANS_DIR, filename), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            scans.append(data)
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
        
        # Sort by timestamp (newest first)
        scans.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Style & Layout
        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Eco-Agent Dashboard</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
            <meta http-equiv="refresh" content="30"> <!-- Fallback refresh every 30s -->
            <script>
                // Simple polling to check for new scans
                let lastScanCount = {len(scans)};
                async function checkForUpdates() {
                    try {
                        const response = await fetch('/');
                        const text = await response.text();
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(text, 'text/html');
                        const currentScanCount = doc.querySelectorAll('.card').length;
                        
                        if (currentScanCount > lastScanCount) {
                            console.log("New scan detected! Reloading...");
                            window.location.reload();
                        }
                    } catch (e) { console.error("Poll failed", e); }
                }
                setInterval(checkForUpdates, 3000); // Check every 3 seconds
            </script>
            <style>
                :root {
                    --bg-color: #0f172a;
                    --card-bg: #1e293b;
                    --accent: #22c55e;
                    --text: #f8fafc;
                }
                body {
                    background-color: var(--bg-color);
                    color: var(--text);
                    font-family: 'Inter', sans-serif;
                    margin: 0;
                    padding: 20px;
                }
                header {
                    text-align: center;
                    padding: 40px 0;
                }
                h1 {
                    font-weight: 600;
                    color: var(--accent);
                    margin-bottom: 10px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 25px;
                }
                .card {
                    background: var(--card-bg);
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
                    transition: transform 0.3s ease;
                    border: 1px solid rgba(255,255,255,0.1);
                }
                .card:hover {
                    transform: translateY(-5px);
                    border-color: var(--accent);
                }
                .card img {
                    width: 100%;
                    height: auto;
                    display: block;
                }
                .card-content {
                    padding: 20px;
                }
                .card-title {
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin: 0 0 10px 0;
                }
                .meta {
                    font-size: 0.85rem;
                    color: #94a3b8;
                    margin-bottom: 15px;
                }
                .badge {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    margin-bottom: 15px;
                }
                .badge-yes { background: #14532d; color: #4ade80; }
                .badge-no { background: #7f1d1d; color: #f87171; }
                
                .property {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-size: 0.9rem;
                }
                .prop-label { color: #94a3b8; }
                .desc {
                    margin-top: 15px;
                    font-size: 0.85rem;
                    line-height: 1.5;
                    border-top: 1px solid rgba(255,255,255,0.1);
                    padding-top: 10px;
                    color: #cbd5e1;
                }
            </style>
        </head>
        <body>
            <header>
                <h1>🌿 Eco-Agent Scanner</h1>
                <p>История классификации отходов в реальном времени</p>
            </header>
            <div class="container">
        """

        if not scans:
            html += "<p style='grid-column: 1/-1; text-align: center; color: #64748b;'>Пока нет сохраненных результатов. Запустите анализ!</p>"

        for scan in scans:
            # Try both possible keys for backward compatibility
            img_path = scan.get("image") or scan.get("image_path") or ""
            res = scan.get("result", {})
            ts = scan.get("timestamp", "")
            try:
                date_str = datetime.fromisoformat(ts).strftime("%d.%m.%Y %H:%M:%S")
            except:
                date_str = ts

            html += f"""
                <div class="card">
                    <img src="{img_path}" alt="Object Image">
                    <div class="card-content">
                        <div class="card-title">{res.get('item_name', 'Unknown object').capitalize()}</div>
                        <div class="meta">{date_str}</div>
                        
                        <div class="property">
                            <span class="prop-label">Материал:</span>
                            <span>{res.get('material', '???')}</span>
                        </div>
                        <div class="property">
                            <span class="prop-label">Категория:</span>
                            <span>{res.get('category', '???')}</span>
                        </div>
                        
                        <div class="desc">
                            {res.get('description', 'No description available')}
                        </div>

                        <div style="margin-top: 15px; font-size: 0.75rem; color: #64748b; display: flex; gap: 15px; border-top: 1px dashed rgba(255,255,255,0.05); padding-top: 10px;">
                            <span>⏱️ {scan.get('metadata', {}).get('time_sec', '?.?')}s</span>
                            <span>💾 {scan.get('metadata', {}).get('memory_mb', '???')} MB</span>
                        </div>
                    </div>
                </div>
            """

        html += """
            </div>
            <footer style="text-align: center; margin-top: 50px; color: #64748b; font-size: 0.8rem;">
                Built with Native Python http.server & Llama.cpp
            </footer>
        </body>
        </html>
        """
        return html

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    import socket
    
    # Try to find local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"

    Handler = DashboardHandler
    with ThreadedHTTPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"\n" + "="*50)
        print(f"🚀 Eco-Agent Dashboard is ONLINE!")
        print(f"📲 Local access:  http://localhost:{PORT}")
        print(f"🌐 Network access: http://{local_ip}:{PORT}")
        print("="*50 + "\n")
        print("Нажми Ctrl+C, чтобы остановить сервер.")
        httpd.serve_forever()
