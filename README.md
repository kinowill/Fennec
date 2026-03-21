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

## ✨ Fonctionnalités

| Catégorie | Commandes |
|-----------|-----------|
| 📁 Fichiers | `list`, `find`, `read`, `write`, `delete`, `move`, `duplicate`, `rename`, `sort`, `redate` |
| 🌐 Web | `search` (DDG + synthèse IA), `download` |
| 📦 Logiciels | `install`, `uninstall` (+ nettoyage Geek Uninstaller) |
| 🤖 IA | `agent` (mode ReAct autonome), `chat` (conversation libre), `helpchat` (aide intégrée) |
| 🗂️ Divers | `open`, `clip`, `exec`, `bm` (favoris), `logs` |

---

## 🚀 Installation

### Prérequis
- **Windows 10/11**
- **Python 3.10+** — [python.org](https://python.org)
- **Ollama** — [ollama.com](https://ollama.com)

### Lancement

1. Clone le repo :
```bash
git clone https://github.com/kinowill/Fennec.git
cd Fennec
```

2. Double-clique sur `fennec.bat` — il s'occupe de tout :
   - Installe les dépendances Python automatiquement
   - Démarre Ollama si nécessaire
   - Télécharge `qwen2.5:7b` au premier lancement (~4.7 Go)

> 💡 **Optionnel** : pour la désinstallation propre des logiciels, place [Geek Uninstaller](https://geekuninstaller.com) (gratuit, portable) renommé en `geek.exe` dans le dossier Fennec.

---

## 🦊 Utilisation

```
search météo montpellier aujourd'hui
agent trouve les 5 fichiers les plus lourds de mon bureau
install VLC
rename *.JPG *.jpg
helpchat comment déplacer tous mes PDF dans un dossier
chat
```

### Mode agent
L'agent ReAct analyse ta demande, choisit les outils, agit et recommence jusqu'à 8 étapes. Il demande toujours confirmation avant de supprimer ou déplacer.

```
agent liste tous les fichiers .tmp du bureau et supprime-les
```

### Recherche web intelligente
`search` scrape DuckDuckGo et passe les extraits à Qwen pour une réponse directe :

```
search combien de temps cuire un oeuf dur
→ Réponse > Pour un oeuf dur parfait, comptez 10 minutes dans l'eau bouillante...
→ Sources : [1] cuisson-oeufs.com  [2] ...
```

### Renommage en masse
```
rename *.jpg 2024_*        → ajoute un préfixe
rename *.JPG *.jpg         → change l'extension
rename rapport_* note_*    → remplace un mot
```

---

## 📦 Dépendances

```
rich
prompt_toolkit
pdfplumber       # optionnel — lecture PDF
python-docx      # optionnel — lecture DOCX
```

Installées automatiquement par `fennec.bat`.

---

## 🔒 Confidentialité

Fennec est **100% local**. Qwen2.5 tourne sur ta machine via Ollama. Aucune donnée n'est envoyée à un serveur externe, sauf lors des recherches web DuckDuckGo.

---

## ⚙️ Configuration

Les paramètres principaux sont en tête de `fennec.py` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `MODEL` | `qwen2.5:7b` | Modèle Ollama utilisé |
| `OLLAMA_URL` | `http://localhost:11434` | URL du serveur Ollama |

---

## 📄 Licence

MIT — fais-en ce que tu veux.
