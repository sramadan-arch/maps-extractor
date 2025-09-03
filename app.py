import os
import subprocess

# Ensure Playwright Chromium is installed in deployment
if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    subprocess.run(["playwright", "install", "chromium"])

import re
import asyncio
from flask import Flask, request, jsonify, render_template_string
from playwright.async_api import async_playwright

app = Flask(__name__)

# ---------------------------
# Helper: extract coordinates
# ---------------------------
def extract_coords_from_url(url: str):
    match_3d4d = re.search(r'!3d([-0-9.]+)!4d([-0-9.]+)', url)
    if match_3d4d:
        return round(float(match_3d4d.group(1)), 7), round(float(match_3d4d.group(2)), 7)

    match_at = re.search(r'@([-0-9.]+),([-0-9.]+)', url)
    if match_at:
        return round(float(match_at.group(1)), 7), round(float(match_at.group(2)), 7)

    match_q = re.search(r'[?&]q=([-0-9.]+),([-0-9.]+)', url)
    if match_q:
        return round(float(match_q.group(1)), 7), round(float(match_q.group(2)), 7)

    return None, None


# ---------------------------
# Helper: expand short link
# ---------------------------
async def expand_link(link, page):
    await page.goto(link, timeout=60000)
    await asyncio.sleep(2)
    final_url = page.url
    return extract_coords_from_url(final_url)


# ---------------------------
# Process multiple links
# ---------------------------
async def process_links(links):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for link in links:
            link = link.strip()
            if not link:
                continue
            try:
                lat, lng = await expand_link(link, page)
                results.append({"link": link, "latitude": lat, "longitude": lng})
            except Exception as e:
                results.append({"link": link, "latitude": None, "longitude": None, "error": str(e)})

        await browser.close()
    return results


# ---------------------------
# API Endpoint
# ---------------------------
@app.route("/extract", methods=["POST"])
def extract():
    data = request.json
    links = data.get("links", [])
    results = asyncio.run(process_links(links))
    return jsonify(results)


# ---------------------------
# Web UI
# ---------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Google Maps Coordinate Extractor</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; }
    textarea { width: 100%; height: 150px; margin-bottom: 10px; }
    button { margin: 5px 5px 15px 0; padding: 10px 18px; cursor: pointer; }
    table { border-collapse: collapse; margin-top: 20px; width: 100%; }
    table, th, td { border: 1px solid #ccc; padding: 8px; }
    th { background-color: #f0f0f0; }
  </style>
</head>
<body>
  <h2>Google Maps Coordinate Extractor</h2>
  <p>Paste Google Maps links (one per line):</p>
  <textarea id="links"></textarea><br>
  <button onclick="extract()">Extract Coordinates</button>
  <button onclick="downloadCSV()">Save as CSV</button>

  <table id="results"></table>

  <script>
    async function extract() {
      const links = document.getElementById("links").value.trim().split("\\n");
      if (links.length === 0) {
        alert("Please paste at least one link.");
        return;
      }

      const response = await fetch("/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ links })
      });

      const results = await response.json();
      const table = document.getElementById("results");
      table.innerHTML = "<tr><th>Link</th><th>Latitude</th><th>Longitude</th></tr>";

      results.forEach(r => {
        table.innerHTML += `<tr>
          <td>${r.link}</td>
          <td>${r.latitude ?? "N/A"}</td>
          <td>${r.longitude ?? "N/A"}</td>
        </tr>`;
      });

      window._results = results; // keep for CSV
    }

    function downloadCSV() {
      if (!window._results) {
        alert("No results yet!");
        return;
      }
      let csv = "Link,Latitude,Longitude\\n";
      window._results.forEach(r => {
        csv += `${r.link},${r.latitude ?? ""},${r.longitude ?? ""}\\n`;
      });

      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "coordinates.csv";
      a.click();
      URL.revokeObjectURL(url);
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
  import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "App is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




