document.addEventListener("DOMContentLoaded", function () {
  function waitForMap(retries = 20, delay = 200) {
    let attempt = 0;

    const interval = setInterval(() => {
      let leafletMap = null;
      for (let key in window) {
        if (window[key] instanceof L.Map) {
          leafletMap = window[key];
          break;
        }
      }

      if (leafletMap) {
        clearInterval(interval);
        setupDrawing(leafletMap);
      } else {
        attempt++;
        if (attempt >= retries) {
          clearInterval(interval);
          alert("Could not detect Leaflet map.");
        }
      }
    }, delay);
  }

  function setupDrawing(map) {
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: true,
        rectangle: true,
        circle: true,
        marker: false,
        circlemarker: false,
        polyline: false
      },
      edit: {
        featureGroup: drawnItems
      }
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, function (e) {
      drawnItems.addLayer(e.layer);
    });

    document.getElementById("submit-btn").onclick = function () {
      const polygons = [];

      drawnItems.eachLayer(function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
          const latlngs = layer.getLatLngs()[0];  // Outer ring
          const coords = latlngs.map(latlng => [latlng.lng, latlng.lat]);
          // Close the polygon ring
          if (coords.length > 2 && coords[0][0] !== coords.at(-1)[0] && coords[0][1] !== coords.at(-1)[1]) {
            coords.push(coords[0]);
          }
          polygons.push(coords);
        }
      });

      fetch("/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ bbox: polygons })
      }).then(response => {
        if (response.ok) {
          alert("Bounding boxes submitted! You may now close the browser session.");
        }
      });
    };
  }

  waitForMap();
});

