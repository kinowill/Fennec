"""
fennec_launcher.py
Compilé en fennec.exe avec PyInstaller :
  pip install pyinstaller
  pyinstaller --onefile --noconsole --icon=fennec.ico --name=fennec launcher.py
"""

import sys
import os
import subprocess
import ctypes
from pathlib import Path


def est_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relancer_en_admin():
    """Relance le process en mode admin via UAC."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def trouver_python():
    """Cherche Python dans l'ordre : venv local > PATH > Microsoft Store stub."""
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    venv = base / ".venv" / "Scripts" / "python.exe"
    if venv.exists():
        return str(venv)
    # python dans PATH
    for candidat in ("python", "python3"):
        try:
            r = subprocess.run([candidat, "--version"], capture_output=True)
            if r.returncode == 0 and b"Python 3" in r.stdout + r.stderr:
                return candidat
        except FileNotFoundError:
            continue
    return None


def installer_dependances(py):
    deps = ["rich", "prompt_toolkit", "pdfplumber", "python-docx"]
    for dep in deps:
        subprocess.run([py, "-m", "pip", "install", dep, "--quiet"],
                       capture_output=True)


def verifier_ollama():
    """Retourne True si ollama est installé."""
    r = subprocess.run(["where", "ollama"], capture_output=True)
    return r.returncode == 0


def demarrer_ollama():
    """Démarre ollama serve en arrière-plan si pas déjà actif."""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True  # déjà actif
    except Exception:
        pass
    subprocess.Popen(["ollama", "serve"],
                     creationflags=subprocess.CREATE_NO_WINDOW)
    import time
    for _ in range(8):
        time.sleep(2)
        try:
            urllib.request.urlopen("http://localhost:11434", timeout=2)
            return True
        except Exception:
            continue
    return False


def verifier_modele():
    r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    return "qwen2.5" in r.stdout.lower()


def telecharger_modele():
    subprocess.run(["ollama", "pull", "qwen2.5:7b"])


def message_erreur(titre, texte):
    ctypes.windll.user32.MessageBoxW(0, texte, titre, 0x10)  # MB_ICONERROR


def main():
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    fennec_py = base / "fennec.py"

    # Vérification fichier principal
    if not fennec_py.exists():
        message_erreur("Fennec — Erreur",
                       f"fennec.py introuvable dans :\n{base}\n\n"
                       "Place fennec.exe et fennec.py dans le même dossier.")
        return

    # Python
    py = trouver_python()
    if not py:
        message_erreur("Fennec — Erreur",
                       "Python 3 introuvable.\n\nInstalle-le depuis https://python.org")
        return

    # Dépendances (silencieux)
    installer_dependances(py)

    # Ollama
    if not verifier_ollama():
        message_erreur("Fennec — Erreur",
                       "Ollama n'est pas installé.\n\nTélécharge-le sur https://ollama.com")
        return

    if not demarrer_ollama():
        message_erreur("Fennec — Erreur",
                       "Ollama ne répond pas après 16 secondes.")
        return

    # Modèle
    if not verifier_modele():
        # Téléchargement dans un terminal visible
        subprocess.run(
            f'start "Fennec — Téléchargement modèle" cmd /k "ollama pull qwen2.5:7b && exit"',
            shell=True
        )
        # Attend la fin
        import time
        while not verifier_modele():
            time.sleep(3)

    # Lancement Fennec dans Windows Terminal ou conhost
    try:
        subprocess.run(
            f'wt --title "Fennec 🦊" "{py}" "{fennec_py}"',
            shell=True
        )
    except Exception:
        # Fallback : cmd classique
        subprocess.run(
            f'start "Fennec" cmd /k ""{py}" "{fennec_py}""',
            shell=True
        )


if __name__ == "__main__":
    main()
