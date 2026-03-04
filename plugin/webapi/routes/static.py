import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from .. import context
from ..log import log

router = APIRouter()


@router.get("/api-docs", include_in_schema=False)
def redirect_api_docs_to_slash():
	return RedirectResponse(url="/api-docs/", status_code=302)


@router.get("/api-docs/", include_in_schema=False)
def serve_api_docs_index():
	static_dir = context.get_static_dir()
	if not static_dir or not static_dir.exists():
		return JSONResponse(content={"error": "Frontend not available"}, status_code=404)
	static_dir = static_dir.resolve()
	api_docs_dir = static_dir / "api-docs"
	index_path = api_docs_dir / "index.html"
	index_str = os.path.normpath(os.path.join(str(static_dir), "api-docs", "index.html"))
	if not os.path.isfile(index_str):
		log.warning(f"api-docs index not found at {index_str} (static_dir={static_dir})")
		return JSONResponse(content={"error": "File not found"}, status_code=404)
	return FileResponse(index_path)


@router.get("/", include_in_schema=False)
@router.get("/{path:path}", include_in_schema=False)
def serve_static(path: str = ""):
	static_dir = context.get_static_dir()
	if not static_dir or not static_dir.exists():
		return JSONResponse(content={"error": "Frontend not available"}, status_code=404)
	static_dir = static_dir.resolve()
	if not path:
		path = "index.html"
	path_clean = path.rstrip("/")
	if path_clean == "api-docs":
		api_docs_index = os.path.normpath(os.path.join(str(static_dir), "api-docs", "index.html"))
		if os.path.isfile(api_docs_index):
			return FileResponse(os.path.join(static_dir, "api-docs", "index.html"))
	file_path = (static_dir / path_clean).resolve()
	try:
		if not file_path.is_relative_to(static_dir):
			return JSONResponse(content={"error": "Invalid path"}, status_code=400)
	except (ValueError, AttributeError):
		return JSONResponse(content={"error": "Invalid path"}, status_code=400)
	if file_path.exists() and file_path.is_dir():
		path_clean = f"{path_clean}/index.html"
		file_path = (static_dir / path_clean).resolve()
	elif not file_path.exists() and not path_clean.endswith(".html"):
		index_candidate = static_dir / path_clean / "index.html"
		if index_candidate.resolve().exists() and index_candidate.resolve().is_file():
			path_clean = f"{path_clean}/index.html"
			file_path = index_candidate.resolve()
	if not file_path.exists() or not file_path.is_file():
		return JSONResponse(content={"error": "File not found"}, status_code=404)
	try:
		return FileResponse(file_path)
	except Exception as e:
		log.error(f"Error serving static file {file_path}: {e}")
		return JSONResponse(content={"error": "Failed to serve file"}, status_code=500)
