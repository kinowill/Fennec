<p align="center">
  <img src="https://raw.githubusercontent.com/kinowill/Fennec/main/FENNEC_LOGO.webp" width="160" />
</p>

<h1 align="center">Fennec</h1>
<p align="center"><b>Shell Windows intelligent propulsé par IA locale</b></p>
<p align="center">Gère tes fichiers, lance des agents autonomes, discute avec Qwen — 100% local, sans cloud, sans clé API.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Ollama-qwen2.5:7b-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/100%25-Local-green?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
  <img src="https://img.shields.io/badge/version-2.0-cyan?style=flat-square" />
</p>

---

## 🚀 Démarrage rapide

**Prérequis :**
- [Python 3.10+](https://python.org/downloads) — coche **"Add Python to PATH"**
- [Ollama](https://ollama.com) — le moteur IA local

```bash
git clone https://github.com/kinowill/Fennec.git
cd Fennec
```

Double-clique sur **`fennec.bat`** — il installe les dépendances, démarre Ollama et télécharge le modèle automatiquement.

> Le premier lancement télécharge `qwen2.5:7b` (~4.7 Go). Les suivants sont instantanés.

---

## ✨ Nouveautés v2

| Fonctionnalité | Description |
|---|---|
| **Mode sudo** | `sudo on` — valide automatiquement toutes les confirmations pour les agents longs |
| **Streaming** | `chat` et `helpchat` affichent les réponses en temps réel, token par token |
| **Steps dynamiques** | L'agent estime lui-même le nombre d'étapes nécessaires via Qwen |
| **Undo** | `delete`, `move`, `rename` sont annulables avec `undo` |
| **Corbeille** | `delete` déplace dans `.fennec_trash/` au lieu de supprimer définitivement |
| **Diff** | `diff fichier1 fichier2` — comparaison colorée ligne à ligne |
| **Alias** | `alias add ll list` — raccourcis de commandes persistants |
| **Settings interactif** | `settings` seul ouvre un menu de configuration |
| **Helpchat interactif** | `helpchat` seul ouvre un bot d'aide en mode conversation |
| **i18n fr/en** | `settings lang en` bascule toute l'interface en anglais |
| **Multi-modèle** | `settings model llama3.2` — change de modèle Ollama à la volée |
| **find --depth** | `find *.pdf . 3` — limite la profondeur de recherche |
| **Config persistante** | `fennec_config.json` — tous les paramètres sauvegardés entre sessions |

---

## 📋 Commandes

### Navigation
| Commande | Description |
|---|---|
| `cd [dossier]` | Changer de dossier |
| `list [dossier]` | Lister les fichiers |
| `find *.ext [dossier] [profondeur]` | Recherche récursive |
| `sort [dossier] [taille\|date]` | Trier par taille ou date |

### Fichiers
| Commande | Description |
|---|---|
| `read [fichier] [n]` | Lire un fichier (n lignes max) |
| `write [fichier] [texte]` | Écrire dans un fichier ⚠️ |
| `delete [fichier]` | Corbeille (récupérable avec `undo`) ⚠️ |
| `rename [dossier] [ancien] [nouveau]` | Renommage en masse avec glob ⚠️ |
| `move [source] [dest]` | Déplacer ⚠️ |
| `duplicate [source]` | Copier |
| `diff [fichier1] [fichier2]` | Comparer deux fichiers |
| `undo` | Annuler la dernière action destructive |

### Système
| Commande | Description |
|---|---|
| `open [chemin]` | Ouvrir avec l'app Windows associée |
| `clip [chemin]` | Copier le chemin dans le presse-papier |
| `exec [commande]` | Exécuter une commande CMD ⚠️ |
| `redate [dossier]` | Renommer par date+numéro ⚠️ |

### Web & Install
| Commande | Description |
|---|---|
| `search [terme]` | Recherche DuckDuckGo + synthèse Qwen |
| `download [url]` | Télécharger un fichier |
| `install [programme]` | Installer via winget ⚠️ |
| `uninstall [programme]` | Désinstaller + nettoyage registre ⚠️ |

### IA
| Commande | Description |
|---|---|
| `agent [instruction]` | Agent autonome (étapes auto-estimées) |
| `chat` | Conversation streaming avec Qwen |
| `helpchat [question]` | Bot d'aide intégré sur Fennec |

### Config & Divers
| Commande | Description |
|---|---|
| `sudo [on\|off]` | Mode auto-validation (plus de o/n) |
| `settings` | Menu de configuration interactif |
| `bm [list\|add\|remove] [nom]` | Favoris de dossiers |
| `alias [list\|add\|remove] [nom] [cmd]` | Alias de commandes |
| `logs [n]` | Derniers logs |
| `help` | Liste toutes les commandes |
| `exit` | Quitter |

> ⚠️ = confirmation requise — utiliser `sudo on` pour passer en mode auto-validation

---

## 💡 Exemples

```
# Agent avec auto-validation (plus besoin de taper o/n a chaque etape)
sudo on
agent trie mes 5 fichiers les plus gros dans mes telechargements
       et place-les dans un dossier "Archives" sur le bureau
sudo off

# Recherche web
search meteo Montpellier

# Renommage en masse
rename . *.JPG *.jpg
rename Photos rapport_* note_*

# Comparer deux fichiers
diff config_old.json config_new.json

# Chat en streaming
chat

# Changer de langue
settings lang en
```

---

## ⚙️ Configuration

`settings` ou édite `fennec_config.json` directement :

```json
{
  "model": "qwen2.5:7b",
  "ollama_url": "http://localhost:11434",
  "lang": "fr",
  "max_steps": 0,
  "aliases": {
    "ll": "list",
    "g": "agent"
  }
}
```

| Paramètre | Description |
|---|---|
| `model` | Modèle Ollama (`qwen2.5:7b`, `llama3.2`, `mistral`…) |
| `ollama_url` | URL du serveur Ollama |
| `lang` | Langue de l'interface (`fr` ou `en`) |
| `max_steps` | Étapes max pour l'agent (`0` = auto via Qwen) |
| `aliases` | Raccourcis de commandes |

---

## 🔧 Structure du projet

```
Fennec/
├── fennec.py          # Application principale
├── launcher.py        # Lanceur GUI (compile en .exe avec PyInstaller)
├── fennec.bat         # Lanceur Windows avec auto-install des dépendances
├── fennec_config.json # Configuration (créé au premier lancement)
├── fennec_logs.txt    # Logs des actions
├── FENNEC_LOGO.webp   # Logo
├── LICENSE
└── README.md
```

**Fichiers créés automatiquement (ignorés par git) :**
- `.fennec_history` — historique des commandes
- `.fennec_bookmarks.json` — favoris
- `.fennec_trash/` — corbeille interne
- `fennec_config.json` — config personnelle
- `fennec_config.bak` — sauvegarde config
- `fennec_logs.txt` — logs

---

## 🔒 Sécurité

- **100% local** — Qwen tourne sur ta machine via Ollama
- **Aucune donnée envoyée**, sauf les recherches web DuckDuckGo
- **Corbeille interne** — `delete` est réversible via `undo`
- **Confirmation systématique** sur toutes les actions destructives
- **Limite de longueur** sur les commandes exec (2048 chars max)
- **Backup automatique** de `fennec_config.json` à chaque modification

> ⚠️ `sudo on` désactive toutes les confirmations. À utiliser pour les agents longs, puis `sudo off` aussitôt après.

---

## 💡 Optionnel

Place [Geek Uninstaller](https://geekuninstaller.com) (gratuit, portable) renommé en `geek.exe` dans le dossier Fennec pour nettoyer le registre après chaque `uninstall`.

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE)
