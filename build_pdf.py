#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pdf.py — JSON -> PDF VF (briques 2+3+4 réunies).

Chaîne : valide le JSON (brique 1) -> HTML (brique 2) -> CSS (brique 3) ->
WeasyPrint, avec AUTOFIT (brique 4) : si le texte d'une page déborde sur une
2e page PDF, on réduit la taille de police de CETTE page jusqu'à ce qu'elle
tienne sur une seule page — l'invariant « 1 page VO = 1 page VF » est ainsi
préservé même sur une page chargée.

Les PDF ScottsBassLessons sont aérés : en pratique l'autofit ne se déclenche
quasiment jamais. C'est un filet de sécurité (utile pour d'autres PDF un jour).

Usage :
    python build_pdf.py <entree.json> [sortie.pdf]
"""

import json
import os
import sys

import json_to_html as j2h
from pdf_engine import HTML, CSS
from validateur import valider

CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")

TAILLE_BASE = 11.0     # pt — taille nominale (doit refléter le CSS)
TAILLE_MIN = 7.0       # pt — plancher en dessous duquel on renonce à réduire
PAS = 0.5              # pt — décrément de l'autofit


def _feuille_style():
    return CSS(filename=CSS_PATH)


def nb_pages_pdf(section_html):
    """Nombre de pages PDF produites par une section seule."""
    doc = j2h.envelopper(section_html)
    rendu = HTML(string=doc, base_url=".").render(stylesheets=[_feuille_style()])
    return len(rendu.pages)


def taille_qui_tient(page):
    """Cherche la plus grande taille de police (de TAILLE_BASE à TAILLE_MIN)
    pour laquelle la page tient sur UNE seule page PDF.
    Retourne (taille, deborde) ; deborde=True si même TAILLE_MIN ne suffit pas."""
    # Cas le plus courant : la taille de base tient déjà.
    if nb_pages_pdf(j2h.rendre_page(page)) <= 1:
        return None, False  # None = on garde le défaut du CSS

    taille = TAILLE_BASE - PAS
    while taille >= TAILLE_MIN:
        if nb_pages_pdf(j2h.rendre_page(page, font_pt=taille)) <= 1:
            return taille, False
        taille -= PAS
    return TAILLE_MIN, True  # déborde malgré tout : on prend le plancher


def construire(data):
    """Construit le HTML final, page par page, avec autofit."""
    sections = []
    avertissements = []
    for page in data["pages"]:
        pn = page["page_number"]
        if page["status"] == "no_translation":
            sections.append(j2h.rendre_page(page))
            continue
        taille, deborde = taille_qui_tient(page)
        if taille is not None:
            note = f"page {pn} : autofit -> {taille:g} pt"
            if deborde:
                note += f" (déborde encore au plancher {TAILLE_MIN:g} pt)"
            avertissements.append(note)
        sections.append(j2h.rendre_page(page, font_pt=taille))
    return j2h.envelopper("\n".join(sections)), avertissements


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if len(argv) not in (2, 3):
        print("Usage : python build_pdf.py <entree.json> [sortie.pdf]")
        return 2

    entree = argv[1]
    sortie = argv[2] if len(argv) == 3 else (
        entree[:-5] + ".pdf" if entree.lower().endswith(".json")
        else entree + ".pdf"
    )

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

    html_final, avertissements = construire(data)
    HTML(string=html_final, base_url=".").write_pdf(
        sortie, stylesheets=[_feuille_style()])

    n = len(data["pages"])
    print(f"✅ PDF VF généré : {sortie} ({n} page(s)).")
    for a in avertissements:
        print(f"  · {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
