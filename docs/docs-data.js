/*
 * Fast Rub docs data loader.
 *
 * The docs server injects a content hash into
 * <meta name="docs-hash" content="...">.  Data is requested as
 * ../<name>.json?h=<hash>; unchanged JSON keeps the same URL and is served
 * from the browser cache, while changed JSON gets a new URL.
 */
(function () {
  "use strict";

  // Resolve data next to the loader itself, so it works at the site root
  // (/docs-data.js -> /features.json) and under /docs
  // (/docs/docs-data.js -> /docs/features.json).
  const scriptUrl = document.currentScript
    ? document.currentScript.src
    : window.location.href;

  function getHash() {
    const meta = document.querySelector('meta[name="docs-hash"]');
    return meta ? (meta.getAttribute("content") || "") : "";
  }

  async function load(name) {
    const hash = getHash();
    const hasContentHash = !!hash && hash.indexOf("__FASTRUB_DOCS_HASH__") === -1;
    if (!hasContentHash) {
      // Static preview / old host: no server-injected hash.  Fall back to a
      // revalidated URL so the page still works, just without immutable
      // caching for the JSON.
      console.warn(
        "[fast_rub docs] server hash not injected; using revalidated JSON URLs."
      );
    }

    // With a server/build-injected hash, fetch the generated minified file.
    // Without a hash (plain static preview), prefer the pretty source of
    // truth over a possibly stale committed .min.json.
    const dataName = hasContentHash ? name + ".min.json" : name + ".json";
    const url = new URL(dataName, scriptUrl);
    if (hasContentHash) {
      url.searchParams.set("h", hash);
    }

    let response = await fetch(url.toString(), {
      cache: hasContentHash ? "force-cache" : "no-cache",
    });

    // Defensive fallback: an older/partial deployment may not have the
    // minified file yet. The pretty source is always present.
    if (hasContentHash && response.status === 404) {
      const prettyUrl = new URL(name + ".json", scriptUrl);
      response = await fetch(prettyUrl.toString(), { cache: "no-cache" });
    }

    if (!response.ok) {
      throw new Error("HTTP " + response.status + " — " + url.toString());
    }
    return response.json();
  }

  function showError(containerId, error) {
    const box = document.getElementById(containerId);
    if (!box) {
      console.error(error);
      return;
    }

    box.innerHTML = "";
    const panel = document.createElement("div");
    panel.style.cssText =
      "margin:2rem 0;padding:1.2rem 1.5rem;border-radius:10px;" +
      "background:#fff3f3;border-right:4px solid #e53935;color:#5a1a1a;";

    const title = document.createElement("strong");
    title.textContent = "خطا در بارگذاری مستندات";
    panel.appendChild(title);

    const detail = document.createElement("p");
    detail.style.margin = "0.6rem 0 0";
    detail.textContent = (error && error.message) ? error.message : String(error);
    panel.appendChild(detail);

    const hint = document.createElement("p");
    hint.style.margin = "0.6rem 0 0";
    hint.textContent =
      "مسیر JSON و سرور مستندات را بررسی کنید: " +
      "uvicorn docs_server.app:app --port 8000";
    panel.appendChild(hint);

    box.appendChild(panel);
    console.error("[fast_rub docs]", error);
  }

  window.DocsData = { getHash: getHash, load: load, showError: showError };
})();
