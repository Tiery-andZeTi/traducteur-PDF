<#
    lancer_traductions.ps1 — wrapper de lot pour traduire_pdf.py

    Pensé pour être lancé sans surveillance (tâche planifiée, la nuit) :
      1. regarde le dossier "a_traduire"
      2. pour chaque PDF trouvé, lance traduire_pdf.py
      3. si la traduction réussit : déplace le PDF source dans "fait"
         (le PDF bilingue + les JSON atterrissent dans "traduit")
      4. si elle échoue : laisse le PDF dans "a_traduire" pour réessayer
         la nuit suivante, et journalise l'erreur
      5. tout est consigné dans un fichier de log horodaté sous "logs"

    Aucune IA ici : c'est un simple orchestrateur. Le travail de traduction
    reste fait par traduire_pdf.py via le serveur LOCAL LM Studio.

    Réglages : modifie les variables du bloc CONFIG ci-dessous.
#>

# --------------------------------------------------------------------------- #
#  CONFIG — à adapter au besoin
# --------------------------------------------------------------------------- #
$Model = "google/gemma-4-12b-qat"   # id exact du modèle chargé dans LM Studio
$Dpi   = 150                         # résolution d'envoi (voir guide, section 7)
$BaseUrl = "http://localhost:1234/v1"

# Racine du projet = dossier où se trouve CE script (robuste si déplacé).
$Root      = $PSScriptRoot
$Python    = Join-Path $Root ".venv\Scripts\python.exe"
$Script    = Join-Path $Root "traduire_pdf.py"
$DossierIn = Join-Path $Root "a_traduire"
$DossierOut= Join-Path $Root "traduit"
$DossierFait = Join-Path $Root "fait"
$DossierLog  = Join-Path $Root "logs"

# --------------------------------------------------------------------------- #
#  Préparation : créer les dossiers manquants, ouvrir le log
# --------------------------------------------------------------------------- #
foreach ($d in @($DossierIn, $DossierOut, $DossierFait, $DossierLog)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}

$horodatage = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogFile = Join-Path $DossierLog "traduction_$horodatage.log"

function Log($msg) {
    $ligne = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
    Write-Output $ligne
    Add-Content -Path $LogFile -Value $ligne -Encoding utf8
}

Log "=== Demarrage du lot ==="
Log "Racine    : $Root"
Log "Modele    : $Model   DPI : $Dpi"

# Garde-fous : binaires présents ?
if (-not (Test-Path $Python)) { Log "ERREUR : Python du venv introuvable ($Python). Arret."; exit 2 }
if (-not (Test-Path $Script)) { Log "ERREUR : traduire_pdf.py introuvable ($Script). Arret."; exit 2 }

# --------------------------------------------------------------------------- #
#  Verif serveur LM Studio (sinon, run nocturne perdu sans explication)
# --------------------------------------------------------------------------- #
try {
    Invoke-RestMethod -Uri "$BaseUrl/models" -TimeoutSec 15 -ErrorAction Stop | Out-Null
    Log "Serveur LM Studio : joignable."
} catch {
    Log "ERREUR : serveur LM Studio injoignable sur $BaseUrl."
    Log "  -> Demarre le serveur (LM Studio > Developer > Local Server) avec un modele vision charge."
    Log "=== Lot interrompu (aucun PDF traite) ==="
    exit 2
}

# --------------------------------------------------------------------------- #
#  Boucle sur les PDF du dossier d'entree
# --------------------------------------------------------------------------- #
$pdfs = Get-ChildItem -Path $DossierIn -Filter *.pdf -File
if (-not $pdfs) {
    Log "Aucun PDF dans $DossierIn — rien a faire."
    Log "=== Fin du lot ==="
    exit 0
}

Log ("{0} PDF a traiter." -f $pdfs.Count)
$ok = 0; $ko = 0

foreach ($pdf in $pdfs) {
    $nom = $pdf.BaseName
    $src = $pdf.FullName
    $out = Join-Path $DossierOut ("{0}_FINAL.pdf" -f $nom)
    Log "--- Traitement : $($pdf.Name) ---"

    # On se place dans "traduit" pour que les JSON intermediaires y atterrissent.
    # (Python trouve quand meme ses modules : le dossier du script est sur sys.path.)
    Push-Location $DossierOut
    try {
        & $Python $Script $src $out --model $Model --dpi $Dpi --base-url $BaseUrl 2>&1 |
            Tee-Object -FilePath $LogFile -Append
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    if ($code -eq 0) {
        Move-Item -Path $src -Destination (Join-Path $DossierFait $pdf.Name) -Force
        Log "OK : $($pdf.Name) -> traduit\$([System.IO.Path]::GetFileName($out)) ; source deplacee dans fait\"
        $ok++
    } else {
        Log "ECHEC (code $code) : $($pdf.Name) laisse dans a_traduire pour reessai."
        $ko++
    }
}

Log ("=== Fin du lot : {0} reussi(s), {1} echec(s) ===" -f $ok, $ko)
exit 0
