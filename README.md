<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Ollama-qwen2.5:7b-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/100%25-Local-green?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
</p>

<h1 align="center">🦊 Fennec</h1>
<p align="center"><b>Shell Windows intelligent propulsé par IA locale (Qwen2.5)</b></p>
<p align="center">Gère tes fichiers, installe des logiciels, cherche sur le web — tout depuis un terminal, sans cloud, sans clé API.</p>

---

## 🚀 Démarrage rapide

### 1 — Installe Python
Télécharge et installe Python 3.10+ depuis [python.org](https://python.org/downloads).

> ⚠️ Coche **"Add Python to PATH"** pendant l'installation.

### 2 — Installe Ollama
Télécharge et installe Ollama depuis [ollama.com](https://ollama.com).

> Ollama fait tourner le modèle IA en local sur ta machine.

### 3 — Télécharge Fennec
```bash
git clone https://github.com/kinowill/Fennec.git
cd Fennec
```
Ou télécharge le ZIP depuis GitHub → **Code → Download ZIP**, puis extrais le dossier.

### 4 — Lance Fennec
Double-clique sur **`fennec.bat`**

C'est tout. Le script s'occupe automatiquement de :
- Installer les dépendances Python (`rich`, `prompt_toolkit`, `pdfplumber`, `python-docx`)
- Démarrer Ollama en arrière-plan si nécessaire
- Télécharger le modèle `qwen2.5:7b` (~4.7 Go) au premier lancement

> ⏱️ Le premier lancement peut prendre plusieurs minutes selon ta connexion (téléchargement du modèle). Les lancements suivants sont instantanés.

---

## 📋 Commandes

| Commande | Description |
|----------|-------------|
| `list [dossier]` | Lister les fichiers |
| `find *.ext [dossier]` | Recherche récursive |
| `read [fichier] [n]` | Lire un fichier (n lignes max) |
| `write [fichier] [texte]` | Écrire dans un fichier |
| `delete [fichier]` | Supprimer un fichier ou dossier ⚠️ |
| `rename [ancien] [nouveau]` | Renommage en masse avec `*` |
| `move [source] [dest]` | Déplacer ⚠️ |
| `duplicate [source]` | Copier |
| `sort [dossier] [taille\|date]` | Trier par taille ou date |
| `redate [dossier]` | Renommer par date de création ⚠️ |
| `open [chemin]` | Ouvrir avec l'application Windows associée |
| `clip [chemin]` | Copier le chemin dans le presse-papier |
| `exec [commande]` | Exécuter une commande CMD ⚠️ |
| `search [terme]` | Recherche web (DuckDuckGo + synthèse IA) |
| `download [url]` | Télécharger un fichier |
| `install [programme]` | Installer via winget ⚠️ |
| `uninstall [programme]` | Désinstaller + nettoyage ⚠️ |
| `bm [list\|add\|remove] [nom]` | Gérer les favoris de dossiers |
| `agent [instruction]` | Agent IA autonome (max 8 étapes) |
| `chat` | Conversation libre avec Qwen |
| `helpchat [question]` | Aide intégrée sur Fennec |
| `logs [n]` | Afficher les derniers logs |
| `help` | Afficher toutes les commandes |
| `exit` | Quitter |

> ⚠️ = confirmation requise avant exécution

---

## 💡 Exemples

```bash
# Recherche web avec réponse IA
search météo montpellier aujourd'hui

# Agent autonome
agent trouve les 5 fichiers les plus lourds de mon bureau
agent supprime tous les fichiers .tmp du dossier courant

# Renommage en masse
rename *.JPG *.jpg              # changer l'extension
rename rapport_* note_*         # remplacer un mot
rename . * 2024_*               # ajouter un préfixe

# Installer / désinstaller
install VLC
uninstall AnyDesk

# Chat avec contexte web automatique
chat
toi > quelle météo à Paris ce soir ?
```

---

## 🔧 Configuration

En tête de `fennec.py` :

```python
MODEL      = "qwen2.5:7b"              # modèle Ollama (ex: llama3, mistral)
OLLAMA_URL = "http://localhost:11434"  # URL du serveur Ollama
```

---

## 💡 Optionnel — Nettoyage après désinstallation

Place [Geek Uninstaller](https://geekuninstaller.com) (gratuit, portable) renommé en `geek.exe` dans le dossier Fennec. La commande `uninstall` l'ouvrira automatiquement après chaque désinstallation pour nettoyer les restes du registre.

---

## 🔒 Confidentialité

Fennec est **100% local**. Qwen2.5 tourne sur ta machine via Ollama. Aucune donnée n'est envoyée à un serveur externe, sauf lors des recherches web DuckDuckGo.

---

## 📄 Licence

MIT — fais-en ce que tu veux.
