# Import/Export and Similarity Search Test Guide

## What Was Fixed

1. **Import labels persistence**: Fixed `saveLabels()` and `loadLabels()` to properly persist imported labels
2. **Dropdown update**: Fixed import function to use correct element ID and `updateLabelDropdown()` function
3. **Label count**: Updated `updateLabelCount()` to show both markers and embeddings
4. **Similarity search circles**: Verified circles render correctly (already working)

## Test Workflow

### Step 1: Clear Browser Storage (Fresh Start)
1. Open browser DevTools (F12)
2. Go to Application → LocalStorage
3. Find `bangalore_labels_3panel` and delete it
4. Close DevTools

### Step 2: Import Test Labels
1. Go to http://localhost:8001
2. Click "Import Labels" button
3. Select the test file: `/tmp/test_labels.json`
4. You should see: ✓ Successfully imported 2 labels with 4 embeddings!

### Step 3: Verify Labels Appear in Dropdown
- [ ] "building" label appears in "Active Label" dropdown
- [ ] "road" label appears in "Active Label" dropdown
- [ ] Label count shows "Labels: 4" (4 imported embeddings)
- [ ] Labels are sorted alphabetically

### Step 4: Verify Labels Persist on Reload
1. Reload the page (F5)
2. Check that:
   - [ ] Labels still appear in dropdown
   - [ ] Label count still shows "Labels: 4"
   - [ ] Console shows: ✓ Loaded 4 embeddings for 2 labels

### Step 5: Test Similarity Search
1. Select "building" from the Active Label dropdown
2. Click "Find Similar" button
3. You should see:
   - [ ] Message: "Found X similar pixels"
   - [ ] Circles appear on the middle panel (embedding map)
   - [ ] Circles have dashed outline, semi-transparent fill
   - [ ] Hovering shows popup with label and distance

### Step 6: Test Exporting Labels
1. Label a pixel manually:
   - Click "+ Create Label"
   - Name it "test"
   - Click "Start Labeling"
   - Click on the middle panel (embedding map)
   - Click "Stop Labeling"
2. Click "Export Labels"
3. Browser downloads `embedding_labels_[timestamp].json`
4. Open the file to verify format:
   ```json
   [
     {"label": "building", "embedding": [[...], ...]},
     {"label": "road", "embedding": [[...], ...]},
     {"label": "test", "embedding": [[...]]}
   ]
   ```

### Step 7: Test Import → Use → Export Cycle
1. Delete browser storage again
2. Import the exported file
3. Verify labels appear
4. Find similar pixels
5. Export again
6. Verify format is correct

## Troubleshooting

### Labels don't appear after import
- Check browser console (F12) for errors
- Verify test file is valid JSON
- Check localStorage has `bangalore_labels_3panel` key

### Circles don't appear after search
- Check console for errors
- Verify threshold slider is set correctly (0.0 = exact, 1.0 = broad)
- Make sure you have labeled at least one pixel in that label
- Try increasing threshold or zooming into the map

### Label count doesn't update
- Reload the page
- Check console for updateLabelCount() logs

## Console Checks

Open DevTools (F12) and go to Console tab to see:

**After Import:**
```
✓ Imported "building": 1 embeddings
✓ Imported "road": 2 embeddings
✓ Saved: 0 markers + 4 embeddings
```

**After Page Reload:**
```
✓ Loaded 4 embeddings for 2 labels
```

**After "Find Similar":**
```
[SIMILARITY] Searching for pixels similar to "building"
[SIMILARITY] Found 379,605 similar pixels
[SIMILARITY] Visualized 379,605 similar pixels with circles
```
