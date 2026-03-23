<p align="center">
  <img src="https://raw.githubusercontent.com/kinowill/Fennec/main/FENNEC_LOGO.webp" width="160" />
</p>

<h1 align="center">Fennec</h1>
<p align="center"><b>Shell Windows intelligent propulse par IA locale</b></p>
<p align="center">Gere tes fichiers, lance des agents autonomes, discute avec Qwen — 100% local, sans cloud, sans cle API.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Ollama-qwen2.5:7b-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows" />
  <img src="https://img.shields.io/badge/100%25-Local-green?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
  <img src="https://img.shields.io/badge/version-2.3-cyan?style=flat-square" />
</p>

---

## Demarrage rapide

**Prerequis :**
- [Python 3.10+](https://python.org/downloads) — coche **"Add Python to PATH"**
- [Ollama](https://ollama.com) — le moteur IA local

```bash
git clone https://github.com/kinowill/Fennec.git
cd Fennec
```

Double-clique sur **`fennec.bat`** — il installe les dependances, demarre Ollama et telecharge le modele automatiquement.

> Le premier lancement telecharge `qwen2.5:7b` (~4.7 Go). Les suivants sont instantanes.

---

## Nouveautes v2

| Fonctionnalite | Description |
|---|---|
| **Agent ReAct** | Agent autonome avec estimation dynamique des etapes via Qwen |
| **Mode sudo** | `sudo on` — auto-valide toutes les confirmations, aucune restriction |
| **Streaming** | `chat` et `helpchat` affichent les reponses token par token |
| **Undo persistant** | `delete`, `move`, `rename`, `write` sont annulables avec `undo` (20 derniers) |
| **Corbeille** | `delete` deplace dans `.fennec_trash/` + `emptytrash` pour vider |
| **Diff** | `diff fichier1 fichier2` — comparaison coloree ligne a ligne |
| **Tree** | `tree [dossier] [profondeur]` — arborescence visuelle |
| **Size** | `size [chemin]` — taille recursive d'un fichier ou dossier |
| **Summary** | `summary [fichier]` — resume IA (PDF, DOCX, texte) |
| **Compress/Decompress** | ZIP, TAR, TAR.GZ — compression et extraction |
| **History** | `history [n]` — historique des commandes |
| **Alias** | `alias add ll list` — raccourcis de commandes persistants |
| **Settings interactif** | `settings` seul ouvre un menu de configuration |
| **i18n fr/en** | `settings lang en` bascule toute l'interface en anglais |
| **Multi-modele** | `settings model llama3.2` — change de modele Ollama a la volee |
| **Timeout configurable** | `settings ollama_timeout 180` — timeout Ollama ajustable |
| **find --depth** | `find *.pdf . 3` — limite la profondeur de recherche |
| **Limites d'affichage** | `list` (50), `sort` (30), `find` (200) avec message "... N de plus" |
| **Config persistante** | `fennec_config.json` avec rotation atomique (backup auto) |

---

## Commandes

### Navigation
| Commande | Description |
|---|---|
| `cd [dossier]` | Changer de dossier |
| `list/ls [dossier]` | Lister les fichiers (50 max, `list . all` pour tout) |
| `find *.ext [dossier] [profondeur]` | Recherche recursive |
| `sort [dossier] [taille\|date\|taille_asc\|date_asc] [n]` | Trier par taille ou date (asc/desc) |
| `tree [dossier] [profondeur]` | Arborescence visuelle |

### Fichiers
| Commande | Description |
|---|---|
| `read/cat [fichier] [n]` | Lire un fichier (PDF, DOCX, texte) |
| `write [fichier] [texte]` | Ecrire dans un fichier (backup auto en corbeille) |
| `delete/rm [fichier]` | Corbeille (recuperable avec `undo`) |
| `emptytrash [fennec\|windows]` | Vider la corbeille Fennec ou Windows |
| `rename [dossier] [ancien] [nouveau]` | Renommage en masse avec glob |
| `move/mv [source] [dest]` | Deplacer |
| `duplicate/cp [source] [dest?]` | Copier fichier ou dossier |
| `diff [fichier1] [fichier2]` | Comparer deux fichiers |
| `undo` | Annuler la derniere action destructive |
| `size [chemin]` | Taille fichier ou dossier |
| `compress [source] [dest?]` | Compresser en .zip |
| `decompress [archive] [dest?]` | Extraire archive (ZIP, TAR, GZ) |

> Les commandes marquees ci-dessous demandent confirmation — `sudo on` pour passer en mode auto-validation.

### Systeme
| Commande | Description |
|---|---|
| `open [chemin]` | Ouvrir avec l'app Windows associee |
| `clip [chemin]` | Copier le chemin dans le presse-papier |
| `exec [commande]` | Executer une commande CMD (max 2048 chars) |
| `redate [dossier] [creation\|modif]` | Renommer par date+numero |

### Web & Install
| Commande | Description |
|---|---|
| `search [terme]` | Recherche DuckDuckGo + synthese Qwen |
| `download [url] [dest?]` | Telecharger un fichier |
| `install [programme]` | Installer via winget |
| `uninstall [programme]` | Desinstaller + nettoyage registre |

### IA
| Commande | Description |
|---|---|
| `agent [instruction]` | Agent autonome ReAct (etapes auto-estimees) |
| `chat` | Conversation streaming avec Qwen |
| `helpchat [question]` | Bot d'aide integre sur Fennec |
| `summary [fichier] [long?]` | Resume IA d'un fichier (PDF, DOCX, texte) |

### Config & Divers
| Commande | Description |
|---|---|
| `sudo [on\|off]` | Mode auto-validation (plus de o/n) |
| `settings [cle] [valeur?]` | Menu de configuration interactif |
| `bm [list\|add\|remove] [nom]` | Favoris de dossiers |
| `alias [list\|add\|remove] [nom] [cmd]` | Alias de commandes |
| `history [n]` | Historique des commandes |
| `logs [n]` | Derniers logs |
| `help` | Liste toutes les commandes |
| `exit` | Quitter |

---

## Exemples

```
# Agent avec auto-validation
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

# Arborescence d'un dossier
tree Documents 2

# Taille d'un dossier
size Downloads

# Resume IA d'un PDF
summary rapport.pdf

# Compresser un dossier
compress MonProjet MonProjet.zip

# Chat en streaming
chat

# Changer de langue
settings lang en
```

---

## Configuration

`settings` ou edite `fennec_config.json` directement :

```json
{
  "model": "qwen2.5:7b",
  "ollama_url": "http://localhost:11434",
  "lang": "fr",
  "max_steps": 0,
  "ollama_timeout": 120,
  "aliases": {
    "ll": "list",
    "g": "agent"
  }
}
```

| Parametre | Description |
|---|---|
| `model` | Modele Ollama (`qwen2.5:7b`, `llama3.2`, `mistral`...) |
| `ollama_url` | URL du serveur Ollama |
| `lang` | Langue de l'interface (`fr` ou `en`) |
| `max_steps` | Etapes max pour l'agent (`0` = auto via Qwen) |
| `ollama_timeout` | Timeout Ollama en secondes (defaut : 120) |
| `num_ctx` | Context window Ollama (`0` = auto depuis le modele). Les limites agent sont scalees automatiquement |
| `aliases` | Raccourcis de commandes |

---

## Structure du projet

```
Fennec/
├── fennec.py          # Application principale (~2570 lignes)
├── launcher.py        # Lanceur GUI (compile en .exe avec PyInstaller)
├── fennec.bat         # Lanceur Windows avec auto-install des dependances
├── fennec_config.json # Configuration (cree au premier lancement)
├── fennec_logs.txt    # Logs des actions
├── FENNEC_LOGO.webp   # Logo
├── LICENSE
└── README.md
```

**Fichiers crees automatiquement (ignores par git) :**
- `.fennec_history` — historique des commandes
- `.fennec_bookmarks.json` — favoris
- `.fennec_trash/` — corbeille interne
- `.fennec_undo.json` — pile d'annulation (20 derniers)
- `fennec_config.json` — config personnelle
- `fennec_config.bak` — sauvegarde config (rotation atomique)
- `fennec_logs.txt` — logs

---

## Securite

- **100% local** — Qwen tourne sur ta machine via Ollama
- **Aucune donnee envoyee**, sauf les recherches web DuckDuckGo
- **Corbeille interne** — `delete` est reversible via `undo`
- **Undo persistant** — les 20 dernieres actions destructives sont restaurables
- **Confirmation systematique** sur toutes les actions destructives
- **Limite de longueur** sur les commandes exec (2048 chars max)
- **Backup automatique** de `fennec_config.json` (rotation atomique)
- **Protection path traversal** — resolution securisee des chemins
- **Whitelist agent** — l'agent ne peut utiliser que les outils Fennec approuves
- **Anti-saturation agent** — `find`/`list` avec beaucoup de resultats envoient un resume compact a Qwen (par dossier) au lieu de la liste brute

> `sudo on` desactive toutes les confirmations. A utiliser pour les agents longs, puis `sudo off` aussitot apres.

---

## Optionnel

Place [Geek Uninstaller](https://geekuninstaller.com) (gratuit, portable) renomme en `geek.exe` dans le dossier Fennec pour nettoyer le registre apres chaque `uninstall`.

---

## Licence

MIT — voir [LICENSE](LICENSE)
