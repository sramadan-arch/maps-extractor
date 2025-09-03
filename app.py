import os
from flask import Flask, render_template_string, request, send_file
import csv
import io
from playwright.sync_api import sync_playwright

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Google Maps Link → Coordinates</title>
</head>
<body>
  <h2>Paste Google Maps Short Links</h2>
  <form method="POST" action="/extract">
    <textarea name="links" rows="6" cols="60" placeholder="Paste links here..."></textarea><br><br>
    <button type="submit">Extract Coordinates</button>
  </form>
  {% if results %}
    <h3>Results:</h3>
    <table border="1">
      <tr><th>Link</th><th>Latitude</th><th>Longitude</th></tr>
      {% for row in results %}
      <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td></tr>
      {% endfor %}
    </table>
    <form method="POST" action="/download">
      <input type="hidden" name="data" value="{{ results|tojson }}">
      <button type="submit">Save as CSV</button>
    </form>
  {% endif %}
</body>
</html>
"""

def extract_coordinates(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)  # wait 3s for redirect
        final_url = page.url
        browser.close()

    if "/@" in final_url:
        try:
            coords = final_url.split("/@")[1].split("/")[0].split(",")
            return coords[0], coords[1]
        except:
            return None, None
    return None, None

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
    import json
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
