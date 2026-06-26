#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_engine.py — accès centralisé à WeasyPrint.

Sous Windows, WeasyPrint a besoin des DLL natives GTK/Pango (installées via
MSYS2 dans C:\\msys64\\mingw64\\bin). Ce module ajoute ce dossier au chemin de
recherche AVANT d'importer weasyprint, pour que tous les scripts puissent
simplement faire :

    from pdf_engine import HTML, CSS
"""

import os
import sys

# Dossier des DLL GTK/Pango installées par MSYS2 (modifiable via la variable
# d'environnement GTK_BIN_DIR si l'installation est ailleurs).
_GTK_BIN = os.environ.get("GTK_BIN_DIR", r"C:\msys64\mingw64\bin")

if sys.platform == "win32" and os.path.isdir(_GTK_BIN):
    os.add_dll_directory(_GTK_BIN)

from weasyprint import HTML, CSS  # noqa: E402  (import après add_dll_directory)

__all__ = ["HTML", "CSS"]
