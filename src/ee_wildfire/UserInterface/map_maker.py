from flask import Flask, render_template, request, jsonify, cli
import threading
import webbrowser
import time
import folium
import tempfile
import geemap
from folium.plugins import Draw

from ee_wildfire.constants import *
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.UserConfig.UserConfig import UserConfig

import ee

from typing import List

app = Flask(__name__)
bbox_coords = None


@app.route("/")
def index():
    return render_template("map.html")  # Load the cleaned-up HTML

# @app.route("/submit", methods=["POST"])
# def submit():
#     global bbox_coords
#     data = request.get_json()
#     bbox_coords = data.get("bbox")
#     ConsoleUI.print(f"Received bounding box")
#     ConsoleUI.log(f"Bounding box: {bbox_coords}")
#     return jsonify(success=True)

@app.route("/submit", methods=["POST"])
def submit():
    global bbox_coords
    data = request.get_json()
    raw_bbox = data.get("bbox")

    if not raw_bbox:
        ConsoleUI.error("Invalid bounding box recieved from flask server.")
        return jsonify(success=False, error="Invalid bounding box received")

    # complete the circle
    ConsoleUI.debug(f"map maker first point before fix: {raw_bbox[0][0]}")
    ConsoleUI.debug(f"map maker last point before fix: {raw_bbox[0][-1]}")
    ConsoleUI.debug(f"map maker complete points before fix? {raw_bbox[0][0] == raw_bbox[0][-1]}")

    if raw_bbox[0][0] != raw_bbox[0][-1]:
        ConsoleUI.debug(f"map maker, circle incomplete appending point: {raw_bbox[0][0]}")
        raw_bbox[0].append(raw_bbox[0][0])

    ConsoleUI.debug(f"map maker first point after fix: {raw_bbox[0][0]}")
    ConsoleUI.debug(f"map maker last point after fix: {raw_bbox[0][-1]}")
    ConsoleUI.debug(f"map maker complete points after fix? {raw_bbox[0][0] == raw_bbox[0][-1]}")

    ConsoleUI.debug(f"map maker raw bbox: {raw_bbox}")
    bbox_coords = raw_bbox

    ConsoleUI.print(f"Received bounding box")
    ConsoleUI.log(f"Bounding box polygon: {bbox_coords}")
    return jsonify(success=True)

def setup_logging(user_config: UserConfig):

    flask_loggers = ['werkzeug', 'flask.app']

    for name in flask_loggers:
        logger = logging.getLogger(name)
        logger.handers = []
        logger.setLevel(LOG_LEVELS[user_config.log_level])
        logger.propagate = False

        handlers = ConsoleUI.get_log_handlers()

        if handlers:
            for handler in handlers:
                logger.addHandler(handler)

def get_map_html():
    ConsoleUI.print("Generating HTML")
    mapObj = folium.Map(location=USA_CENTER)

    mapObj.get_root().html.add_child(folium.Element(
        """
        <div style="position:fixed;left:70px;top:150px;height:100px;z-index:900">
        <button id="submit-btn">Submit</button>
        </div>
        <script src="/static/js/draw_handler.js"></script>
        """
    ))

    draw = Draw(
        export=False, 
        draw_options={
            'polyline': False,
            # 'rectangle': True,
            # 'polygon': True,
            # 'circle': True,
            'marker': False,
            'circlemarker': False,
        },
        )
    draw.add_to(mapObj)


    mapObj.save(TEMPLATE_DIR / "map.html")

def launch_draw_map() -> List:
    ConsoleUI.print("Launching web browser")
    global bbox_coords
    bbox_coords = None

    def run():
        cli.show_server_banner = lambda *args, **kwargs:None
        app.run(port=5000, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    # FIX: check for webbrowser access
    time.sleep(1)  # Give server time to start
    webbrowser.open("http://127.0.0.1:5000")

    # Wait until user submits bbox
    while bbox_coords is None:
        time.sleep(0.5)

    return bbox_coords

def show_bbox_on_map(bbox: List, center=None, zoom=8):
    """Display the bounding box in a standalone browser window."""
    bbox = ee.Geometry.Polygon(bbox) # type: ignore
    if center is None:
        coords = bbox.bounds().coordinates().getInfo()[0]
        lons = [pt[0] for pt in coords]
        lats = [pt[1] for pt in coords]
        center = [(max(lats) + min(lats)) / 2, (max(lons) + min(lons)) / 2]

    # Create map
    m = geemap.Map(center=center, zoom=zoom)
    m.addLayer(bbox, {}, 'Bounding Box')
    m.addLayerControl()

    # Export to HTML and open in browser
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        m.save(tmp.name)
        webbrowser.open(f"file://{tmp.name}")
if __name__ == "__main__":
    ConsoleUI.setup_logging(log_dir=DEFAULT_LOG_DIR, log_level="info")
    get_map_html()
    launch_draw_map()
