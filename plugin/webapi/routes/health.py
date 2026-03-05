from fastapi import APIRouter

from .. import config
from ..schemas import ConfigResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
	"/health",
	summary="Health check",
	response_model=HealthResponse,
	responses={
		200: {"description": "Server is running. Returns status and API version."},
	},
)
def health_check():
	return {"status": "ok", "version": config.API_VERSION}


@router.get(
	"/config",
	summary="Get server config",
	response_model=ConfigResponse,
	responses={
		200: {"description": "HTTP and WebSocket ports used by the server."},
	},
)
def get_config():
	return {
		"httpPort": config.HTTP_PORT,
		"websocketPort": config.WEBSOCKET_PORT,
	}
