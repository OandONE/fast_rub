"""Pure data/render helpers shared by the docs server and the static builder.

Both entry points use this module so the hash-based cache busting behaves the
same when docs are served by FastAPI or exported as static files for GitHub
Pages.  Only the standard library is used here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HASH_TOKEN = "__FASTRUB_DOCS_HASH__"

# Order matters for the aggregate all.json (matches docs/json_miner.py).
BASE_FILES: tuple[str, ...] = (
    "methods",
    "models",
    "features",
    "pyrubi",
    "prerequisites",
)

# page key -> (html template relative to docs/, JSON source stem)
PAGE_SPECS: dict[str, tuple[str, str]] = {
    "features": ("features/index.html", "features"),
    "methods": ("methods/index.html", "methods"),
    "models": ("models/index.html", "models"),
    "prerequisites": ("prerequisites/index.html", "prerequisites"),
    "pyrubi": ("pyrubi/index.html", "pyrubi"),
}

BASE_FILE_SET = frozenset(BASE_FILES)


def content_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:16]


def minify_json(data: Any) -> bytes:
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_json(data: Any, indent: int = 4) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=indent).encode("utf-8")


class DocsSite:
    """Reads docs/*.json and renders hash-injected HTML templates.

    The pretty JSON files are the source of truth.  Minified JSON and the
    aggregate ``all.json`` are derived at request/build time, so a forgotten
    ``json_miner.py`` run can never leave the site with stale minified data.
    """

    def __init__(self, docs_dir: Path) -> None:
        self.docs_dir = Path(docs_dir)
        # name -> (mtime_ns, size, raw bytes, parsed data)
        self._sources: dict[str, tuple[int, int, bytes, Any]] = {}
        # name -> (source states, content hash, raw bytes)
        self._documents: dict[str, tuple[tuple[tuple[str, int, int], ...], str, bytes]] = {}
        # page -> (template mtime_ns, data hash, body, etag)
        self._pages: dict[str, tuple[int, str, str, str]] = {}

    # ------------------------------------------------------------------
    # sources
    # ------------------------------------------------------------------
    def _source(self, name: str) -> tuple[int, int, bytes, Any]:
        if name not in BASE_FILE_SET:
            raise KeyError(name)

        path = self.docs_dir / f"{name}.json"
        stat = path.stat()
        cached = self._sources.get(name)
        if (
            cached is not None
            and cached[0] == stat.st_mtime_ns
            and cached[1] == stat.st_size
        ):
            return cached

        raw = path.read_bytes()
        data = json.loads(raw)
        item = (stat.st_mtime_ns, stat.st_size, raw, data)
        self._sources[name] = item
        return item

    def _source_state(self, names: tuple[str, ...]) -> tuple[tuple[str, int, int], ...]:
        state = []
        for name in names:
            mtime_ns, size, _, _ = self._source(name)
            state.append((name, mtime_ns, size))
        return tuple(state)

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------
    def document(self, name: str) -> tuple[str, bytes]:
        """Return (content hash, bytes) for a base/minified/aggregate document.

        Supports: features, features.min, ..., all, all.min.
        """
        is_min = name.endswith(".min")
        base = name[:-4] if is_min else name

        if base == "all":
            names = BASE_FILES
            state = self._source_state(names)
            cached = self._documents.get(name)
            if cached is not None and cached[0] == state:
                return cached[1], cached[2]

            aggregate = {key: self._source(key)[3] for key in names}
            raw = minify_json(aggregate) if is_min else pretty_json(aggregate)
            digest = content_hash(raw)
            self._documents[name] = (state, digest, raw)
            return digest, raw

        if base not in BASE_FILE_SET:
            raise KeyError(name)

        state = self._source_state((base,))
        cached = self._documents.get(name)
        if cached is not None and cached[0] == state:
            return cached[1], cached[2]

        pretty, data = self._source(base)[2], self._source(base)[3]
        raw = minify_json(data) if is_min else pretty
        digest = content_hash(raw)
        self._documents[name] = (state, digest, raw)
        return digest, raw

    # ------------------------------------------------------------------
    # pages
    # ------------------------------------------------------------------
    def page(self, page: str) -> tuple[str, str]:
        """Return (rendered HTML, etag) for a docs page."""
        spec = PAGE_SPECS.get(page)
        if spec is None:
            raise KeyError(page)

        template_rel, data_name = spec
        # Pages fetch the minified JSON, so the injected hash must be the
        # hash of the minified bytes.
        data_hash, _ = self.document(f"{data_name}.min")

        template_path = self.docs_dir / template_rel
        stat = template_path.stat()
        cached = self._pages.get(page)
        if (
            cached is not None
            and cached[0] == stat.st_mtime_ns
            and cached[1] == data_hash
        ):
            return cached[2], cached[3]

        template = template_path.read_text(encoding="utf-8")
        if HASH_TOKEN not in template:
            raise ValueError(f"Hash placeholder missing from {template_rel}")

        body = template.replace(HASH_TOKEN, data_hash)
        etag = 'W/"' + content_hash(body.encode("utf-8")) + '"'
        self._pages[page] = (stat.st_mtime_ns, data_hash, body, etag)
        return body, etag

    def page_data_file(self, page: str) -> str:
        """Public JSON filename (with extension) used by a page's loader."""
        spec = PAGE_SPECS[page]
        return f"{spec[1]}.min.json"


__all__ = [
    "BASE_FILES",
    "BASE_FILE_SET",
    "HASH_TOKEN",
    "PAGE_SPECS",
    "DocsSite",
    "content_hash",
    "minify_json",
    "pretty_json",
]
