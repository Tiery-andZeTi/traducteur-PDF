#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON → HTML — projet traducteur PDF (brique n°2).

Transforme un JSON de traduction (conforme au schéma figé) en un document HTML.
Le HTML sera ensuite habillé par le CSS (brique 3) puis rendu en PDF par
WeasyPrint (brique 4), avant l'interfoliage VO/VF par PyMuPDF (brique 5).

Le convertisseur VALIDE d'abord le JSON (brique 1) : il refuse de produire
quoi que ce soit à partir d'un JSON non conforme.

Mapping :
    heading   -> <h2>
    paragraph -> <p>
    list      -> <ul><li>…</li></ul>
    fragment  -> texte, enveloppé de <strong> si bold, de <em> si italic
    page      -> <section class="page" data-page="N"> … </section>
                 (page no_translation -> section vide marquée pour la VF de référence)

Usage :
    python json_to_html.py <entree.json> [sortie.html]

Code de sortie : 0 si OK, 1 si JSON invalide, 2 si problème d'usage/fichier.
"""

import html
import json
import sys

from validateur import valider


def rendre_fragment(frag):
    """Un fragment {text, bold?, italic?} -> chaîne HTML échappée."""
    morceau = html.escape(frag["text"], quote=False)
    if frag.get("italic"):
        morceau = f"<em>{morceau}</em>"
    if frag.get("bold"):
        morceau = f"<strong>{morceau}</strong>"
    return morceau


def rendre_fragments(frags):
    """Concatène une liste de fragments en HTML inline."""
    return "".join(rendre_fragment(f) for f in frags)


def rendre_bloc(bloc):
    """Un bloc -> ligne(s) HTML (sans indentation de page)."""
    t = bloc["type"]
    if t == "heading":
        return f"<h2>{rendre_fragments(bloc['content'])}</h2>"
    if t == "paragraph":
        return f"<p>{rendre_fragments(bloc['content'])}</p>"
    if t == "list":
        lignes = "".join(
            f"<li>{rendre_fragments(ligne)}</li>" for ligne in bloc["items"]
        )
        return f"<ul>{lignes}</ul>"
    # Inatteignable : le validateur a déjà rejeté tout autre type.
    raise ValueError(f"type de bloc inattendu : {t!r}")


def grouper_blocs(blocks):
    """Regroupe les blocs en « rubriques » : une étiquette (heading) + le corps
    (paragraphes/listes) qui la suit, pour aligner chaque étiquette en marge
    face à son texte. Les blocs avant tout heading forment une rubrique sans
    étiquette."""
    groupes = []
    courant = {"label": None, "corps": []}
    for b in blocks:
        if b["type"] == "heading":
            if courant["label"] is not None or courant["corps"]:
                groupes.append(courant)
            courant = {"label": b, "corps": []}
        else:
            courant["corps"].append(b)
    if courant["label"] is not None or courant["corps"]:
        groupes.append(courant)
    return groupes


def rendre_groupe(groupe):
    """Une rubrique -> <div class='rubrique'> avec colonne étiquette + colonne corps."""
    if groupe["label"] is not None:
        label = f"<h2>{rendre_fragments(groupe['label']['content'])}</h2>"
    else:
        label = ""
    corps = "".join(rendre_bloc(b) for b in groupe["corps"])
    return ('      <div class="rubrique">'
            f'<div class="label">{label}</div>'
            f'<div class="corps">{corps}</div>'
            "</div>")


def rendre_page(page, font_pt=None):
    """Une page -> une <section class='page'>.

    font_pt : taille de police imposée à la page (autofit). None = défaut du CSS.
    """
    pn = page["page_number"]
    style = f' style="font-size:{font_pt}pt"' if font_pt is not None else ""
    if page["status"] == "no_translation":
        reason = html.escape(page.get("reason", ""), quote=True)
        attr = f' data-reason="{reason}"' if reason else ""
        # Page VF de référence : volontairement vide, marquée pour l'assemblage.
        return (f'    <section class="page no-translation" '
                f'data-page="{pn}"{attr}></section>')
    corps = "\n".join(rendre_groupe(g) for g in grouper_blocs(page["blocks"]))
    return (f'    <section class="page" data-page="{pn}"{style}>\n'
            f"{corps}\n"
            f"    </section>")


def envelopper(sections):
    """Enveloppe une ou plusieurs <section> dans un document HTML autonome."""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "  <head>\n"
        '    <meta charset="utf-8">\n'
        "    <title>Traduction</title>\n"
        '    <link rel="stylesheet" href="style.css">\n'
        "  </head>\n"
        "  <body>\n"
        f"{sections}\n"
        "  </body>\n"
        "</html>\n"
    )


def rendre_document(data):
    """Le JSON complet -> document HTML autonome."""
    sections = "\n".join(rendre_page(p) for p in data["pages"])
    return envelopper(sections)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if len(argv) not in (2, 3):
        print("Usage : python json_to_html.py <entree.json> [sortie.html]")
        return 2

    entree = argv[1]
    sortie = argv[2] if len(argv) == 3 else (
        entree[:-5] + ".html" if entree.lower().endswith(".json")
        else entree + ".html"
    )

    try:
        with open(entree, encoding="utf-8") as f:
            texte = f.read()
    except OSError as e:
        print(f"Impossible de lire {entree} : {e}")
        return 2

    try:
        data = json.loads(texte)
    except json.JSONDecodeError as e:
        print(f"❌ JSON mal formé : {e.msg} (ligne {e.lineno}, colonne {e.colno}).")
        return 1

    erreurs = []
    valider(data, erreurs)
    if erreurs:
        print(f"❌ JSON invalide — {len(erreurs)} erreur(s), aucun HTML produit :")
        for msg in erreurs:
            print(f"  - {msg}")
        return 1

    html_doc = rendre_document(data)
    try:
        with open(sortie, "w", encoding="utf-8") as f:
            f.write(html_doc)
    except OSError as e:
        print(f"Impossible d'écrire {sortie} : {e}")
        return 2

    print(f"✅ HTML généré : {sortie} ({len(data['pages'])} page(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
