from flask import Flask, request, jsonify, render_template_string
from playwright.sync_api import sync_playwright
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)

# HTML template
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Google Maps Link Extractor</title>
</head>
<body>
    <h1>Paste Google Maps Short Links</h1>
    <form method="POST" action="/extract">
        <textarea name="links" rows="10" cols="80" placeholder="Paste Google Maps short links here..."></textarea><br>
        <button type="submit">Extract Coordinates</button>
    </form>
    {% if results %}
    <h2>Results:</h2>
    <table border="1">
        <tr><th>Link</th><th>Latitude</th><th>Longitude</th></tr>
        {% for row in results %}
        <tr>
            <td>{{ row['link'] }}</td>
            <td>{{ row['lat'] }}</td>
            <td>{{ row['lng'] }}</td>
        </tr>
        {% endfor %}
    </table>
    <form method="POST" action="/download">
        <input type="hidden" name="data" value="{{ results }}">
        <button type="submit">Download as CSV</button>
    </form>
    {% endif %}
</body>
</html>
"""

def extract_coordinates(links):
    coords = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for link in links:
            try:
                page.goto(link.strip(), timeout=60000)
                page.wait_for_load_state("networkidle")
                url = page.url  # final redirected URL

                # Parse latitude/longitude from the URL
                if "@"
 in url:
                    at_index = url.find("@")
                    parts = url[at_index+1:].split(",")
                    lat = parts[0]
                    lng = parts[1]
                else:
                    lat, lng = None, None

                coords.append({"link": link, "lat": lat, "lng": lng})
            except Exception as e:
                coords.append({"link": link, "lat": None, "lng": None})
        browser.close()
    return coords

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/extract", methods=["POST"])
def extract():
    links = request.form["links"].splitlines()
    results = extract_coordinates(links)
    return render_template_string(HTML_PAGE, results=results)

@app.route("/download", methods=["POST"])
def download():
    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["link", "lat", "lng"])
    writer.writeheader()
    # Retrieve results again (simplified for demo)
    # In production you would store session results instead
    data = request.form.get("data")
    output.write(data)
    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=coordinates.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
