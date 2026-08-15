# AGENTS.md

Legacy Plex Framework 2 metadata agent that matches JAV rips against libredmm.com's JSON API. The entire plugin is one Python 2.7 file: `Contents/Code/__init__.py` (single `Librefanza(Agent.Movies)` class). No build, lint, or test infrastructure — the checkout in `Plug-ins/` *is* the live install.

## Develop / verify cycle

- Syntax-check with Plex's own interpreter (system `python2` no longer exists on macOS):

  ```bash
  PYHOME="/Applications/Plex Media Server.app/Contents/Resources/Python"
  PYTHONHOME="$PYHOME" PYTHONPATH="$PYHOME/python27.zip:$PYHOME/python2.7" \
    "/Applications/Plex Media Server.app/Contents/MacOS/Plex Script Host" -c \
    "import py_compile; py_compile.compile('Contents/Code/__init__.py', doraise=True, cfile='/dev/null'); print 'OK'"
  ```

- Reload after edits by restarting PMS: `osascript -e 'quit app "Plex Media Server"' && open -a "Plex Media Server"`.
- Plugin log: `~/Library/Logs/Plex Media Server/PMS Plugin Logs/com.libredmm.plex.log`. Agent registration appears in `com.plexapp.system.log` ("Receiving agent info from com.libredmm.plex").
- Code is black-formatted (see the "auto format" commit); keep that style.

## Plex sandbox constraints (learned the hard way)

- Even under the `Elevated` code policy, source is compiled with **RestrictedPython**: identifiers starting with `_` (including a bare `_` unpacking target) fail the whole plugin at load with a SyntaxError in the log.
- Framework globals are injected, never imported: `Agent`, `Locale`, `MetadataSearchResult`, `JSON`, `HTTP`, `Proxy`, `Log`, `Prefs`, `Core`. Stdlib imports (`urllib`, `base64`, `datetime`, `re`, `json`, `urlparse`) work fine.
- `JSON.ObjectFromString`/`ObjectFromURL` reject payloads over 5 MB — use stdlib `json` for anything bigger.
- Python 2.7 only: no f-strings; paths from `media.filename` may arrive as UTF-8 `str` and need `.decode("utf-8")`.
- PMS exposes **one agent per bundle identifier per media type**. A second `Agent.Movies` class in this bundle registers but never appears in the library-agent UI — that is why Vixen-siterip support lives in the sibling `librevixen.bundle` (identifier `com.libredmm.vixen`) instead of here. A brand-new agent bundle may need **two** PMS restarts before it shows up: the first persists its agent info in the system bundle's Dict, the second lists it.

## Architecture

- `search()`: derives the movie ID from the **parent directory name**'s first whitespace token (expected layout `ABC-123 Title/file.mp4`), builds `http://www.libredmm.com/movies/<id>.json`, returns one result with score 100. Manual match accepts a pasted libredmm.com URL (`.json` appended if missing) or free text normalized by `librefanzaURL()`.
- Result ids are `"librefanza|" + base64(url)`; `update()` guards on the prefix and keeps a `TypeError` fallback that treats the payload as a raw ID (pre-base64 id scheme compatibility) — don't remove it.
- `update()` re-fetches the JSON and maps fields; `rating` is deliberately not pulled (commit 4893e33).
- `contributes_to = ["com.libredmm.plex"]` is self-referential and effectively a no-op; harmless.

## Conventions

- Commits are authored with the repo-local identity `LibreDMM <admin@libredmm.com>` (already in `.git/config`), subjects short and lowercase.
- This repository is public-facing: keep it self-contained; no references to private dotfiles or the home network.
