#!/usr/bin/env python3
"""
Test the similarity search API to debug why similar pixels aren't being found.
"""

import requests
import json
import numpy as np
from pathlib import Path

# Configuration
BASE_URL = 'http://localhost:8001'
VIEWPORT = 'tile_aligned'

# Test coordinates (viewport center region)
TEST_LAT = 13.0
TEST_LON = 77.55

print("=" * 70)
print("SIMILARITY SEARCH DIAGNOSTIC TEST")
print("=" * 70)

# Step 1: Extract embedding at test location
print(f"\n[STEP 1] Extracting embedding at ({TEST_LAT}, {TEST_LON})...")
response = requests.post(f'{BASE_URL}/api/embeddings/extract', json={
    'lat': TEST_LAT,
    'lon': TEST_LON
})

if response.status_code != 200:
    print(f"ERROR: Extract failed with status {response.status_code}")
    print(response.text)
    exit(1)

extract_data = response.json()
if not extract_data['success']:
    print(f"ERROR: {extract_data['error']}")
    exit(1)

embedding = extract_data['embedding']
pixel = extract_data['pixel']
print(f"✓ Extracted embedding at pixel ({pixel['x']}, {pixel['y']})")
print(f"  Embedding dimensions: {len(embedding)}")
print(f"  Embedding values (first 10): {embedding[:10]}")
print(f"  Embedding range: [{min(embedding)}, {max(embedding)}]")
print(f"  Embedding mean: {np.mean(embedding):.1f}")

# Step 2: Test similarity search with low threshold (should find many matches)
print(f"\n[STEP 2] Testing similarity search with different thresholds...")

thresholds = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

for threshold in thresholds:
    response = requests.post(f'{BASE_URL}/api/embeddings/search-similar', json={
        'embedding': embedding,
        'threshold': threshold,
        'viewport_id': VIEWPORT
    })

    if response.status_code != 200:
        print(f"  Threshold {threshold}: ERROR (status {response.status_code})")
        continue

    data = response.json()
    if not data['success']:
        print(f"  Threshold {threshold}: ERROR - {data['error']}")
        continue

    matches = data['matches']
    stats = data['query_stats']
    print(f"  Threshold {threshold}: {len(matches)} matches (search time: {stats['computation_time_ms']:.0f}ms)")

    if len(matches) > 0:
        # Show first few matches
        print(f"    First 3 matches:")
        for i, match in enumerate(matches[:3]):
            print(f"      {i+1}. Distance: {match['distance']:.4f}, Pixel: ({match['pixel']['x']}, {match['pixel']['y']})")

# Step 3: Check what embeddings are in the FAISS index
print(f"\n[STEP 3] Checking FAISS index statistics...")

DATA_DIR = Path.home() / "blore_data"
FAISS_DIR = DATA_DIR / "faiss_indices" / VIEWPORT

if FAISS_DIR.exists():
    try:
        all_embeddings = np.load(str(FAISS_DIR / 'all_embeddings.npy'))
        print(f"✓ FAISS index found for {VIEWPORT}")
        print(f"  Total embeddings: {len(all_embeddings):,}")
        print(f"  Embedding shape: {all_embeddings.shape}")

        # Compute distances from our test embedding
        test_emb_f32 = np.array(embedding, dtype=np.float32) / 255.0
        all_emb_f32 = all_embeddings.astype(np.float32) / 255.0

        diff = all_emb_f32 - test_emb_f32[np.newaxis, :]
        distances = np.sqrt(np.sum(diff ** 2, axis=1))

        print(f"\n  Distance statistics for test embedding:")
        print(f"    Min distance: {distances.min():.4f}")
        print(f"    Max distance: {distances.max():.4f}")
        print(f"    Mean distance: {distances.mean():.4f}")
        print(f"    Median distance: {np.median(distances):.4f}")
        print(f"    Std deviation: {distances.std():.4f}")

        # Count matches at different thresholds
        print(f"\n  Matches at different thresholds:")
        for th in [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]:
            count = np.sum(distances <= th)
            pct = (count / len(distances)) * 100
            print(f"    {th}: {count:,} matches ({pct:.2f}%)")

    except Exception as e:
        print(f"ERROR reading FAISS index: {e}")
else:
    print(f"✗ FAISS index not found at {FAISS_DIR}")

print("\n" + "=" * 70)
