#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validateur JSON — projet traducteur PDF (brique n°1).

Vérifie qu'un fichier JSON produit par l'IA locale respecte EXACTEMENT le
schéma figé. Il ne corrige rien, ne traduit rien : il accepte ou refuse, et
quand il refuse il LOCALISE chaque problème (« page 4, bloc 3, fragment 2 »)
et les liste TOUS d'un coup (pas seulement le premier).

Usage :
    python validateur.py <fichier.json>

Code de sortie : 0 si valide, 1 sinon.
"""

import json
import sys

# Clés autorisées à chaque niveau — toute autre clé est une hallucination du 12B.
CLES_PAGE = {"page_number", "status", "blocks", "reason"}
CLES_BLOC_CONTENT = {"type", "content"}   # heading, paragraph
CLES_BLOC_LIST = {"type", "items"}        # list
CLES_FRAGMENT = {"text", "bold", "italic"}
STATUTS = {"translated", "no_translation"}
TYPES_BLOC = {"heading", "paragraph", "list"}


def valider_fragment(frag, ctx, erreurs):
    """Valide un fragment {text, bold?, italic?}."""
    if not isinstance(frag, dict):
        erreurs.append(f"{ctx} : devrait être un objet {{\"text\": …}}, "
                       f"trouvé {type_fr(frag)}.")
        return
    extra = set(frag) - CLES_FRAGMENT
    if extra:
        erreurs.append(f"{ctx} : clé(s) interdite(s) {sorted(extra)} "
                       f"(autorisées : text, bold, italic).")
    if "text" not in frag:
        erreurs.append(f"{ctx} : clé \"text\" manquante.")
    else:
        txt = frag["text"]
        if not isinstance(txt, str):
            erreurs.append(f"{ctx} : \"text\" doit être une chaîne, "
                           f"trouvé {type_fr(txt)}.")
        elif txt.strip() == "":
            erreurs.append(f"{ctx} : \"text\" est vide.")
    for cle in ("bold", "italic"):
        if cle in frag and not isinstance(frag[cle], bool):
            erreurs.append(f"{ctx} : \"{cle}\" doit être un booléen "
                           f"(true/false), trouvé {type_fr(frag[cle])}.")


def valider_liste_fragments(frags, ctx, erreurs):
    """Valide une liste de fragments non vide (le content d'un bloc/une ligne)."""
    if not isinstance(frags, list):
        erreurs.append(f"{ctx} : devrait être une liste de fragments, "
                       f"trouvé {type_fr(frags)}.")
        return
    if len(frags) == 0:
        erreurs.append(f"{ctx} : liste de fragments vide.")
        return
    for k, frag in enumerate(frags):
        valider_fragment(frag, f"{ctx}, fragment {k + 1}", erreurs)


def valider_bloc(bloc, ctx, erreurs):
    """Valide un bloc heading / paragraph / list."""
    if not isinstance(bloc, dict):
        erreurs.append(f"{ctx} : devrait être un objet, trouvé {type_fr(bloc)}.")
        return
    if "type" not in bloc:
        erreurs.append(f"{ctx} : clé \"type\" manquante.")
        return
    t = bloc["type"]
    if t not in TYPES_BLOC:
        erreurs.append(f"{ctx} : type \"{t}\" inconnu "
                       f"(attendus : heading, paragraph, list).")
        return

    if t in ("heading", "paragraph"):
        extra = set(bloc) - CLES_BLOC_CONTENT
        if extra:
            erreurs.append(f"{ctx} : clé(s) interdite(s) {sorted(extra)} "
                           f"pour un bloc {t} (autorisées : type, content).")
        if "content" not in bloc:
            erreurs.append(f"{ctx} : clé \"content\" manquante.")
        else:
            valider_liste_fragments(bloc["content"], ctx, erreurs)

    elif t == "list":
        extra = set(bloc) - CLES_BLOC_LIST
        if extra:
            erreurs.append(f"{ctx} : clé(s) interdite(s) {sorted(extra)} "
                           f"pour un bloc list (autorisées : type, items).")
        if "items" not in bloc:
            erreurs.append(f"{ctx} : clé \"items\" manquante.")
        else:
            items = bloc["items"]
            if not isinstance(items, list):
                erreurs.append(f"{ctx} : \"items\" doit être une liste, "
                               f"trouvé {type_fr(items)}.")
            elif len(items) == 0:
                erreurs.append(f"{ctx} : \"items\" est vide.")
            else:
                for l, ligne in enumerate(items):
                    valider_liste_fragments(
                        ligne, f"{ctx}, ligne {l + 1}", erreurs)


def valider_page(page, position, erreurs):
    """Valide une page. Retourne le page_number si c'est un entier valide, sinon None."""
    # Contexte par défaut tant qu'on n'a pas de numéro fiable.
    ctx = f"page en position {position}"
    if not isinstance(page, dict):
        erreurs.append(f"{ctx} : devrait être un objet, trouvé {type_fr(page)}.")
        return None

    # page_number d'abord, pour un contexte parlant dans les messages suivants.
    pn = page.get("page_number")
    pn_valide = isinstance(pn, int) and not isinstance(pn, bool) and pn >= 1
    if pn_valide:
        ctx = f"page {pn}"

    extra = set(page) - CLES_PAGE
    if extra:
        erreurs.append(f"{ctx} : clé(s) interdite(s) {sorted(extra)} "
                       f"(autorisées : page_number, status, blocks, reason).")

    if "page_number" not in page:
        erreurs.append(f"{ctx} : clé \"page_number\" manquante.")
    elif not pn_valide:
        erreurs.append(f"{ctx} : \"page_number\" doit être un entier ≥ 1, "
                       f"trouvé {pn!r}.")

    statut = page.get("status")
    if "status" not in page:
        erreurs.append(f"{ctx} : clé \"status\" manquante.")
    elif statut not in STATUTS:
        erreurs.append(f"{ctx} : status \"{statut}\" invalide "
                       f"(attendus : translated, no_translation).")

    if "reason" in page:
        if statut != "no_translation":
            erreurs.append(f"{ctx} : \"reason\" n'a de sens que si "
                           f"status = no_translation.")
        elif not (isinstance(page["reason"], str) and page["reason"].strip()):
            erreurs.append(f"{ctx} : \"reason\" doit être une chaîne non vide.")

    if "blocks" not in page:
        erreurs.append(f"{ctx} : clé \"blocks\" manquante.")
    else:
        blocks = page["blocks"]
        if not isinstance(blocks, list):
            erreurs.append(f"{ctx} : \"blocks\" doit être une liste, "
                           f"trouvé {type_fr(blocks)}.")
        elif statut == "translated" and len(blocks) == 0:
            erreurs.append(f"{ctx} : status translated mais \"blocks\" est vide.")
        elif statut == "no_translation" and len(blocks) != 0:
            erreurs.append(f"{ctx} : status no_translation mais \"blocks\" "
                           f"n'est pas vide.")
        else:
            for j, bloc in enumerate(blocks):
                valider_bloc(bloc, f"{ctx}, bloc {j + 1}", erreurs)

    return pn if pn_valide else None


def valider_sequence_pages(numeros, erreurs):
    """Vérifie la séquence des page_number : croissante de 1 en 1, sans trou ni doublon.
    (On n'impose pas de commencer à 1 : un extrait d'une seule page reste valide.)"""
    precedent = None
    for i, pn in enumerate(numeros):
        if pn is None:          # page_number déjà signalé comme invalide
            precedent = None
            continue
        if precedent is not None:
            if pn == precedent:
                erreurs.append(f"séquence : page_number {pn} en double "
                               f"(positions {i} et {i + 1}).")
            elif pn < precedent:
                erreurs.append(f"séquence : page_number {pn} (position {i + 1}) "
                               f"arrive après {precedent} — ordre rompu.")
            elif pn > precedent + 1:
                manquants = list(range(precedent + 1, pn))
                erreurs.append(f"séquence : trou avant page_number {pn} "
                               f"(position {i + 1}) — manque {manquants}.")
        precedent = pn


def valider(data, erreurs):
    """Point d'entrée logique : valide la structure complète déjà parsée."""
    if not isinstance(data, dict):
        erreurs.append(f"racine : devrait être un objet {{\"pages\": …}}, "
                       f"trouvé {type_fr(data)}.")
        return
    extra = set(data) - {"pages"}
    if extra:
        erreurs.append(f"racine : clé(s) interdite(s) {sorted(extra)} "
                       f"(seule \"pages\" est autorisée).")
    if "pages" not in data:
        erreurs.append("racine : clé \"pages\" manquante.")
        return
    pages = data["pages"]
    if not isinstance(pages, list):
        erreurs.append(f"racine : \"pages\" doit être une liste, "
                       f"trouvé {type_fr(pages)}.")
        return
    if len(pages) == 0:
        erreurs.append("racine : \"pages\" est vide.")
        return

    numeros = []
    for i, page in enumerate(pages):
        numeros.append(valider_page(page, i + 1, erreurs))
    valider_sequence_pages(numeros, erreurs)


def type_fr(valeur):
    """Nom de type lisible en français pour les messages."""
    if valeur is None:
        return "null"
    if isinstance(valeur, bool):
        return "booléen"
    if isinstance(valeur, int):
        return "entier"
    if isinstance(valeur, float):
        return "nombre"
    if isinstance(valeur, str):
        return "chaîne"
    if isinstance(valeur, list):
        return "liste"
    if isinstance(valeur, dict):
        return "objet"
    return type(valeur).__name__


def main(argv):
    # La console Windows est souvent en cp1252 et ne sait pas afficher ✅ ❌ ≥ —.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if len(argv) != 2:
        print("Usage : python validateur.py <fichier.json>")
        return 2
    chemin = argv[1]
    try:
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
    except OSError as e:
        print(f"Impossible de lire {chemin} : {e}")
        return 2

    try:
        data = json.loads(texte)
    except json.JSONDecodeError as e:
        print(f"❌ INVALIDE — JSON mal formé : {e.msg} "
              f"(ligne {e.lineno}, colonne {e.colno}).")
        print("   (Le 12B oublie souvent de fermer une accolade. "
              "Aucun contrôle de fond n'a pu être fait.)")
        return 1

    erreurs = []
    valider(data, erreurs)

    if not erreurs:
        n = len(data["pages"])
        print(f"✅ VALIDE — {n} page(s), conforme au schéma.")
        return 0

    print(f"❌ INVALIDE — {len(erreurs)} erreur(s) :")
    for msg in erreurs:
        print(f"  - {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
