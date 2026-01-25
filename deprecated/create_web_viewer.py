#!/usr/bin/env python3
"""
Create a standalone HTML viewer for embeddings
No Jupyter required - just open the HTML file in a browser
"""

import sys
import json
from pathlib import Path
import base64
from PIL import Image
import rasterio
from rasterio.warp import transform_bounds

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.viewport_utils import get_active_viewport

DATA_DIR = Path.home() / "blore_data"
PYRAMIDS_DIR = DATA_DIR / "pyramids"
YEARS = list(range(2017, 2025))

def get_image_bounds(image_path):
    """Get bounds of a GeoTIFF in lat/lon."""
    with rasterio.open(image_path) as src:
        bounds = src.bounds
        if str(src.crs) != 'EPSG:4326':
            bounds = transform_bounds(src.crs, 'EPSG:4326', *bounds)
        # Return as [[south, west], [north, east]] for Leaflet
        return [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]

def create_html_viewer(viewport_id=None, viewport_bounds=None):
    """Generate HTML file with 9 Leaflet maps."""

    # Use viewport-specific HTML filename
    if viewport_id:
        output_html = Path(f"{viewport_id}_viewer.html")
    else:
        output_html = Path("bangalore_viewer.html")

    # Calculate center and zoom from viewport bounds
    if viewport_bounds:
        # bounds format: (min_lat, min_lon, max_lat, max_lon)
        center = [
            (viewport_bounds[0] + viewport_bounds[2]) / 2,
            (viewport_bounds[1] + viewport_bounds[3]) / 2
        ]
        # Calculate appropriate zoom level based on bounds extent
        lat_extent = viewport_bounds[2] - viewport_bounds[0]
        lon_extent = viewport_bounds[3] - viewport_bounds[1]
        extent = max(lat_extent, lon_extent)
        if extent < 0.05:
            initial_zoom = 15
        elif extent < 0.1:
            initial_zoom = 14
        elif extent < 0.2:
            initial_zoom = 13
        else:
            initial_zoom = 12
        bounds = [[viewport_bounds[0], viewport_bounds[1]], [viewport_bounds[2], viewport_bounds[3]]]
    else:
        # Default Bangalore bounds for backwards compatibility
        center = [12.97, 77.59]
        initial_zoom = 12
        bounds = [[12.83, 77.46], [13.14, 77.78]]
        viewport_id = "bangalore"

    # Get bounds from one of the images
    sample_img = PYRAMIDS_DIR / "2024" / "level_4.tif"
    if sample_img.exists():
        bounds = get_image_bounds(sample_img)
    else:
        # Use calculated or default bounds
        pass

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{viewport_id.title()} Tessera Embeddings Viewer</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f0f0f0;
        }}

        #controls {{
            margin-bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        #controls input {{
            padding: 8px;
            margin-right: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            width: 200px;
        }}

        #controls button {{
            padding: 8px 15px;
            margin-right: 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-weight: bold;
        }}

        .save-btn {{
            background: #28a745;
            color: white;
        }}

        .clear-btn {{
            background: #dc3545;
            color: white;
        }}

        .export-btn {{
            background: #007bff;
            color: white;
        }}

        #map-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            max-width: 1800px;
        }}

        .map-container {{
            background: white;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .map-label {{
            padding: 10px;
            background: #333;
            color: white;
            font-weight: bold;
            text-align: center;
        }}

        .map-label.center {{
            background: #007bff;
        }}

        .map {{
            height: 400px;
            width: 100%;
        }}

        #status {{
            margin-top: 20px;
            padding: 10px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .marker-popup {{
            font-size: 14px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>{viewport_id.title()} Tessera Embeddings Interactive Viewer</h1>

    <div id="controls">
        <label>Label: <input type="text" id="label-input" value="building" placeholder="Enter label name"></label>
        <button class="save-btn" onclick="saveLabels()">Save Labels</button>
        <button class="clear-btn" onclick="clearAllLabels()">Clear All</button>
        <button class="export-btn" onclick="exportLabels()">Export JSON</button>
        <span id="label-count">Labels: 0</span>
    </div>

    <div id="map-grid">
        <div class="map-container">
            <div class="map-label">2017</div>
            <div id="map-2017" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2018</div>
            <div id="map-2018" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2019</div>
            <div id="map-2019" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2020</div>
            <div id="map-2020" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label center">2024 Satellite RGB</div>
            <div id="map-satellite" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2021</div>
            <div id="map-2021" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2022</div>
            <div id="map-2022" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2023</div>
            <div id="map-2023" class="map"></div>
        </div>
        <div class="map-container">
            <div class="map-label">2024</div>
            <div id="map-2024" class="map"></div>
        </div>
    </div>

    <div id="status">
        <strong>Instructions:</strong><br>
        1. Enter a label name in the text box (e.g., "building", "road", "vegetation")<br>
        2. Click on any map to place a labeled marker<br>
        3. Click "Save Labels" to save to localStorage<br>
        4. Click "Export JSON" to download labels as a JSON file<br>
        5. All maps are synchronized - zoom/pan on any map will update all others
    </div>

    <script>
        const center = {CENTER};
        const zoom = {INITIAL_ZOOM};
        const bounds = {bounds};

        // Store for labels: {{mapId: [[lat, lon, label], ...]}}
        let labels = {{
            '2017': [], '2018': [], '2019': [], '2020': [], '2021': [],
            '2022': [], '2023': [], '2024': [], 'satellite': []
        }};

        // Store for marker objects
        let markers = {{}};

        // Map instances
        let maps = {{}};
        let referenceMap = null;

        // Create all maps
        const mapIds = ['2017', '2018', '2019', '2020', 'satellite', '2021', '2022', '2023', '2024'];

        mapIds.forEach(mapId => {{
            const map = L.map(`map-${{mapId}}`, {{
                center: center,
                zoom: zoom,
                zoomControl: true
            }});

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);

            // Add image overlay (to be loaded from server or embedded)
            // For now, just showing basemap

            // Add click handler
            map.on('click', function(e) {{
                const label = document.getElementById('label-input').value || 'unlabeled';
                addMarker(mapId, e.latlng.lat, e.latlng.lng, label);
            }});

            maps[mapId] = map;
            markers[mapId] = {{}};

            // Use satellite map as reference for syncing
            if (mapId === 'satellite') {{
                referenceMap = map;
            }}
        }});

        // Synchronize all maps with the reference map
        function syncMaps() {{
            if (!referenceMap) return;

            referenceMap.on('zoomend moveend', function() {{
                const refCenter = referenceMap.getCenter();
                const refZoom = referenceMap.getZoom();

                mapIds.forEach(mapId => {{
                    if (mapId !== 'satellite') {{
                        maps[mapId].setView(refCenter, refZoom, {{animate: false}});
                    }}
                }});
            }});
        }}

        syncMaps();

        function addMarker(mapId, lat, lon, label) {{
            const key = `${{lat}},${{lon}}`;

            // Check if marker already exists (remove it)
            if (markers[mapId][key]) {{
                removeMarker(mapId, lat, lon);
                return;
            }}

            // Create marker
            const marker = L.marker([lat, lon]).addTo(maps[mapId]);
            marker.bindPopup(`<div class="marker-popup">${{label}}</div>`);

            // Store marker
            markers[mapId][key] = marker;
            labels[mapId].push([lat, lon, label]);

            updateLabelCount();
            console.log(`Added '${{label}}' at (${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}) on ${{mapId}}`);
        }}

        function removeMarker(mapId, lat, lon) {{
            const key = `${{lat}},${{lon}}`;

            if (markers[mapId][key]) {{
                maps[mapId].removeLayer(markers[mapId][key]);
                delete markers[mapId][key];

                // Remove from labels
                labels[mapId] = labels[mapId].filter(
                    ([la, lo]) => Math.abs(la - lat) > 0.0001 || Math.abs(lo - lon) > 0.0001
                );

                updateLabelCount();
                console.log(`Removed marker at (${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}) from ${{mapId}}`);
            }}
        }}

        function updateLabelCount() {{
            const total = Object.values(labels).reduce((sum, arr) => sum + arr.length, 0);
            document.getElementById('label-count').textContent = `Labels: ${{total}}`;
        }}

        function saveLabels() {{
            localStorage.setItem('{viewport_id}_labels', JSON.stringify(labels));
            alert(`Saved ${{Object.values(labels).reduce((sum, arr) => sum + arr.length, 0)}} labels to browser storage`);
        }}

        function loadLabels() {{
            const stored = localStorage.getItem('{viewport_id}_labels');
            if (stored) {{
                const loadedLabels = JSON.parse(stored);
                Object.keys(loadedLabels).forEach(mapId => {{
                    loadedLabels[mapId].forEach(([lat, lon, label]) => {{
                        addMarker(mapId, lat, lon, label);
                    }});
                }});
                console.log('Loaded labels from browser storage');
            }}
        }}

        function clearAllLabels() {{
            if (!confirm('Clear all labels?')) return;

            Object.keys(markers).forEach(mapId => {{
                Object.values(markers[mapId]).forEach(marker => {{
                    maps[mapId].removeLayer(marker);
                }});
                markers[mapId] = {{}};
                labels[mapId] = [];
            }});

            updateLabelCount();
            console.log('Cleared all labels');
        }}

        function exportLabels() {{
            const dataStr = JSON.stringify(labels, null, 2);
            const dataBlob = new Blob([dataStr], {{type: 'application/json'}});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'training_labels.json';
            link.click();
            URL.revokeObjectURL(url);
            console.log('Exported labels to JSON file');
        }}

        // Load saved labels on page load
        window.onload = function() {{
            loadLabels();
        }};
    </script>
</body>
</html>'''

    with open(output_html, 'w') as f:
        f.write(html)

    print(f"✓ Created web viewer: {output_html.absolute()}")
    print(f"\nTo use:")
    print(f"  open {output_html.absolute()}")
    print(f"\nor double-click the HTML file in Finder")

if __name__ == "__main__":
    # Try to get active viewport, fall back to Bangalore for backwards compatibility
    viewport_id = None
    viewport_bounds = None
    try:
        viewport = get_active_viewport()
        viewport_id = viewport['viewport_id']
        viewport_bounds = viewport['bounds_tuple']
    except Exception as e:
        print(f"Warning: Could not read active viewport: {e}")
        print("Using default Bangalore bounds...")

    create_html_viewer(viewport_id, viewport_bounds)
