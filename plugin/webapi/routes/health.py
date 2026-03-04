from fastapi import APIRouter

from .. import config

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
	return {"status": "ok", "version": config.API_VERSION}


@router.get("/config")
def get_config():
	return {
		"httpPort": config.HTTP_PORT,
		"websocketPort": config.WEBSOCKET_PORT,
	}
