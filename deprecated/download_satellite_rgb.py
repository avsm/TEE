#!/usr/bin/env python3
"""
Download Sentinel-2 RGB imagery for current viewport

Uses Element84 STAC API with direct COG access (more reliable than Planetary Computer)
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent))

from lib.viewport_utils import get_active_viewport, check_cache

# Configuration
YEAR = 2024
RESOLUTION = 10  # meters per pixel
DATA_DIR = Path.home() / "blore_data"

def download_satellite_rgb_stac():
    """Download Sentinel-2 RGB using Element84 STAC API."""

    # Read active viewport
    try:
        viewport = get_active_viewport()
        BBOX = viewport['bounds_tuple']
        viewport_id = viewport['viewport_id']
    except Exception as e:
        print(f"ERROR: Failed to read viewport: {e}", file=sys.stderr)
        sys.exit(1)

    # Use viewport-specific filename
    OUTPUT_FILE = DATA_DIR / "mosaics" / f"{viewport_id}_satellite_rgb.tif"

    # Check cache
    cached_file = check_cache(BBOX, 'satellite')
    if cached_file:
        print(f"✓ Cache hit! Using existing satellite data: {cached_file}")
        return

    print(f"Downloading Sentinel-2 RGB imagery")
    print(f"Viewport: {viewport_id}")
    print(f"Bounding box: {BBOX}")
    print(f"Year: {YEAR}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

    try:
        import rasterio
        import numpy as np

        # Query STAC API
        stac_api_url = "https://earth-search.aws.element84.com/v1"
        search_url = f"{stac_api_url}/search"

        lon_min, lat_min, lon_max, lat_max = BBOX
        search_body = {
            "collections": ["sentinel-2-l2a"],
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "datetime": f"{YEAR}-01-01T00:00:00Z/{YEAR}-12-31T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": 20}},
            "limit": 1
        }

        print(f"\nQuerying STAC API: {stac_api_url}")
        request = urllib.request.Request(
            search_url,
            data=json.dumps(search_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        print("Searching for Sentinel-2 images...")
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
            items = result.get('features', [])

            if not items:
                print("✗ No Sentinel-2 images found")
                sys.exit(1)

            item = items[0]
            print(f"✓ Found image: {item['id']}")
            print(f"  Date: {item.get('properties', {}).get('datetime')}")
            print(f"  Cloud cover: {item.get('properties', {}).get('eo:cloud_cover'):.1f}%")

            assets = item.get('assets', {})

            # Find band assets (prefer non-JP2)
            band_keys = {
                'red': 'red' if 'red' in assets else 'red-jp2',
                'green': 'green' if 'green' in assets else 'green-jp2',
                'blue': 'blue' if 'blue' in assets else 'blue-jp2'
            }

            print(f"Using bands: {band_keys}")

            bands_data = []
            profile = None

            # Download each band
            for color in ['red', 'green', 'blue']:
                key = band_keys[color]
                url = assets[key]['href']

                print(f"\nDownloading {color} band...")
                vsi_path = f"/vsicurl/{url}"

                try:
                    with rasterio.open(vsi_path) as src:
                        data = src.read(1).astype(np.float32)
                        bands_data.append(data)
                        if profile is None:
                            profile = src.profile
                        print(f"  ✓ Shape: {data.shape}, Range: [{data.min():.0f}, {data.max():.0f}]")
                except Exception as e:
                    print(f"  ✗ Error reading {color}: {e}")
                    raise

            if len(bands_data) != 3:
                print(f"✗ Expected 3 bands, got {len(bands_data)}")
                sys.exit(1)

            print(f"\n✓ All bands downloaded successfully")

            # Stack and normalize
            rgb_data = np.stack(bands_data, axis=0)
            print(f"RGB shape: {rgb_data.shape}")

            # Normalize to 8-bit (clip to 0-3000 for good visualization)
            rgb_data = np.clip(rgb_data / 3000 * 255, 0, 255).astype(np.uint8)

            # Save
            print(f"\nSaving to: {OUTPUT_FILE}")
            profile.update(dtype=rasterio.uint8, count=3, compress='lzw')

            with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
                dst.write(rgb_data)

            size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
            print(f"✓ Saved: {size_mb:.1f} MB")

            # Verify
            with rasterio.open(OUTPUT_FILE) as src:
                print(f"\nVerification:")
                print(f"  Size: {src.width} × {src.height} pixels")
                print(f"  Bands: {src.count} (RGB)")
                print(f"  CRS: {src.crs}")

            print("\n✅ Satellite RGB download complete!")

    except urllib.error.URLError as e:
        print(f"✗ Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    download_satellite_rgb_stac()
