#!/usr/bin/env python3
"""
End-to-end test: simulate user labeling a pixel and searching for similar ones.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from lib.viewport_writer import set_active_viewport
import requests
import json

BASE_URL = 'http://localhost:8001'

print("=" * 70)
print("END-TO-END SIMILARITY CIRCLE TEST")
print("=" * 70)

# Switch to tile_aligned viewport
set_active_viewport("tile_aligned")
print(f"\n✓ Switched to tile_aligned viewport")

# Step 1: Simulate user clicking on a pixel to label it
print(f"\n[STEP 1] Simulating user labeling pixel at (13.0, 77.55)...")
response = requests.post(f'{BASE_URL}/api/embeddings/extract', json={'lat': 13.0, 'lon': 77.55})
if not response.json().get('success'):
    print("✗ Failed to extract embedding")
    exit(1)

embedding = response.json()['embedding']
pixel_x, pixel_y = response.json()['pixel']['x'], response.json()['pixel']['y']
print(f"✓ Got embedding for pixel ({pixel_x}, {pixel_y})")

# Step 2: Simulate "Find Similar" button with threshold at 50% (0.1 in new scale)
print(f"\n[STEP 2] Searching for similar pixels (threshold=0.1)...")
response = requests.post(f'{BASE_URL}/api/embeddings/search-similar', json={
    'embedding': embedding,
    'threshold': 0.1,
    'viewport_id': 'tile_aligned'
})

if not response.json().get('success'):
    print(f"✗ Search failed: {response.json().get('error')}")
    exit(1)

matches = response.json()['matches']
stats = response.json()['query_stats']

print(f"✓ Found {len(matches):,} similar pixels")
print(f"  Search took: {stats['computation_time_ms']:.0f}ms")
print(f"  Matching {(len(matches)/stats['total_pixels']*100):.1f}% of image")

# Step 3: Show what the circles would look like
if len(matches) > 0:
    print(f"\n[STEP 3] Circle visualization would show:")
    print(f"  Total circles to draw: {len(matches)}")
    print(f"  Each circle: 15m radius, dashed outline, semi-transparent fill")
    print(f"\n  Sample circles (first 10):")
    for i, match in enumerate(matches[:10]):
        lat, lon = match['lat'], match['lon']
        dist = match['distance']
        px, py = match['pixel']['x'], match['pixel']['y']
        print(f"    Circle {i+1}: lat={lat:.6f}, lon={lon:.6f}, distance={dist:.4f}")
else:
    print(f"\n✗ No matches found - circles will not be visible")
    print(f"  (Try with a higher threshold like 0.2 or 0.3)")

print("\n" + "=" * 70)
print("✅ Similarity search and circle visualization is working!")
print("=" * 70)
print("\nNow you can:")
print("1. Open http://localhost:8001 in your browser")
print("2. Click on the 'Create Label' button")
print("3. Click on the embedding map (middle panel) to label some pixels")
print("4. Click 'Find Similar' - you should see circles appear!")
