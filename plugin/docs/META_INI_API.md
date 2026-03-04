# Meta.ini API Feature

## Overview

Added API endpoints to read and write custom key=value pairs to mod `meta.ini` files under the `[mo2web]` section. This allows external applications to store custom metadata for mods.

## Implementation Details

### mobase API Investigation

Mod Organizer 2's `mobase` API provides:

- `mod.absolutePath()` - Returns the absolute path to a mod's directory
- `mod.comments()` - Can read/write comments, but not arbitrary key=value pairs

Since mobase doesn't provide direct INI file manipulation methods, the implementation uses Python's built-in `configparser` module to read and write INI files directly.

### Files Created/Modified

1. **Created: `webapi/organizer/ini_helper.py`**
   - Helper functions for reading/writing meta.ini files
   - Uses `configparser.ConfigParser` for INI file operations
   - Thread-safe task function factories for use with TaskExecutor
   - Functions:
     - `read_meta_value()` - Read a single value
     - `read_meta_section()` - Read all key=value pairs from a section
     - `write_meta_value()` - Write a single key=value pair
     - `write_meta_values()` - Write multiple key=value pairs
     - `delete_meta_key()` - Delete a key from INI file
     - Task function factories: `write_meta_value_fn()`, `write_meta_values_fn()`, `delete_meta_key_fn()`

2. **Modified: `webapi/routes/mods.py`**
   - Added import: `from ..organizer import ini_helper`
   - Added 5 new endpoints for meta.ini operations

3. **Modified: `README.md`**
   - Documented all new endpoints
   - Added usage examples (Python, curl)

## API Endpoints

### GET `/mods/<modName>/meta`

Get all key=value pairs from the [mo2web] section.

### GET `/mods/<modName>/meta/<key>`

Get a single value from the [mo2web] section.

### POST `/mods/<modName>/meta`

Write multiple key=value pairs to the [mo2web] section.

### PUT/POST `/mods/<modName>/meta/<key>`

Write a single key=value pair to the [mo2web] section.

### DELETE `/mods/<modName>/meta/<key>`

Delete a key from the [mo2web] section.

## Usage Examples

### Write Custom Metadata

```python
import requests

# Write multiple values
requests.post("http://localhost:5000/mods/SkyUI/meta", json={
    "data": {
        "lastSync": "2026-02-02",
        "rating": "5",
        "customTag": "essential"
    }
})

# Write a single value
requests.put("http://localhost:5000/mods/SkyUI/meta/rating", json={
    "value": "5"
})
```

### Read Custom Metadata

```python
# Read all values
response = requests.get("http://localhost:5000/mods/SkyUI/meta")
meta_data = response.json()

# Read a single value
response = requests.get("http://localhost:5000/mods/SkyUI/meta/rating")
value = response.json()["value"]
```

### Delete Custom Metadata

```python
requests.delete("http://localhost:5000/mods/SkyUI/meta/customTag")
```

## File Format

The meta.ini file will contain a `[mo2web]` section with custom key=value pairs:

```ini
[General]
version=1.0.0
installDate=2026-01-15

[mo2web]
lastSync=2026-02-02
rating=5
customTag=essential
```

## Use Cases

1. **Mod Synchronization**: Store last sync timestamps
2. **Custom Ratings**: Store user ratings or scores
3. **Tags and Categories**: Store custom classification data
4. **External Tool Integration**: Store data from external mod management tools
5. **Mod State Tracking**: Track custom mod states across sessions

## Technical Notes

- All write operations are queued and executed in the main Qt thread via TaskExecutor
- INI files are encoded in UTF-8
- Section parameter is optional and defaults to "mo2web"
- If meta.ini doesn't exist, it will be created automatically
- configparser preserves existing sections when writing
- Empty sections are automatically removed when the last key is deleted

## Thread Safety

All write operations use the TaskExecutor to ensure thread-safe execution in MO2's main Qt thread, preventing race conditions and ensuring proper integration with MO2's event system.
