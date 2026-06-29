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
