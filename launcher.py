#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RemixZ Cleaner X — LAUNCHER (compilado a .exe)

Estrategia DEFINITIVA (repara: No module named 'json' / tkinter.filedialog):

  1) Preferir pythonw/python del sistema + RemixZ_Cleaner_X_App.py del DISCO
     → stdlib completa del intérprete real (json, ssl, tkinter, …).

  2) Fallback in-process: NUNCA vaciar sys.path.
     Pre-importar stdlib crítica (para que PyInstaller la empaquete) y
     reponer base_library.zip + _MEIPASS + stdlib en disco antes de cargar App.

Causa del bug:
  Un launcher mínimo no importa 'json'. PyInstaller no lo mete en el PYZ.
  Al cargar App.py / remixz_update.py del disco → ModuleNotFoundError: json.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# STDLIB CRÍTICA — importar SIEMPRE aquí para que PyInstaller las empaquete
# en el EXE (hidden imports de facto). No quitar aunque “no se usen”.
# ---------------------------------------------------------------------------
import importlib
import importlib.util
import json  # noqa: F401  — requerido por remixz_update / App
import os
import re  # noqa: F401
import shutil  # noqa: F401
import ssl  # noqa: F401
import subprocess
import sys
import tempfile  # noqa: F401
import threading  # noqa: F401
import time  # noqa: F401
import traceback
import zipfile  # noqa: F401
from pathlib import Path

try:
    import urllib.error  # noqa: F401
    import urllib.request  # noqa: F401
except Exception:
    pass

try:
    import dataclasses  # noqa: F401
except Exception:
    pass

try:
    import hashlib  # noqa: F401
    import base64  # noqa: F401
    import platform  # noqa: F401
    import copy  # noqa: F401
    import collections  # noqa: F401
    import concurrent.futures  # noqa: F401
except Exception:
    pass


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()


def _log(msg: str) -> None:
    try:
        with open(APP_DIR / "launcher_error.log", "a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def _find_pythonw() -> str | None:
    """Busca pythonw/python del sistema (nunca este EXE frozen)."""
    candidates: list[Path] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        for ver in ("Python312", "Python313", "Python311", "Python310", "Python39", "Python314"):
            base = Path(local) / "Programs" / "Python" / ver
            candidates.append(base / "pythonw.exe")
            candidates.append(base / "python.exe")
    for name in ("pythonw.exe", "python.exe"):
        for d in os.environ.get("PATH", "").split(os.pathsep):
            if not d:
                continue
            p = Path(d) / name
            if p.is_file():
                candidates.append(p)
    windir = os.environ.get("WINDIR", r"C:\Windows")
    candidates.append(Path(windir) / "py.exe")

    self_exe = None
    if getattr(sys, "frozen", False):
        try:
            self_exe = Path(sys.executable).resolve()
        except Exception:
            self_exe = None

    seen: set[str] = set()
    for c in candidates:
        try:
            key = str(c.resolve()).lower()
            resolved = c.resolve()
        except Exception:
            key = str(c).lower()
            resolved = c
        if key in seen:
            continue
        seen.add(key)
        if not c.is_file():
            continue
        if self_exe is not None:
            try:
                if resolved == self_exe:
                    continue
            except Exception:
                pass
        # Evitar stub de WindowsApps (abre Store)
        if "windowsapps" in key:
            continue
        return str(resolved)
    return None


def _run_with_system_python(app_py: Path) -> bool:
    """Lanza App.py con pythonw del sistema. True si se lanzó OK."""
    py = _find_pythonw()
    if not py:
        _log("No hay pythonw/python del sistema → fallback in-process.")
        return False

    env = os.environ.copy()
    lib = str(APP_DIR / "lib")
    pp = env.get("PYTHONPATH", "")
    # lib primero, sin pisar stdlib del intérprete
    env["PYTHONPATH"] = lib + (os.pathsep + pp if pp else "")
    env["REMIXZ_APP_DIR"] = str(APP_DIR)
    # Forzar que el hijo use su stdlib, no confunda con frozen
    env.pop("PYTHONHOME", None)

    flags = 0
    if os.name == "nt":
        flags = (
            getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        )
        if Path(py).name.lower() == "python.exe":
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        # Verificar que ese Python tiene json (stdlib real)
        check = subprocess.run(
            [py, "-c", "import json,tkinter; print('ok')"],
            capture_output=True,
            text=True,
            timeout=12,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        if check.returncode != 0 or "ok" not in (check.stdout or ""):
            _log(f"Python inválido (sin json/tkinter): {py} rc={check.returncode} {check.stderr}")
            return False

        subprocess.Popen(
            [py, str(app_py)],
            cwd=str(APP_DIR),
            env=env,
            close_fds=True,
            creationflags=flags if os.name == "nt" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        _log(f"OK: lanzado con sistema: {py} {app_py.name}")
        return True
    except Exception as e:
        _log(f"Fallo lanzar con {py}: {e}")
        return False


def _meipass() -> Path:
    return Path(getattr(sys, "_MEIPASS", APP_DIR / "_internal"))


def _ensure_frozen_stdlib_paths() -> None:
    """
    Restaura rutas del bundle PyInstaller SIN borrar sys.path.
    Crítico: base_library.zip + _MEIPASS deben permanecer.
    """
    extras: list[str] = []
    mei = _meipass()
    for p in (
        mei,
        APP_DIR / "_internal",
        mei / "base_library.zip",
        APP_DIR / "_internal" / "base_library.zip",
        APP_DIR / "stdlib",
        APP_DIR / "_internal" / "stdlib",
    ):
        try:
            if p.exists():
                extras.append(str(p.resolve()))
        except Exception:
            pass

    # Lib del Python embebido / prefix (por si hay DLL + Lib)
    for attr in ("base_prefix", "prefix", "exec_prefix"):
        root = getattr(sys, attr, None)
        if not root:
            continue
        for sub in ("Lib", "lib", "DLLs", "lib-dynload"):
            cand = Path(root) / sub
            if cand.exists():
                extras.append(str(cand.resolve()))

    # Insertar al final (no al principio) para no tapar APP_DIR
    for s in extras:
        if s not in sys.path:
            sys.path.append(s)

    # APP_DIR + lib al inicio (updates en disco) — sin wipe
    root = str(APP_DIR.resolve())
    lib = str((APP_DIR / "lib").resolve())
    for s in (lib, root):
        while s in sys.path:
            try:
                sys.path.remove(s)
            except ValueError:
                break
    sys.path.insert(0, root)
    if Path(lib).is_dir():
        sys.path.insert(1, lib)


def _preflight_stdlib() -> None:
    """Garantiza json (y amigos) importables antes de cargar App del disco."""
    _ensure_frozen_stdlib_paths()
    missing: list[str] = []
    for name in ("json", "ssl", "zipfile", "urllib.request", "pathlib"):
        try:
            importlib.import_module(name)
        except Exception as e:
            missing.append(f"{name}: {e}")

    if not missing:
        return

    # Último recurso: copiar json del sistema si hay python con stdlib
    _try_inject_stdlib_from_system()
    _ensure_frozen_stdlib_paths()
    still = []
    for name in ("json",):
        try:
            importlib.import_module(name)
        except Exception as e:
            still.append(f"{name}: {e}")
    if still:
        raise ImportError(
            "Stdlib incompleta en el EXE (falta json).\n"
            "Solución: instala Python 3.10+ o reinstala RemixZ con launcher nuevo.\n"
            + "\n".join(still + missing)
        )


def _try_inject_stdlib_from_system() -> None:
    """Copia módulos stdlib mínimos (json) junto al EXE si faltan en frozen."""
    py = _find_pythonw()
    if not py:
        return
    try:
        r = subprocess.run(
            [
                py,
                "-c",
                "import json,pathlib; print(pathlib.Path(json.__file__).parent "
                "if getattr(json,'__file__',None) else pathlib.Path(json.__path__[0]))",
            ],
            capture_output=True,
            text=True,
            timeout=12,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        src = (r.stdout or "").strip()
        if not src or not Path(src).exists():
            return
        dest_root = APP_DIR / "stdlib"
        dest_root.mkdir(parents=True, exist_ok=True)
        src_p = Path(src)
        # json es paquete (json/) o json.py
        if src_p.is_dir():
            dest = dest_root / "json"
            if not dest.exists():
                shutil.copytree(src_p, dest, dirs_exist_ok=True)
        elif src_p.is_file():
            shutil.copy2(src_p, dest_root / src_p.name)
        _log(f"stdlib inyectada desde sistema: {src} → {dest_root}")
    except Exception as e:
        _log(f"inject stdlib: {e}")


def _ensure_tkinter_path() -> None:
    candidates = [
        _meipass(),
        APP_DIR / "_internal",
        APP_DIR / "stdlib",
        APP_DIR,
    ]
    for attr in ("base_prefix", "prefix"):
        r = getattr(sys, attr, None)
        if r:
            candidates.append(Path(r) / "Lib")
    for base in candidates:
        try:
            if (base / "tkinter" / "filedialog.py").is_file() or (
                base / "tkinter" / "filedialog.pyc"
            ).is_file():
                s = str(base.resolve())
                if s in sys.path:
                    sys.path.remove(s)
                sys.path.insert(0, s)
                return
        except Exception:
            continue


def _import_tkinter_full() -> None:
    for k in list(sys.modules):
        if k == "tkinter" or k.startswith("tkinter."):
            del sys.modules[k]
    _ensure_tkinter_path()
    import tkinter  # noqa: F401
    import tkinter.filedialog  # noqa: F401
    import tkinter.ttk  # noqa: F401
    import tkinter.scrolledtext  # noqa: F401
    import tkinter.messagebox  # noqa: F401


def _load_py_from_disk(modname: str, filename: str):
    path = APP_DIR / filename
    if not path.is_file():
        alt = APP_DIR / "_internal" / filename
        if alt.is_file():
            path = alt
    if not path.is_file():
        raise FileNotFoundError(filename)

    for k in list(sys.modules):
        if k == modname or k.startswith(modname + "."):
            del sys.modules[k]

    spec = importlib.util.spec_from_file_location(modname, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    try:
        # Reafirmar stdlib justo antes de exec (App toca sys.path)
        _ensure_frozen_stdlib_paths()
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(modname, None)
        raise
    return mod


def _run_inprocess() -> None:
    """Fallback: cargar App dentro del EXE con stdlib pre-empaquetada."""
    _log("Usando fallback in-process (sin pythonw del sistema).")
    _preflight_stdlib()
    try:
        _import_tkinter_full()
    except Exception as e:
        _log(f"tkinter preload: {e}")
    _ensure_frozen_stdlib_paths()

    for name, fname in (
        ("fluent_ui", "fluent_ui.py"),
        ("remixz_update", "remixz_update.py"),
        ("remixz_djtools", "remixz_djtools.py"),
    ):
        try:
            _ensure_frozen_stdlib_paths()
            _load_py_from_disk(name, fname)
        except Exception as e:
            _log(f"preload {name}: {e}")

    _ensure_frozen_stdlib_paths()
    app = _load_py_from_disk("RemixZ_Cleaner_X_App", "RemixZ_Cleaner_X_App.py")
    if not hasattr(app, "main"):
        raise AttributeError("RemixZ_Cleaner_X_App.py sin main()")
    app.main()


def main() -> None:
    try:
        err = APP_DIR / "launcher_error.log"
        if err.is_file():
            err.unlink()
    except Exception:
        pass

    try:
        os.chdir(str(APP_DIR))
        app_py = APP_DIR / "RemixZ_Cleaner_X_App.py"
        if not app_py.is_file():
            raise FileNotFoundError(f"Falta RemixZ_Cleaner_X_App.py en:\n{APP_DIR}")

        # Sanity: si ya estamos en Python real, json siempre existe
        try:
            import json as _j  # noqa: F401
            _log(f"preflight json OK (frozen={getattr(sys, 'frozen', False)})")
        except Exception as e:
            _log(f"preflight json FAIL: {e}")
            _try_inject_stdlib_from_system()
            _ensure_frozen_stdlib_paths()
            import json as _j  # noqa: F401

        # 1) Camino preferido: Python del sistema
        if _run_with_system_python(app_py):
            return

        # 2) Fallback in-process
        _run_inprocess()

    except Exception as e:
        msg = f"Error fatal en el launcher:\n{e}\n\n{traceback.format_exc()}"
        try:
            (APP_DIR / "launcher_error.log").write_text(msg, encoding="utf-8")
        except Exception:
            pass
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "RemixZ Cleaner X — Launcher",
                f"No se pudo iniciar.\n\n{e}\n\n"
                f"Prueba: ejecutar_Cleaner_X.vbs\n"
                f"Log: {APP_DIR / 'launcher_error.log'}",
            )
            root.destroy()
        except Exception:
            pass
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
