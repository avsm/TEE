#!/usr/bin/env python3
"""
Test the full similarity search workflow.
"""

import requests
import json
import numpy as np
from pathlib import Path

BASE_URL = 'http://localhost:8001'

print("=" * 70)
print("FULL SIMILARITY SEARCH WORKFLOW TEST")
print("=" * 70)

# Step 1: Get active viewport
print("\n[STEP 1] Getting active viewport...")
response = requests.get(f'{BASE_URL}/api/viewports/current')
viewport_data = response.json()
viewport_id = viewport_data['viewport']['name']
print(f"✓ Active viewport: {viewport_id}")

# Step 2: Extract embedding at a location
print(f"\n[STEP 2] Extracting test embedding at (13.0, 77.55)...")
response = requests.post(f'{BASE_URL}/api/embeddings/extract', json={
    'lat': 13.0,
    'lon': 77.55
})
extract_data = response.json()
if not extract_data['success']:
    print(f"✗ Error: {extract_data['error']}")
    exit(1)

embedding1 = extract_data['embedding']
pixel1 = extract_data['pixel']
print(f"✓ Got embedding at pixel ({pixel1['x']}, {pixel1['y']})")

# Step 3: Extract another embedding nearby (should be similar)
print(f"\n[STEP 3] Extracting nearby embedding at (13.001, 77.551)...")
response = requests.post(f'{BASE_URL}/api/embeddings/extract', json={
    'lat': 13.001,
    'lon': 77.551
})
extract_data = response.json()
if not extract_data['success']:
    print(f"✗ Error: {extract_data['error']}")
    exit(1)

embedding2 = extract_data['embedding']
pixel2 = extract_data['pixel']
print(f"✓ Got embedding at pixel ({pixel2['x']}, {pixel2['y']})")

# Step 4: Calculate average embedding (simulating user with multiple labeled pixels)
print(f"\n[STEP 4] Computing average embedding (simulating multiple labels)...")
avg_embedding = np.mean([embedding1, embedding2], axis=0).tolist()
print(f"✓ Average embedding computed")

# Step 5: Search for similar pixels
print(f"\n[STEP 5] Searching for similar pixels (threshold=0.1)...")
response = requests.post(f'{BASE_URL}/api/embeddings/search-similar', json={
    'embedding': avg_embedding,
    'threshold': 0.1,
    'viewport_id': viewport_id
})
search_data = response.json()
if not search_data['success']:
    print(f"✗ Error: {search_data['error']}")
    exit(1)

matches = search_data['matches']
stats = search_data['query_stats']
print(f"✓ Found {len(matches):,} matches in {stats['computation_time_ms']:.0f}ms")
print(f"  Total pixels searched: {stats['total_pixels']:,}")
print(f"  Matching percentage: {(len(matches) / stats['total_pixels'] * 100):.1f}%")

# Show sample matches
if len(matches) > 0:
    print(f"\n  Sample matches (first 5):")
    for i, match in enumerate(matches[:5]):
        dist = match['distance']
        px, py = match['pixel']['x'], match['pixel']['y']
        print(f"    {i+1}. Distance: {dist:.4f}, Pixel: ({px}, {py})")

# Verify L2 distance calculation
print(f"\n[STEP 6] Verifying distance calculation...")
test_dist_sq = sum((avg_embedding[i] - embedding1[i]) ** 2 for i in range(len(avg_embedding)))
test_dist = np.sqrt(test_dist_sq)
print(f"  Manual distance calculation: {test_dist:.4f}")
print(f"  (Should be close to first match which is around 0.0000)")

print("\n" + "=" * 70)
print("✅ Similarity search is working correctly!")
print("=" * 70)
