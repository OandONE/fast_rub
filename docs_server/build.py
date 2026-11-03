"""Build the static Fast Rub docs site for GitHub Pages.

This is the GitHub-Pages counterpart of ``docs_server.app``: it renders the
same hash-injected HTML pages, generates minified JSON and the aggregate
``all.json`` from the pretty JSON sources, and writes a self-contained
``_site`` directory.

Usage:

    python -m docs_server.build --out _site

No third-party packages are required.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .render import BASE_FILES, PAGE_SPECS, DocsSite

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_DIR = ROOT / "docs"
DEFAULT_OUT_DIR = ROOT / "_site"

def build(docs_dir: Path = DEFAULT_DOCS_DIR, out_dir: Path = DEFAULT_OUT_DIR) -> Path:
    docs_dir = Path(docs_dir)
    out_dir = Path(out_dir)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    site = DocsSite(docs_dir)

    # 1) rendered pages (hash-injected templates)
    for page in PAGE_SPECS:
        body, _ = site.page(page)
        target = out_dir / page / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    # 2) static files used by the pages
    for name in ("index.html", "docs-data.js", "icon.jpg", "manifest.json"):
        source = docs_dir / name
        if source.is_file():
            shutil.copy2(source, out_dir / name)

    # 3) JSON documents: pretty sources, generated minified and aggregate files
    names = (
        list(BASE_FILES)
        + [f"{name}.min" for name in BASE_FILES]
        + ["all", "all.min"]
    )
    for name in names:
        _, raw = site.document(name)
        (out_dir / f"{name}.json").write_bytes(raw)

    # GitHub Pages should serve the files as-is, without Jekyll processing.
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Built docs into {out_dir}")
    print(f"  pages: {', '.join(PAGE_SPECS)}")
    print(f"  json : {', '.join(names)}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static Fast Rub docs")
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    build(args.docs_dir, args.out)


if __name__ == "__main__":
    main()
