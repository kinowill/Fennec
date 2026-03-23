# Changelog

## [2.2.1] - 2026-03-23

### Fixed
- **Agent : find/list ne sature plus le contexte Qwen** — les resultats sont cappes a 30 en mode agent, et le feedback envoye a Qwen est un resume par dossier (nombre de fichiers par dossier au lieu de la liste brute des chemins)
- Import `Counter` deplace au niveau module (au lieu d'etre importe dans la boucle agent)

## [2.2] - 2026-03-23

### Security
- Agent ne peut plus bypasser la whitelist (plus de fallback exec sur commande inconnue)
- Protection path traversal dans l'agent (rejet des `..` dans les chemins)
- `resoudre()` assigne correctement le resultat de `resolve()`
- Launcher : suppression des `shell=True` inutiles

### Fixed
- Undo : peek-before-pop — ne perd plus l'entree si la restauration echoue
- 5 strings hardcodees converties en i18n `t()` (67/67 cles fr/en)
- `cmd_sort` : un seul `stat()` par fichier au lieu de deux
- Error printing coherent via `err()`

### Added
- Constante `__version__` en haut de `fennec.py`
- Logging dans `_charger_undo` en cas d'erreur
- `.gitignore` : `.fennec_undo.json`, `.env*`
- `requirements.txt`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- Templates GitHub (issues + PR)

## [2.0] - 2026-03-21

### Added
- Agent autonome ReAct avec estimation dynamique des etapes via Qwen
- Mode sudo (`sudo on/off`) — auto-validation de toutes les confirmations
- Streaming token par token pour `chat` et `helpchat`
- Undo persistant (20 dernieres actions) + corbeille interne `.fennec_trash/`
- Commandes : `diff`, `tree`, `size`, `summary`, `compress`, `decompress`, `history`, `emptytrash`
- i18n complet francais/anglais (60+ cles)
- Aliases de commandes persistants
- Menu `settings` interactif
- Multi-modele Ollama (`settings model`)
- `find` avec profondeur configurable
- Config persistante `fennec_config.json` avec rotation atomique
- Timeout Ollama configurable
- Limites d'affichage (`list` 50, `sort` 30, `find` 200)

## [1.0] - 2026-03-20

### Added
- Release initiale
- Navigation : `cd`, `list`, `find`, `sort`
- Fichiers : `read`, `write`, `delete`, `rename`, `move`, `duplicate`
- Systeme : `open`, `clip`, `exec`, `redate`
- IA : `agent`, `chat`, `helpchat`, `search`
- Web : `download`, `install`, `uninstall`
- Config : `bm` (bookmarks), `logs`, `help`
