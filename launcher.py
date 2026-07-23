#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RemixZ Cleaner X — LAUNCHER (único archivo que se compila a .exe)

Arquitectura:
  RemixZ_Cleaner_X.exe  (este launcher, PyInstaller)
       └── carga SIEMPRE RemixZ_Cleaner_X_App.py desde DISCO
           (junto al .exe), no el código frozen del bundle.

Así los updates de GitHub que sobrescriben .py se ven al reiniciar
sin recompilar el ejecutable.
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()


def _prefer_disk_path() -> None:
    """sys.path: carpeta del exe primero (lib, .py actualizados)."""
    root = str(APP_DIR)
    lib = str(APP_DIR / "lib")
    # Quitar duplicados y poner APP_DIR en [0]
    cleaned = [p for p in sys.path if p not in (root, lib)]
    sys.path[:] = [root]
    if Path(lib).is_dir():
        sys.path.append(lib)
    sys.path.extend(cleaned)


def _load_app_from_disk():
    """
    Importa RemixZ_Cleaner_X_App SOLO desde archivo en disco.
    No usa el módulo frozen del archive de PyInstaller.
    """
    app_py = APP_DIR / "RemixZ_Cleaner_X_App.py"
    if not app_py.is_file():
        raise FileNotFoundError(
            f"No se encontró RemixZ_Cleaner_X_App.py en:\n{APP_DIR}\n"
            "El update debe dejar este archivo junto al .exe."
        )

    # Evitar módulo cached / frozen con el mismo nombre
    name = "RemixZ_Cleaner_X_App"
    for k in list(sys.modules):
        if k == name or k.startswith(name + "."):
            del sys.modules[k]

    spec = importlib.util.spec_from_file_location(name, str(app_py))
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo crear spec para {app_py}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    try:
        import os

        os.chdir(APP_DIR)
        _prefer_disk_path()
        app = _load_app_from_disk()
        if not hasattr(app, "main"):
            raise AttributeError("RemixZ_Cleaner_X_App.py no define main()")
        app.main()
    except Exception as e:
        try:
            log = APP_DIR / "launcher_error.log"
            with open(log, "w", encoding="utf-8") as f:
                f.write(f"Error fatal en el launcher:\n{e}\n\n{traceback.format_exc()}")
        except Exception:
            pass
        # Reintentar mostrar error mínimo si hay tk
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "RemixZ Cleaner X — Launcher",
                f"No se pudo iniciar la app.\n\n{e}\n\n"
                f"Revisa launcher_error.log en:\n{APP_DIR}",
            )
            root.destroy()
        except Exception:
            pass
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
