<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Ollama-qwen2.5:7b-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
</p>

<h1 align="center">🦊 Fennec</h1>
<p align="center"><b>Shell Windows intelligent propulsé par IA locale (Qwen2.5)</b></p>
<p align="center">Gère tes fichiers, installe des logiciels, cherche sur le web — tout depuis un terminal, sans cloud, sans clé API.</p>

---

## 🚀 Démarrage

**Prérequis :**
- [Python 3.10+](https://python.org/downloads) — coche **"Add Python to PATH"** à l'installation
- [Ollama](https://ollama.com) — le moteur IA local

**Lancement :**
```text
git clone https://github.com/kinowill/Fennec.git
cd Fennec
```
Puis double-clique sur **`fennec.bat`** — il installe les dépendances, démarre Ollama et télécharge le modèle automatiquement.

> ⏱️ Le premier lancement télécharge `qwen2.5:7b` (~4.7 Go). Les suivants sont instantanés.

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
| `search [terme]` | Recherche web DuckDuckGo + synthèse IA |
| `download [url]` | Télécharger un fichier |
| `install [programme]` | Installer via winget ⚠️ |
| `uninstall [programme]` | Désinstaller + nettoyage registre ⚠️ |
| `bm [list\|add\|remove] [nom]` | Favoris de dossiers |
| `agent [instruction]` | Agent IA autonome (max 8 étapes) |
| `chat` | Conversation libre avec Qwen |
| `helpchat [question]` | Aide intégrée sur Fennec |
| `logs [n]` | Derniers logs |
| `help` | Liste toutes les commandes |
| `exit` | Quitter |

> ⚠️ = confirmation requise

---

## 💡 Exemples

```text
# Recherche web avec réponse IA
search météo montpellier aujourd'hui

# Agent autonome
agent trouve les 5 fichiers les plus lourds de mon bureau
agent supprime tous les fichiers .tmp du dossier courant

# Renommage en masse
rename *.JPG *.jpg
rename rapport_* note_*

# Chat avec contexte web automatique
chat
```

---

## 🔧 Configuration

En tête de `fennec.py` :

```python
MODEL      = "qwen2.5:7b"              # modèle Ollama (ex: llama3, mistral)
OLLAMA_URL = "http://localhost:11434"  # URL du serveur Ollama
```

---

## 💡 Optionnel

Place [Geek Uninstaller](https://geekuninstaller.com) (gratuit, portable) renommé en `geek.exe` dans le dossier Fennec pour nettoyer le registre après chaque `uninstall`.

---

## 🔒 Confidentialité

100% local. Qwen2.5 tourne sur ta machine via Ollama. Aucune donnée envoyée à l'extérieur, sauf les recherches web DuckDuckGo.

---

## 📄 Licence

MIT
