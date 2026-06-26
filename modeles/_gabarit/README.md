# Gabarit — accueillir un nouveau modèle

`consigne.md` ici est un **prompt neutre et réutilisable** : rôle + schéma JSON
attendu, **sans glossaire, sans terme de solfège, sans réglage spécifique, sans
règle anti-boucle**. (C'est l'ancien `CONSIGNE_TRADUCTEUR_minimal.md`.)

## Méthode pour tester un nouveau LLM

1. Charger le modèle dans LM Studio (Local Server, port 1234).
2. Lancer un PDF court avec ce gabarit :
   ```powershell
   .\.venv\Scripts\python.exe traduire_pdf.py "court.pdf" --model <id-du-modele> --consigne modeles\_gabarit\consigne.md
   ```
   (ajuster `--temperature` / `--reasoning-effort` selon ce que le modèle exige —
   chaque modèle se recalibre **de zéro**).
3. **Observer** ce que le modèle produit seul : qualité de trad, gestion des
   partitions, structure, vocabulaire, tendance à boucler.
4. **Dériver une consigne dédiée** : copier ce dossier en `modeles/<nom>/`,
   renommer en `consigne.md`, ajouter glossaire + patches + réglages, et créer un
   `README.md` (réglages validés + commande). C'est ainsi qu'on a fait Qwen.
5. Reporter le verdict dans [`../COMPARATIF.md`](../COMPARATIF.md) et au CHANGELOG.

> Le contrat JSON que ce gabarit fait produire est décrit dans
> [`../../docs/contrat-sortie.md`](../../docs/contrat-sortie.md).
