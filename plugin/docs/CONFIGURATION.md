# Configuration

The plugin now uses environment variables for configuration. You can customize settings by creating a `.env` file.

## Quick Setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` to customize your settings

## Available Settings

### Server Configuration

- `HTTP_PORT` - HTTP server port (default: 5000)
- `WEBSOCKET_PORT` - WebSocket server port (default: 5001)

### Frontend Configuration

- `FRONTEND_DIST_DIR` - Path to frontend build directory relative to plugin folder (default: frontend/dist)

### CORS Settings

- `CORS_ALLOW_ORIGIN` - Allowed origins (default: \*)
- `CORS_ALLOW_METHODS` - Allowed HTTP methods
- `CORS_ALLOW_HEADERS` - Allowed headers

### Logging

- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

## Example .env File

```env
# Server Ports
HTTP_PORT=5000
WEBSOCKET_PORT=5001

# Frontend (relative to plugin directory)
FRONTEND_DIST_DIR=frontend/dist

# Logging
LOG_LEVEL=INFO

# CORS Settings (restrict in production!)
CORS_ALLOW_ORIGIN=*
```

## Security Note

**Never commit your `.env` file!** It's already in `.gitignore`. Use `.env.example` as a template for sharing configurations.
