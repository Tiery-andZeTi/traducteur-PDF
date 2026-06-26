#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assembler.py — assemblage final (brique n°5).

Produit le PDF final en interfoliant, pour chaque page :
    1) la page VO (originale) rasterisée depuis le PDF source,
    2) la page VF (traduction) rendue par WeasyPrint, juste après.

Ordre final : VO1, VF1, VO2, VF2, …  (invariant 1 page VO = 1 page VF).

Contrat de mapping : la page VF de page_number N est appariée à la page N
(1-based) du PDF source.

Chaîne complète : JSON --valide--> HTML/CSS --WeasyPrint--> VF (en mémoire)
                  + PDF source --rasterise--> VO ;  interfoliage --> PDF final.

Usage :
    python assembler.py <entree.json> <source.pdf> [sortie.pdf]
"""

import json
import os
import sys

import fitz  # PyMuPDF

import build_pdf
import json_to_html as j2h
from pdf_engine import HTML
from validateur import valider

DPI_VO = 200  # résolution de rasterisation des pages originales


def construire_vf_pdf(data):
    """Rend le PDF VF (toutes pages) en mémoire et retourne un document fitz."""
    html_final, avertissements = build_pdf.construire(data)
    vf_bytes = HTML(string=html_final, base_url=".").write_pdf(
        stylesheets=[build_pdf._feuille_style()])
    return fitz.open(stream=vf_bytes, filetype="pdf"), avertissements


def assembler(data, source_pdf, sortie):
    """Interfolie VO (rasterisée) et VF, dans l'ordre VO, VF, VO, VF, …"""
    src = fitz.open(source_pdf)
    vf, avertissements = construire_vf_pdf(data)
    final = fitz.open()

    manquantes = []
    for idx, page in enumerate(data["pages"]):
        pn = page["page_number"]
        src_index = pn - 1  # page_number N -> page source N (1-based)

        # --- VO : page source rasterisée en image ---
        if 0 <= src_index < src.page_count:
            spage = src[src_index]
            pix = spage.get_pixmap(dpi=DPI_VO)
            vo = final.new_page(width=spage.rect.width, height=spage.rect.height)
            vo.insert_image(vo.rect, pixmap=pix)
        else:
            manquantes.append(pn)
            # Page VO absente du source : on insère une page blanche pour ne pas
            # casser l'alternance VO/VF.
            final.new_page()

        # --- VF : page traduite, juste après ---
        final.insert_pdf(vf, from_page=idx, to_page=idx)

    final.save(sortie, deflate=True, garbage=4)
    final.close()
    src.close()
    vf.close()
    return avertissements, manquantes


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if len(argv) not in (3, 4):
        print("Usage : python assembler.py <entree.json> <source.pdf> [sortie.pdf]")
        return 2

    entree, source_pdf = argv[1], argv[2]
    sortie = argv[3] if len(argv) == 4 else (
        entree[:-5] + "_final.pdf" if entree.lower().endswith(".json")
        else entree + "_final.pdf"
    )

    if not os.path.isfile(source_pdf):
        print(f"PDF source introuvable : {source_pdf}")
        return 2

    try:
        with open(entree, encoding="utf-8") as f:
            data = json.loads(f.read())
    except OSError as e:
        print(f"Impossible de lire {entree} : {e}")
        return 2
    except json.JSONDecodeError as e:
        print(f"❌ JSON mal formé : {e.msg} (ligne {e.lineno}, colonne {e.colno}).")
        return 1

    erreurs = []
    valider(data, erreurs)
    if erreurs:
        print(f"❌ JSON invalide — {len(erreurs)} erreur(s), aucun PDF produit :")
        for msg in erreurs:
            print(f"  - {msg}")
        return 1

    avertissements, manquantes = assembler(data, source_pdf, sortie)

    n = len(data["pages"])
    print(f"✅ PDF final assemblé : {sortie} "
          f"({n} page(s) VO+VF = {2 * n} pages).")
    for a in avertissements:
        print(f"  · {a}")
    if manquantes:
        print(f"  ⚠ pages VO absentes du source (page blanche insérée) : {manquantes}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
