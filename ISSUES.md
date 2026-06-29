# ISSUES.md

## Issue #1 — HF Spaces build failure: gradio version conflict
**Status:** Fixed (2026-06-29)
**Severity:** Critical — build blocked

**Root cause:** The HF Spaces builder reads `sdk_version: 5.7.1` from the README frontmatter and injects `gradio[oauth]==5.7.1` into the build's pip install. But `requirements.txt` specifies `gradio>=5.15.0`. Pip can't satisfy both `==5.7.1` and `>=5.15.0` → build fails with exit code 1.

**Fix:** Updated `sdk_version` from `5.7.1` → `5.15.0` in `README.md` to match the minimum version in `requirements.txt`.

---

## Issue #2 — Return value mismatch in error paths
**Status:** Fixed (commit 8763640)
**Severity:** High — runtime crash on invalid input

**Root cause:** Three error paths in `analyze_product_image()` returned `gr.update(visible=False)` as a second value, but the output component list expects only 1 value. This caused a Gradio interface error whenever the user uploaded no image or an invalid one.

**Fix:** Removed `gr.update(visible=False)` from the 3 error return paths so each returns exactly 1 value.

---

## Issue #3 — Missing `os` import for root_path support
**Status:** Fixed (commit 8763640)
**Severity:** Medium — NameError on startup when `GRADIO_ROOT_PATH` is set

**Root cause:** `app.py` referenced `os.getenv("GRADIO_ROOT_PATH", "")` but never imported `os`.

**Fix:** Added `import os` to the top of `app.py`.

---

## Issue #4 — API routing broken on HuggingFace Spaces
**Status:** Fixed (commit 8763640)
**Severity:** High — API calls fail behind HF reverse proxy

**Root cause:** HF Spaces serves apps under a subpath (e.g. `/spaces/user/repo`), but Gradio's default `root_path=""` causes API requests to hit the wrong URL, resulting in 404s.

**Fix:** Added `root_path=os.getenv("GRADIO_ROOT_PATH", "")` to `demo.launch()` so the app respects the subpath when deployed.

---

## Issue #5 — Missing `audioop-lts` dependency
**Status:** Fixed (commit 2876196)
**Severity:** Medium — ImportError on Python 3.13+

**Root cause:** Python 3.13 removed the built-in `audioop` module. A downstream dependency (likely via transformers/gradio) imports it, causing `ModuleNotFoundError`.

**Fix:** Added `audioop-lts` to `requirements.txt` — a backport that restores the module.

---

## Issue #6 — Unpinned gradio dependency
**Status:** Fixed (commit 11d423e)
**Severity:** Medium — non-reproducible builds, potential breakage on major bumps

**Root cause:** `requirements.txt` listed `gradio` without a version pin, meaning any new major release could break the app silently.

**Fix:** Pinned to `gradio>=5.15.0`.

---

## Issue #7 — Missing pydantic dependency
**Status:** Fixed (commit 11d423e)
**Severity:** Medium — ImportError at runtime

**Root cause:** Gradio's internal dependencies shifted and no longer transitively install a compatible `pydantic` version, causing import failures.

**Fix:** Added `pydantic>=2.10.0,<3.0` to `requirements.txt`.

---

## Issue #8 — `/gradio_api/info` returns 500 on HF Spaces
**Status:** Fixed (2026-06-29)
**Severity:** High — API endpoint broken, programmatic access fails

**Root cause:** Manually setting `root_path` via `GRADIO_ROOT_PATH` environment variable caused Gradio 5.x's API info endpoint (`/gradio_api/info`) to return HTTP 500 on HuggingFace Spaces. The main UI loaded fine, but the API routing for the info endpoint broke due to the manual `root_path` override conflicting with HF Spaces' internal routing.

**Fix:** Removed the manual `root_path` configuration. HF Spaces handles routing automatically — setting `root_path` manually is unnecessary and causes the API info endpoint to crash. Changed `demo.launch(root_path=root_path)` to `demo.launch()`.

---

## Issue #9 — "No API Found" error on HF Spaces (pydantic incompatibility)
**Status:** Fixed (2026-06-29)
**Severity:** High — API endpoint broken on HuggingFace Spaces

**Root cause:** The `pydantic>=2.10.0,<3.0` range allowed newer pydantic releases (2.11+) that introduced an incompatibility with Gradio's Starlette integration. This caused `TypeError: argument of type 'bool' is not iterable` and the "No API Found" error on HF Spaces. ([HF Discussion](https://discuss.huggingface.co/t/error-no-api-found/146226))

**Fix:** Pinned `pydantic==2.10.6` in `requirements.txt` — the last known version compatible with Gradio 5.x on HF Spaces.
