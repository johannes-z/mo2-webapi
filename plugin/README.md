# MO2 WebAPI Plugin

A plugin for Mod Organizer 2 that provides HTTP and WebSocket APIs for external applications to interact with mod management.

## Features

- **RESTful HTTP API** for mod queries and operations
- **WebSocket API** for real-time mod event notifications
- **Thread-safe** task queue for mod operations
- **Type-safe** with comprehensive type hints
- **Well-documented** with docstrings and comments

## Installation

1. Clone or download this repository
2. Copy the `mo2-webapi-plugin` folder to your MO2 plugins directory:
   ```
   <MO2 Installation>\plugins\
   ```
3. Restart Mod Organizer 2
4. Enable the plugin in MO2 Settings → Plugins

## Configuration

The plugin uses the following default settings:

- **HTTP Server Port**: 5000
- **WebSocket Server Port**: 5001

You can modify these in `config.ini` in the plugin directory (or see [webapi/config.py](webapi/config.py) for defaults).

### Dev endpoint

In `config.ini`, set `[dev]` → `dev_endpoint = true` to enable an API overview at **GET `/dev`** and **GET `/api-docs`**: a single page listing all endpoints with collapsible request/response schema and a “Try it” form. Leave this disabled in production.

## HTTP API Endpoints

### GET `/health`

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "version": "1.1.0"
}
```

### GET `/mods`

Get a list of all installed mods.

**Response:**

```json
[
  {
    "name": "SkyUI",
    "isEnabled": true,
    "version": "5.2",
    "priority": 42,
    "isSeparator": false,
    "isForeign": false,
    "isOverwrite": false,
    "installationFile": "SkyUI_5_2-3863.7z",
    "nexusId": 3863,
    "categories": ["interface"],
    "comments": ""
  }
]
```

### GET `/mods/enabled`

Get a list of only enabled mods.

### GET `/mods/disabled`

Get a list of only disabled mods.

### GET `/mods/search?q={query}`

Search for mods by name (case-insensitive).

**Example:** `/mods/search?q=skyui`

### GET `/mods/{modName}`

Get information about a specific mod.

**Response:**

```json
{
  "name": "SkyUI",
  "isEnabled": true,
  "version": "5.2",
  "priority": 42,
  ...
}
```

**Error Response:**

```json
{
  "error": "Mod 'ModName' not found"
}
```

### GET `/profile`

Get the current active profile name.

**Response:**

```json
{
  "name": "Default"
}
```

### POST `/mods/enable`

Enable a specific mod.

**Request Body:**

```json
{
  "name": "SkyUI"
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "enable",
  "mod": "SkyUI"
}
```

### POST `/mods/disable`

Disable a specific mod.

**Request Body:**

```json
{
  "name": "SkyUI"
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "disable",
  "mod": "SkyUI"
}
```

### POST `/mods/toggle`

Toggle a mod's enabled state.

**Request Body:**

```json
{
  "name": "SkyUI"
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "toggle",
  "mod": "SkyUI"
}
```

### POST `/mods/set-priority`

Set a mod's priority (load order position).

**Request Body:**

```json
{
  "name": "SkyUI",
  "priority": 10
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "set_priority",
  "mod": "SkyUI",
  "priority": 10
}
```

### POST `/mods/enable-batch`

Enable multiple mods at once.

**Request Body:**

```json
{
  "names": ["SkyUI", "SKSE", "SkyrimUnleashed"]
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "enable_batch",
  "mods": ["SkyUI", "SKSE", "SkyrimUnleashed"],
  "count": 3
}
```

### POST `/mods/disable-batch`

Disable multiple mods at once.

**Request Body:**

```json
{
  "names": ["SkyUI", "SKSE"]
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "disable_batch",
  "mods": ["SkyUI", "SKSE"],
  "count": 2
}
```

### GET `/mods/meta`

Get all key=value pairs from the [mo2web] section of all mods' meta.ini files.

**Query Parameters:**

- `section` (optional): INI section to read from (default: "mo2web")

**Response:**

```json
{
  "SkyUI": {
    "customKey": "customValue",
    "lastSync": "2026-02-02"
  },
  "SKSE": {
    "rating": "5"
  },
  "My Custom Mod": {
    "lastSync": "2026-01-15",
    "notes": "test"
  }
}
```

### GET `/mods/<modName>/meta`

Get all key=value pairs from the [mo2web] section of a mod's meta.ini file.

**Query Parameters:**

- `section` (optional): INI section to read from (default: "mo2web")

**Response:**

```json
{
  "customKey": "customValue",
  "lastSync": "2026-02-02"
}
```

### GET `/mods/<modName>/meta/<key>`

Get a single value from the [mo2web] section of a mod's meta.ini file.

**Query Parameters:**

- `section` (optional): INI section to read from (default: "mo2web")

**Response:**

```json
{
  "mod": "SkyUI",
  "section": "mo2web",
  "key": "customKey",
  "value": "customValue"
}
```

**Error Response:**

```json
{
  "error": "Key 'customKey' not found in section [mo2web]"
}
```

### POST `/mods/<modName>/meta`

Write multiple key=value pairs to the [mo2web] section of a mod's meta.ini file.

**Request Body:**

```json
{
  "section": "mo2web",
  "data": {
    "customKey": "customValue",
    "lastSync": "2026-02-02",
    "rating": "5"
  }
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "set_meta",
  "mod": "SkyUI",
  "section": "mo2web",
  "keys": ["customKey", "lastSync", "rating"]
}
```

### PUT/POST `/mods/<modName>/meta/<key>`

Write a single key=value pair to the [mo2web] section of a mod's meta.ini file.

**Request Body:**

```json
{
  "section": "mo2web",
  "value": "customValue"
}
```

**Response:**

```json
{
  "status": "queued",
  "action": "set_meta_key",
  "mod": "SkyUI",
  "section": "mo2web",
  "key": "customKey",
  "value": "customValue"
}
```

### DELETE `/mods/<modName>/meta/<key>`

Delete a key from the [mo2web] section of a mod's meta.ini file.

**Query Parameters:**

- `section` (optional): INI section to delete from (default: "mo2web")

**Response:**

```json
{
  "status": "queued",
  "action": "delete_meta_key",
  "mod": "SkyUI",
  "section": "mo2web",
  "key": "customKey"
}
```

## WebSocket API

Connect to `ws://localhost:5001` to receive real-time mod events.

### Events

#### `mod_updated`

Fired when a mod's state changes (enabled/disabled).

```json
{
  "event": "mod_updated",
  "mods": [
    {
      "name": "SkyUI",
      "isEnabled": true,
      ...
    }
  ]
}
```

#### `mod_installed`

Fired when a new mod is installed.

```json
{
  "event": "mod_installed",
  "mods": [
    {
      "name": "NewMod",
      ...
    }
  ]
}
```

#### `mod_moved`

Fired when a mod's load order changes.

```json
{
  "event": "mod_moved",
  "mods": [
    {
      "name": "SkyUI",
      ...
    }
  ],
  "oldPriority": 42,
  "newPriority": 10
}
```

#### `mod_removed`

Fired when a mod is removed.

```json
{
  "event": "mod_removed",
  "mod": "ModName"
}
```

## Usage Examples

### Python Example (HTTP)

```python
import requests

# Get all mods
response = requests.get("http://localhost:5000/mods")
mods = response.json()

# Enable a mod
requests.post("http://localhost:5000/mods/enable", json={"name": "SkyUI"})

# Disable a mod
requests.post("http://localhost:5000/mods/disable", json={"name": "SkyUI"})

# Write custom data to mod's meta.ini
requests.post("http://localhost:5000/mods/SkyUI/meta", json={
    "section": "mo2web",
    "data": {
        "lastSync": "2026-02-02",
        "rating": "5",
        "customTag": "essential"
    }
})

# Read custom data from mod's meta.ini
response = requests.get("http://localhost:5000/mods/SkyUI/meta")
meta_data = response.json()
print(meta_data)  # {"lastSync": "2026-02-02", "rating": "5", ...}

# Read all mods' meta data at once
response = requests.get("http://localhost:5000/mods/meta")
all_meta = response.json()
# {"SkyUI": {"rating": "5", ...}, "SKSE": {...}, ...}

# Read a single key
response = requests.get("http://localhost:5000/mods/SkyUI/meta/rating")
print(response.json()["value"])  # "5"

# Update a single key
requests.put("http://localhost:5000/mods/SkyUI/meta/rating", json={"value": "4"})

# Delete a key
requests.delete("http://localhost:5000/mods/SkyUI/meta/customTag")
```

requests.post("http://localhost:5000/mods/disable", json={"name": "SkyUI"})

````

### JavaScript Example (WebSocket)

```javascript
const ws = new WebSocket("ws://localhost:5001");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Event:", data.event);
  console.log("Mods:", data.mods);
};

ws.onopen = () => {
  console.log("Connected to MO2 WebSocket");
};
````

### curl Examples

```bash
# Get all mods
curl http://localhost:5000/mods

# Get specific mod
curl http://localhost:5000/mods/SkyUI

# Enable a mod
curl -X POST http://localhost:5000/mods/enable \
  -H "Content-Type: application/json" \
  -d '{"name": "SkyUI"}'

# Write to meta.ini
curl -X POST http://localhost:5000/mods/SkyUI/meta \
  -H "Content-Type: application/json" \
  -d '{"data": {"rating": "5", "lastSync": "2026-02-02"}}'

# Read from meta.ini (single mod)
curl http://localhost:5000/mods/SkyUI/meta

# Read all mods' meta data
curl http://localhost:5000/mods/meta

# Read a single key
curl http://localhost:5000/mods/SkyUI/meta/rating

# Update a single key
curl -X PUT http://localhost:5000/mods/SkyUI/meta/rating \
  -H "Content-Type: application/json" \
  -d '{"value": "4"}'

# Delete a key
curl -X DELETE http://localhost:5000/mods/SkyUI/meta/rating

# Health check
curl http://localhost:5000/health
```

# Health check

curl http://localhost:5000/health

```

## Architecture

- **webapi_plugin.py**: Main plugin entry point
- **server_http.py**: HTTP server implementation
- **server_websocket.py**: WebSocket server implementation
- **taskQueue.py**: Thread-safe task queue for mod operations
- **organizer/mod_helper.py**: Helper functions for mod operations
- **config.py**: Configuration settings

The plugin runs two daemon threads:

1. HTTP server for REST API requests
2. WebSocket server for real-time events

Mod operations are queued and executed in the main Qt thread to ensure thread safety with MO2's API.

## Development

### Dependencies

- **PyQt6**: Qt bindings for Python
- **websockets**: WebSocket implementation
- **mobase**: MO2 Python API

### Logging

The plugin uses Python's logging module. Check MO2's logs for detailed information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Author

johannes-z

## Version

1.1.0 (Beta)
```
