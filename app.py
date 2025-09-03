import os
import io
import csv
import json
from flask import Flask, render_template_string, request, send_file
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# HTML Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Google Maps Link → Coordinates</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    textarea { width: 100%; padding: 10px; }
    button { padding: 10px 20px; margin-top: 10px; }
    table { border-collapse: collapse; margin-top: 20px; width: 100%; }
    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
    th { background-color: #f4f4f4; }
  </style>
</head>
<body>
  <h2>Paste Google Maps Short Links</h2>
  <form method="POST" action="/extract">
    <textarea name="links" rows="6" placeholder="Paste Google Maps short links here..."></textarea><br>
    <button type="submit">Extract Coordinates</button>
  </form>
  {% if results %}
    <h3>Results:</h3>
    <table>
      <tr><th>Link</th><th>Latitude</th><th>Longitude</th></tr>
      {% for row in results %}
        <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td></tr>
      {% endfor %}
    </table>
    <form method="POST" action="/download">
      <input type="hidden" name="data" value="{{ results|tojson }}">
      <button type="submit">Download as CSV</button>
    </form>
  {% endif %}
</body>
</html>
"""

# Extract coordinates with Playwright
def extract_coordinates(url):
    try:
        # Force Playwright to use Replit's temporary path
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/playwright"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)  # 20s timeout
            page.wait_for_timeout(3000)    # wait for redirect
            final_url = page.url
            browser.close()

        if "/@" in final_url:
            coords = final_url.split("/@")[1].split("/")[0].split(",")
            return coords[0], coords[1]
        return None, None
    except Exception as e:
        return None, None

# Routes
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/extract", methods=["POST"])
def extract():
    links = request.form["links"].strip().splitlines()
    results = []
    for link in links:
        lat, lon = extract_coordinates(link.strip())
        results.append([link, lat, lon])
    return render_template_string(HTML_TEMPLATE, results=results)

@app.route("/download", methods=["POST"])
def download():
    data = json.loads(request.form["data"])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Link", "Latitude", "Longitude"])
    writer.writerows(data)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="coordinates.csv"
    )

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # default for Replit
    app.run(host="0.0.0.0", port=port)
