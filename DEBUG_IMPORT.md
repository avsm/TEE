# Debug Guide: Labels Not Appearing After Import

## Quick Test (Right Now)

1. **Open http://localhost:8001 in your browser**
2. **Open Browser DevTools** (Press F12)
3. **Go to the Console tab** (You should see a black area with text)
4. **Clear the console** (Click the circle-slash icon)
5. **Click "Import Labels"** button
6. **Select this file**: `/tmp/test_import_debug.json`
7. **Check the console** - you should see many lines starting with `[IMPORT]` and `[DROPDOWN]`

## What You Should See in Console

After clicking import, you should see logs like:

```
[IMPORT] Starting import process...
[IMPORT] definedLabels before: []
[IMPORT] Created new label: "road"
[IMPORT] Added 1 embeddings to "road"
[IMPORT] definedLabels after import: ['road', 'building']
[IMPORT] definedLabels after sort: ['building', 'road']
[IMPORT] Calling updateLabelDropdown()...
[DROPDOWN] Updating dropdown, definedLabels: ['building', 'road']
[DROPDOWN] Found select element: <select id="active-label" ...>
[DROPDOWN] Adding 2 labels to dropdown
[DROPDOWN] Added option: building
[DROPDOWN] Added option: road
[DROPDOWN] Set initial value to: building
[DROPDOWN] Dropdown update complete. Current options: <option value="building">building</option>...
[IMPORT] updateLabelDropdown() completed
```

## If You See Errors

### Error: "Could not find element with id='active-label'"
- The dropdown element might not exist or the page didn't fully load
- **Solution**: Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)

### Error in the console (red text)
- Copy the full error message and share it
- This will tell us exactly what went wrong

### Labels appear in dropdown but no circles show
- Try using "Create Label" first to test the full workflow
- This will help narrow down if it's an import-specific issue

## Step-by-Step Debug

1. **Are labels in the dropdown?**
   - Yes → Go to Step 2
   - No → Check console for `[DROPDOWN]` errors

2. **Does the label count show updated number?**
   - Yes → Go to Step 3
   - No → The import data may not have been read correctly

3. **Select a label and try "Find Similar"**
   - Should see circles on the embedding map
   - If no circles: Increase the similarity threshold slider

4. **Reload page (F5)**
   - Do labels still appear?
   - If yes → Everything is working!
   - If no → LocalStorage might not be saving

## What to Share If It's Still Not Working

When you report the issue, please share:

1. **Screenshot of the browser console** (F12)
2. **The exact error message** (if any, in red)
3. **Confirmation whether you see any `[IMPORT]` or `[DROPDOWN]` logs**
4. **Whether the success alert pops up** ("Successfully imported...")
5. **Whether the dropdown remains as "No labels yet"** or changes

This information will help debug exactly what's happening.
