# Zombie Slayer

A cross-platform network defense desktop app. Watches configured ports,
checks inbound connections against an authorized IP allow-list, and
terminates the local process behind any unauthorized connection —
grouped by protocol (SSH, Telnet, HTTP/S, FTP).

Built with PySide6 (Qt for Python) and `psutil`, so process termination
works the same way on Windows, macOS, and Linux — no shelling out to
`pkill`/`taskkill`.

## Project layout

```
ZombieSlayer/
├── core/                   # No GUI dependencies — the actual defense logic
│   ├── allowlist.py        # Authorized IP set, validated
│   ├── connection_monitor.py  # Per-port TCP listeners, emits events
│   ├── termination_engine.py  # Cross-platform process kill via psutil
│   └── settings_store.py   # JSON settings in the OS app-data dir
├── gui/                    # PySide6 UI
│   ├── main_window.py
│   ├── theme.qss           # Tactical dark-red/chrome theme
│   └── widgets/            # Dashboard, Allow List, Loadout, Settings tabs
├── assets/                 # icon.png / icon.ico / icon.icns
├── tests/
├── main.py                 # Entry point
├── zombieslayer.spec       # PyInstaller build spec (all 3 platforms)
└── .github/workflows/build.yml  # CI: builds + packages for Win/macOS/Linux
```

## Running from source

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Building a native binary locally

```bash
pip install -r requirements-dev.txt
pyinstaller zombieslayer.spec --noconfirm --clean
```

Output lands in `dist/`: `ZombieSlayer.exe` (Windows), `ZombieSlayer.app`
(macOS), or `ZombieSlayer` (Linux).

## Setting this up on GitHub

1. Push this folder as a new repository.
2. The workflow at `.github/workflows/build.yml` runs automatically on
   every push to `main` and on pull requests, building all three
   platforms in parallel via a GitHub Actions matrix.
3. Tag a commit `v1.0.0` (or any `v*` tag) and push the tag — this
   triggers the `release` job, which bundles all three build outputs
   into a GitHub Release automatically.

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Permissions note

Killing another process's connection and binding to low-numbered ports
(22, 80, 443, etc.) generally requires elevated privileges:

- **Windows:** run as Administrator
- **macOS/Linux:** run with `sudo`, or bind only to ports > 1024 during
  testing

## License

See `LICENSE.md`.
