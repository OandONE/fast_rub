"""
FastAPI docs server for Fast Rub.

The HTML pages are static templates on disk.  This server:

* reads the page's JSON source, computes a short content hash,
* injects that hash into the page's ``<meta name="docs-hash">``,
* serves the rendered HTML with ``ETag`` + ``Cache-Control: no-cache``,
* serves ``page.min.json?h=<hash>`` with ``immutable`` caching,
* returns ``304 Not Modified`` for unchanged HTML.

The result: only JSON files need to change.  When nothing changed the browser
revalidates the small HTML response (304) and serves the JSON from cache; when
JSON changes, the hash changes and the page requests the new JSON URL.

Minified JSON and ``all.json`` are derived from the pretty JSON sources at
request time, so the site does not depend on running ``docs/json_miner.py``.

Run locally:

    uvicorn docs_server.app:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse

from .render import BASE_FILES, PAGE_SPECS, DocsSite

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

NO_CACHE = "no-cache"
IMMUTABLE = "public, max-age=31536000, immutable"

site = DocsSite(DOCS_DIR)

JSON_NAMES = frozenset(
    set(BASE_FILES)
    | {f"{name}.min" for name in BASE_FILES}
    | {"all", "all.min"}
)


def _json_info(name: str) -> tuple[str, bytes]:
    if name not in JSON_NAMES:
        raise HTTPException(status_code=404, detail="Unknown JSON document")
    try:
        return site.document(name)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown JSON document") from error
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=f"Invalid JSON document: {error}") from error


def _page_body(page: str) -> tuple[str, str]:
    if page not in PAGE_SPECS:
        raise HTTPException(status_code=404, detail="Unknown docs page")
    try:
        return site.page(page)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown docs page") from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail="Docs template not found") from error
    except (ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def _normalize_etag(tag: str) -> str:
    tag = tag.strip()
    return tag[2:].strip() if tag.startswith("W/") else tag


def _not_modified(request: Request, etag: str) -> bool:
    """RFC 9110 weak comparison for If-None-Match."""
    header = request.headers.get("if-none-match")
    if not header:
        return False

    current = _normalize_etag(etag)
    for candidate in header.split(","):
        candidate = candidate.strip()
        if not candidate:
            continue
        if candidate == "*" or _normalize_etag(candidate) == current:
            return True
    return False


def _html_response(
    request: Request,
    body: bytes | str,
    cache: str = NO_CACHE,
    media_type: str = "text/html; charset=utf-8",
) -> Response:
    raw = body.encode("utf-8") if isinstance(body, str) else body
    etag = 'W/"' + hashlib.sha256(raw).hexdigest()[:16] + '"'
    headers = {"ETag": etag, "Cache-Control": cache}
    if _not_modified(request, etag):
        return Response(status_code=304, headers=headers)
    return Response(content=raw, media_type=media_type, headers=headers)


def _file_response(
    request: Request,
    path: Path,
    media_type: str,
    cache: str = NO_CACHE,
) -> Response:
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return _html_response(
        request,
        path.read_bytes(),
        cache=cache,
        media_type=media_type,
    )


def _page_response(request: Request, page: str) -> Response:
    body, etag = _page_body(page)
    headers = {"ETag": etag, "Cache-Control": NO_CACHE}
    if _not_modified(request, etag):
        return Response(status_code=304, headers=headers)
    return Response(
        content=body,
        media_type="text/html; charset=utf-8",
        headers=headers,
    )


def _json_response(request: Request, name: str) -> Response:
    digest, raw = _json_info(name)
    etag = 'W/"' + digest + '"'

    if request.query_params.get("h") == digest:
        # The URL contains the current content hash, so it is safe to cache
        # forever: changed JSON gets a different URL.
        return Response(
            content=raw,
            media_type="application/json; charset=utf-8",
            headers={"ETag": etag, "Cache-Control": IMMUTABLE},
        )

    # No hash (or a stale one): revalidate with ETag instead of long caching.
    headers = {"ETag": etag, "Cache-Control": NO_CACHE}
    if _not_modified(request, etag):
        return Response(status_code=304, headers=headers)
    return Response(
        content=raw,
        media_type="application/json; charset=utf-8",
        headers=headers,
    )


def build_router() -> APIRouter:
    """Build a router whose paths are relative to the site root.

    Including it with ``prefix="/docs"`` gives the ``/docs/...`` aliases used
    by links on the landing page.
    """
    router = APIRouter()

    @router.get("/")
    def landing(request: Request) -> Response:
        return _file_response(
            request,
            DOCS_DIR / "index.html",
            "text/html; charset=utf-8",
        )

    @router.get("/index.html")
    def landing_index(request: Request) -> Response:
        return _file_response(
            request,
            DOCS_DIR / "index.html",
            "text/html; charset=utf-8",
        )

    @router.get("/docs-data.js")
    def docs_data(request: Request) -> Response:
        return _file_response(
            request,
            DOCS_DIR / "docs-data.js",
            "application/javascript; charset=utf-8",
        )

    @router.get("/icon.jpg")
    def icon(request: Request) -> Response:
        return _file_response(
            request,
            DOCS_DIR / "icon.jpg",
            "image/jpeg",
            cache="public, max-age=86400",
        )

    @router.get("/manifest.json")
    def manifest(request: Request) -> Response:
        return _file_response(
            request,
            DOCS_DIR / "manifest.json",
            "application/json; charset=utf-8",
        )

    # JSON must be registered before /{page}: /features.min.json is a JSON
    # route, /features is a page redirect.
    @router.get("/{name}.json")
    def json_document(name: str, request: Request) -> Response:
        return _json_response(request, name)

    @router.get("/{page}/index.html")
    def page_index(page: str, request: Request) -> Response:
        return _page_response(request, page)

    @router.get("/{page}/")
    def page_slash(page: str, request: Request) -> Response:
        return _page_response(request, page)

    @router.get("/{page}")
    def page_redirect(page: str, request: Request) -> Response:
        if page not in PAGE_SPECS:
            raise HTTPException(status_code=404, detail="Unknown docs page")
        return RedirectResponse(url=request.url.path + "/", status_code=307)

    return router


app = FastAPI(
    title="Fast Rub Docs",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def head_as_get(request: Request, call_next):
    """Support HEAD for cache/proxy checks; GET handlers are used internally."""
    if request.method != "HEAD":
        return await call_next(request)

    request.scope["method"] = "GET"
    response = await call_next(request)
    response.body = b""
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/docs", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    # The site itself uses /docs as an alias; keep FastAPI's Swagger UI off.
    return RedirectResponse(url="/docs/", status_code=307)


# /docs/... aliases first, then root paths.
app.include_router(build_router(), prefix="/docs")
app.include_router(build_router())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
