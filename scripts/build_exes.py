#!/usr/bin/env python3
"""
Build standalone executables (PyInstaller --onefile) for the boxes tools.

Each executable contains the complete ``boxes`` package and all third
party dependencies.  Because the generator modules are discovered
dynamically (``pkgutil.walk_packages``), every ``boxes.*`` submodule is
passed as a hidden import.

Output goes to ``dist/standalone/`` (git-ignored).  The directory depth
is deliberate: ``Path(__file__).parent.parent.parent`` keeps pointing at
the repository root so ``examples.yml`` and ``static/`` still resolve.

Requires: pyinstaller (``pip install pyinstaller``) in the running
environment, plus the runtime dependencies from requirements.txt.

Usage: python scripts/build_exes.py
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_environment() -> None:
    """Re-exec with a repo venv if the current interpreter lacks PyInstaller."""
    try:
        import PyInstaller  # noqa: F401
        import markdown  # noqa: F401
        import qrcode  # noqa: F401
        import shapely  # noqa: F401
        import yaml  # noqa: F401
        return
    except ImportError:
        pass
    for candidate in (
        os.path.join(ROOT, "venv-win-native", "Scripts", "python.exe"),
        os.path.join(ROOT, "venv-win-native", "bin", "python"),
        os.path.join(ROOT, "venv", "Scripts", "python.exe"),
        os.path.join(ROOT, "venv", "bin", "python"),
    ):
        if os.path.exists(candidate):
            os.execv(candidate, [candidate, os.path.abspath(__file__), *sys.argv[1:]])
    sys.exit(
        "PyInstaller or the runtime dependencies are not installed for this\n"
        "interpreter.\n"
        "Install them (pip install -r requirements.txt pyinstaller) or run\n"
        "this script with the project venv, e.g.:\n"
        "  venv-win-native/Scripts/python.exe scripts/build_exes.py"
    )
OUT_DIR = os.path.join(ROOT, "dist", "standalone")
WORK_DIR = os.path.join(ROOT, "build", "standalone")
SPEC_DIR = os.path.join(ROOT, "build", "specs")

# standalone name -> source file (relative to ROOT).
# boxes_proxy is intentionally excluded: it is an Inkscape extension and
# requires inkex/lxml which only exist inside Inkscape.
TARGETS = {
    "boxes": "boxes/scripts/boxes_main.py",
    "boxes_cli": "boxes/scripts/boxes_cli.py",
    "boxes_server": "boxes/scripts/boxesserver.py",
    "boxes_generator": "boxes/scripts/boxes_generator.py",
    "boxes2inkscape": "scripts/boxes2inkscape",
    "boxes2pot": "scripts/boxes2pot",
}


# runtime data bundled into the executables (needed by boxes_server for
# the web UI and by the examples commands)
DATA = [
    ("static", "static"),
    ("locale", "locale"),
    ("examples.yml", "."),
]


def hidden_imports() -> list[str]:
    # make the repository root importable so collect_submodules finds boxes
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from PyInstaller.utils.hooks import collect_submodules

    mods = collect_submodules("boxes")
    # boxes.scripts are the CLI entry points themselves, not needed inside
    # the frozen apps (and boxes_proxy would drag in missing inkex deps).
    return [m for m in mods if not m.startswith("boxes.scripts")]


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(SPEC_DIR, exist_ok=True)

    hidden = hidden_imports()
    print(f"{len(hidden)} hidden imports")

    for name, rel in TARGETS.items():
        src = os.path.join(ROOT, rel)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", name,
            "--distpath", OUT_DIR,
            "--workpath", os.path.join(WORK_DIR, name),
            "--specpath", SPEC_DIR,
            "--clean",
            "--noconfirm",
        ]
        for src_data, dest in DATA:
            cmd += ["--add-data", os.path.join(ROOT, src_data) + os.pathsep + dest]
        for mod in hidden:
            cmd += ["--hidden-import", mod]
        cmd.append(src)
        print(f"=== building {name} ===")
        subprocess.run(cmd, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    ensure_environment()
    sys.exit(main())
