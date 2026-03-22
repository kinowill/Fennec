"""
Fennec — AI-powered Windows file shell
========================================
Dependencies : pip install rich prompt_toolkit
Ollama required : https://ollama.com  (ollama pull qwen2.5:7b)
"""

import os
import io
import re
import html as _html
import json
import shlex
import shutil
import fnmatch
import difflib
import subprocess
import ctypes
import locale
import urllib.request
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.markup import escape
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    raise SystemExit("Install rich: pip install rich")

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.key_binding import KeyBindings as _KB
except ImportError:
    raise SystemExit("Install prompt_toolkit: pip install prompt_toolkit")

# ── Encoding ──────────────────────────────────────────────────────────────────
_enc = locale.getpreferredencoding(False) or "utf-8"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
LOG_FILE       = BASE_DIR / "fennec_logs.txt"
HIST_FILE      = BASE_DIR / ".fennec_history"
BOOKMARKS_FILE = BASE_DIR / ".fennec_bookmarks.json"
CONFIG_FILE    = BASE_DIR / "fennec_config.json"
TRASH_DIR      = BASE_DIR / ".fennec_trash"
GEEK_EXE       = BASE_DIR / "geek.exe"

# ── Config ────────────────────────────────────────────────────────────────────
_DEFAULT_CONFIG = {
    "model":      "qwen2.5:7b",
    "ollama_url": "http://localhost:11434",
    "lang":       "fr",
    "max_steps":  0,
    "aliases":    {},
}

def charger_config():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            cfg = dict(_DEFAULT_CONFIG)
            cfg.update(data)
            return cfg
        except Exception:
            pass
    return dict(_DEFAULT_CONFIG)

def sauver_config(cfg):
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    # Keep one backup before replacing
    if CONFIG_FILE.exists():
        CONFIG_FILE.replace(CONFIG_FILE.with_suffix(".bak"))
    tmp.replace(CONFIG_FILE)

_cfg      = charger_config()
MODEL     = _cfg["model"]
OLLAMA_URL= _cfg["ollama_url"]
LANG      = _cfg["lang"]
_aliases  = dict(_cfg.get("aliases", {}))

# ── i18n ──────────────────────────────────────────────────────────────────────
_STRINGS = {
    "fr": {
        "confirm_prompt":     "Confirmer ? (o/n) :",
        "confirm_yes":        ("o","y","oui","yes"),
        "ollama_down":        "Ollama ne repond pas. Lance : ollama serve",
        "no_reply":           "Pas de reponse de Qwen.",
        "cancelled":          "Annule.",
        "error":              "Erreur : ",
        "not_found":          "Introuvable : ",
        "ok":                 "OK",
        "chat_header":        "-- Chat Qwen  (exit pour quitter) --",
        "chat_back":          "Retour a Fennec.",
        "chat_you":           "toi >",
        "agent_label":        "Agent : ",
        "agent_thinking":     "Qwen reflechit... (etape {s}/{m})",
        "agent_estimating":   "Estimation complexite...",
        "agent_no_cmd":       "Qwen n'a pas specifie de commande.",
        "agent_refused":      "Action refusee par l'utilisateur. Propose autre chose.",
        "agent_limit":        "Limite de {n} etapes atteinte.",
        "agent_extended":     "Extension -> {n} etapes max",
        "agent_complexity":   "Complexite estimee -> {n} etapes max",
        "agent_no_tool_first":"NON. Tu ne peux pas repondre sans avoir utilise au moins un outil. "
                              "Utilise d'abord list, find, sort ou exec. Reponds avec {\"action\":\"tool\",...}.",
        "undo_empty":         "Rien a annuler.",
        "undo_ok":            "Annule : {name}",
        "deleted_to_trash":   "Deplace en corbeille : {name}",
        "settings_saved":     "Parametres sauvegardes.",
        "settings_header":    "-- Parametres Fennec --",
        "alias_added":        "Alias ajoute : {k} -> {v}",
        "alias_removed":      "Alias supprime : {k}",
        "alias_list":         "-- Alias --",
        "alias_none":         "Aucun alias.",
        "diff_same":          "Fichiers identiques.",
        "diff_header":        "-- diff {a} vs {b} --",
        "web_injected":       "(donnees web injectees)",
        "web_none":           "(pas de resultat web, Qwen repond de memoire)",
        "cmd_detected":       "-> commande Fennec detectee, execution directe",
        "install_tip":        "Astuce : essaie avec l'ID exact (ex: install VideoLAN.VLC)",
        "search_label":       "Recherche : ",
        "no_result":          "Aucun resultat.",
        "opening_browser":    "Ouverture navigateur...",
        "goodbye":            "Au revoir.",
        "ctrl_c":             "Ctrl+C -- tape exit pour quitter.",
    },
    "en": {
        "confirm_prompt":     "Confirm? (y/n):",
        "confirm_yes":        ("y","yes","o","oui"),
        "ollama_down":        "Ollama not responding. Run: ollama serve",
        "no_reply":           "No reply from Qwen.",
        "cancelled":          "Cancelled.",
        "error":              "Error: ",
        "not_found":          "Not found: ",
        "ok":                 "OK",
        "chat_header":        "-- Chat Qwen  (exit to quit) --",
        "chat_back":          "Back to Fennec.",
        "chat_you":           "you >",
        "agent_label":        "Agent: ",
        "agent_thinking":     "Qwen thinking... (step {s}/{m})",
        "agent_estimating":   "Estimating complexity...",
        "agent_no_cmd":       "Qwen did not specify a command.",
        "agent_refused":      "Action refused by user. Suggest something else.",
        "agent_limit":        "Step limit of {n} reached.",
        "agent_extended":     "Extended -> {n} max steps",
        "agent_complexity":   "Estimated complexity -> {n} max steps",
        "agent_no_tool_first":"NO. You cannot answer without using at least one tool. "
                              "Use list, find, sort or exec first. Reply with {\"action\":\"tool\",...}.",
        "undo_empty":         "Nothing to undo.",
        "undo_ok":            "Undone: {name}",
        "deleted_to_trash":   "Moved to trash: {name}",
        "settings_saved":     "Settings saved.",
        "settings_header":    "-- Fennec Settings --",
        "alias_added":        "Alias added: {k} -> {v}",
        "alias_removed":      "Alias removed: {k}",
        "alias_list":         "-- Aliases --",
        "alias_none":         "No aliases.",
        "diff_same":          "Files are identical.",
        "diff_header":        "-- diff {a} vs {b} --",
        "web_injected":       "(web data injected)",
        "web_none":           "(no web result, Qwen answers from memory)",
        "cmd_detected":       "-> Fennec command detected, executing directly",
        "install_tip":        "Tip: try the exact ID (e.g. install VideoLAN.VLC)",
        "search_label":       "Search: ",
        "no_result":          "No results.",
        "opening_browser":    "Opening browser...",
        "goodbye":            "Goodbye.",
        "ctrl_c":             "Ctrl+C -- type exit to quit.",
    },
}

def t(key, **kw):
    s = _STRINGS.get(LANG, _STRINGS["fr"]).get(key, _STRINGS["fr"].get(key, key))
    return s.format(**kw) if kw else s

# ── Agent whitelist ───────────────────────────────────────────────────────────
AGENT_CMDS_VALIDES = {"list","ls","find","sort","read","open","cd","exec",
                      "delete","move","duplicate","clip","rename","write"}

# ── State ─────────────────────────────────────────────────────────────────────
console     = Console(highlight=False)
cwd         = Path.cwd()
_bm_cache   = None
_session    = None
_undo_stack = []
_agent_mode    = False   # when True, confirmer() auto-approves (agent already confirmed)
_auto_confirm  = False   # sudo mode: auto-approve ALL confirmations including agent-level

def log(action, details=""):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}]  {action}  |  {details}\n")

def pr(txt):
    console.print(txt)

def confirmer(msg):
    if _agent_mode or _auto_confirm:
        return True
    console.print(f"[yellow]  {escape(msg)}[/yellow]")
    console.print(f"[yellow]  {t('confirm_prompt')}[/yellow] ", end="")
    try:
        rep = input().strip().lower()
    except (KeyboardInterrupt, EOFError):
        return False
    return rep in t("confirm_yes")

def resoudre(chemin):
    bm = charger_bookmarks()
    if chemin in bm:
        return Path(bm[chemin])
    p = Path(chemin)
    resolved = p if p.is_absolute() else cwd / p
    # Block path traversal attempts (../../ etc) outside of absolute paths
    try:
        resolved.resolve()  # raises on bad paths on some OS
    except Exception:
        pass
    return resolved

# ── Bookmarks ─────────────────────────────────────────────────────────────────
def charger_bookmarks():
    global _bm_cache
    if _bm_cache is not None:
        return _bm_cache
    if BOOKMARKS_FILE.exists():
        try:
            _bm_cache = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
            return _bm_cache
        except Exception:
            pass
    _bm_cache = {}
    return _bm_cache

def sauver_bookmarks(bm):
    global _bm_cache
    _bm_cache = bm
    tmp = BOOKMARKS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(bm, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(BOOKMARKS_FILE)

def fmt_taille(n):
    for u in ("o","Ko","Mo","Go"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}To"

# ── Ollama ────────────────────────────────────────────────────────────────────
def ollama_vivant():
    try:
        urllib.request.urlopen(OLLAMA_URL, timeout=3)
        return True
    except Exception:
        return False

def verifier_ollama():
    if not ollama_vivant():
        pr(f"[red]{t('ollama_down')}[/red]")
        return False
    return True

def appel_chat(messages, fmt_json=False):
    """Blocking call. Returns full response. Used for agent (JSON mode) and short queries."""
    payload = json.dumps({
        "model":    MODEL,
        "messages": messages,
        "stream":   False,
        **({"format": "json"} if fmt_json else {})
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "").strip()
    except Exception as e:
        log("ollama_error", str(e))
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)
        return ""

def appel_chat_stream(messages):
    """Streaming call — prints tokens as they arrive. Returns full text.
    NOTE: incompatible with fmt_json=True. Use only for chat/helpchat."""
    payload = json.dumps({
        "model":    MODEL,
        "messages": messages,
        "stream":   True,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    full = []
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                except Exception:
                    continue
                token = chunk.get("message", {}).get("content", "")
                if token:
                    print(token, end="", flush=True)
                    full.append(token)
                if chunk.get("done"):
                    break
        print()
    except Exception as e:
        log("ollama_stream_error", str(e))
        console.print(f"\n[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)
    return "".join(full)

# ── Navigation ────────────────────────────────────────────────────────────────
def cmd_cd(dest=""):
    global cwd
    if not dest:
        pr(str(cwd))
        return
    np = resoudre(dest)
    if not np.exists() or not np.is_dir():
        console.print(f"[red]{t('not_found')}{escape(str(np))}[/red]")
        return
    cwd = np.resolve()
    pr(f"[green]> {cwd}[/green]")
    log("cd", str(cwd))

def cmd_list(dossier=""):
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists():
        console.print(f"[red]{t('not_found')}{escape(str(dp))}[/red]")
        return
    console.print(f"[cyan]{escape(str(dp.resolve()))}[/cyan]")
    entries = sorted(dp.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    for e in entries:
        try:
            if e.is_dir():
                console.print(f"  [blue]/[/blue]{escape(e.name)}")
            else:
                sz  = fmt_taille(e.stat().st_size)
                mod = datetime.fromtimestamp(e.stat().st_mtime).strftime("%d/%m/%y")
                console.print(f"  {e.name}  {sz}  {mod}", markup=False)
        except PermissionError:
            console.print(f"  {e.name}  (access denied)", markup=False)
    log("list", str(dp))

def cmd_find(motif, dossier="", depth=""):
    """Recursive search with optional max depth. Uses os.walk + fnmatch."""
    racine = resoudre(dossier) if dossier else cwd
    if not racine.exists():
        console.print(f"[red]{t('not_found')}{escape(str(racine))}[/red]")
        return
    try:
        max_depth = int(depth) if depth else None
    except ValueError:
        max_depth = None

    LIMITE = 500
    resultats = []
    spin_txt = "[cyan]Searching..." if LANG == "en" else "[cyan]Recherche..."
    with Progress(SpinnerColumn(), TextColumn(spin_txt), transient=True) as prog:
        prog.add_task("")
        for root, dirs, files in os.walk(racine):
            cur_depth = len(Path(root).relative_to(racine).parts)
            if max_depth is not None and cur_depth >= max_depth:
                dirs.clear()
            for name in files:
                if fnmatch.fnmatch(name, motif):
                    resultats.append(Path(root) / name)
            for name in dirs:
                if fnmatch.fnmatch(name, motif):
                    resultats.append(Path(root) / name)
    resultats.sort()
    if not resultats:
        pr(f"[yellow]{t('no_result')} {motif}[/yellow]")
        return
    lbl = "result(s)" if LANG == "en" else "resultat(s)"
    pr(f"[cyan]{len(resultats)} {lbl} - {motif}[/cyan]")
    for r in resultats[:LIMITE]:
        try:
            console.print(f"  {r}  {fmt_taille(r.stat().st_size)}", markup=False)
        except Exception:
            console.print(f"  {r}", markup=False)
    if len(resultats) > LIMITE:
        pr(f"[dim]... {len(resultats)-LIMITE} more[/dim]")
    log("find", f"{motif} in {racine}")

# ── File readers ──────────────────────────────────────────────────────────────
def _lire_pdf(fp):
    try:
        import pdfplumber
        with pdfplumber.open(str(fp)) as pdf:
            texte = "\n".join(p.extract_text() or "" for p in pdf.pages)
        return texte.strip() or "(PDF without extractable text)"
    except ImportError:
        return "(pip install pdfplumber to read PDFs)"
    except Exception as e:
        return f"(PDF error: {e})"

def _lire_docx(fp):
    try:
        from docx import Document
        doc = Document(str(fp))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return "(pip install python-docx to read DOCX)"
    except Exception as e:
        return f"(DOCX error: {e})"

def cmd_read(chemin, limite=100):
    fp = resoudre(chemin)
    if not fp.exists():
        console.print(f"[red]{t('not_found')}{escape(str(fp))}[/red]")
        return
    ext = fp.suffix.lower()
    console.print(f"[cyan]-- {escape(fp.name)} --[/cyan]")
    try:
        if ext == ".pdf":
            texte = _lire_pdf(fp)
        elif ext == ".docx":
            texte = _lire_docx(fp)
        elif ext in (".csv",".json",".md",".html",".htm",".xml",
                     ".txt",".log",".bat",".py",".js",".ts",".css"):
            texte = fp.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                texte = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                texte = f"(Unsupported format: {ext})"
        lignes = texte.splitlines()
        if len(lignes) > limite:
            for l in lignes[:limite]:
                console.print(f"  {l}", markup=False)
            pr(f"[dim]... ({len(lignes)-limite} more lines -- read [file] [n])[/dim]")
        else:
            for l in lignes:
                console.print(f"  {l}", markup=False)
        pr("[cyan]-- end --[/cyan]")
        log("read", str(fp))
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

def cmd_write(chemin, contenu=None):
    fp = resoudre(chemin)
    if contenu is None:
        pr("[dim]Enter content (empty line to finish):[/dim]")
        lignes = []
        try:
            while True:
                ligne = input()
                if ligne == "":
                    break
                lignes.append(ligne)
        except (KeyboardInterrupt, EOFError):
            pr(f"[dim]{t('cancelled')}[/dim]")
            return
        contenu = "\n".join(lignes)
    if not confirmer(f"Overwrite/create {fp}"):
        return
    try:
        fp.write_text(contenu, encoding="utf-8")
        console.print(f"[green]{t('ok')} {escape(str(fp))}[/green]")
        log("write", str(fp))
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

# ── Undo ──────────────────────────────────────────────────────────────────────
def _undo_push(action, original, backup=None):
    _undo_stack.append((action, str(original), str(backup) if backup else None))
    if len(_undo_stack) > 20:
        _undo_stack.pop(0)

def cmd_sudo(args):
    """Toggle or set auto-confirm mode."""
    global _auto_confirm
    sub = args[0].lower() if args else ""
    if sub == "on":
        _auto_confirm = True
    elif sub == "off":
        _auto_confirm = False
    else:
        _auto_confirm = not _auto_confirm

    if _auto_confirm:
        pr("[bold yellow]  ⚡ SUDO ON[/bold yellow][dim]  — actions auto-validees. [yellow]sudo off[/yellow] pour desactiver.[/dim]")
    else:
        pr("[green]  ✓ Sudo off[/green][dim]  — confirmations normales.[/dim]")
    log("sudo", f"auto_confirm={_auto_confirm}")


def cmd_undo():
    if not _undo_stack:
        pr(f"[yellow]{t('undo_empty')}[/yellow]")
        return
    action, original, backup = _undo_stack.pop()
    try:
        if action == "delete" and backup:
            shutil.move(backup, original)
            pr(f"[green]{t('undo_ok', name=Path(original).name)}[/green]")
            log("undo_delete", original)
        elif action == "move" and backup:
            shutil.move(original, backup)
            pr(f"[green]{t('undo_ok', name=Path(original).name)}[/green]")
            log("undo_move", f"{original} -> {backup}")
        elif action == "rename" and backup:
            Path(original).rename(backup)
            pr(f"[green]{t('undo_ok', name=Path(backup).name)}[/green]")
            log("undo_rename", f"{original} -> {backup}")
        else:
            pr(f"[yellow]Cannot undo action: {action}[/yellow]")
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

# ── Destructive ops ───────────────────────────────────────────────────────────
def cmd_delete(chemin):
    fp = resoudre(chemin)
    if not fp.exists():
        console.print(f"[red]{t('not_found')}{escape(str(fp))}[/red]")
        return
    lbl   = "folder" if fp.is_dir() else "file"
    extra = " and all its contents" if fp.is_dir() else ""
    if not confirmer(f"Delete {lbl} {fp.name}{extra}"):
        return
    try:
        TRASH_DIR.mkdir(exist_ok=True)
        trash_path = TRASH_DIR / fp.name
        if trash_path.exists():
            stamp = datetime.now().strftime("%H%M%S")
            trash_path = TRASH_DIR / f"{fp.stem}_{stamp}{fp.suffix}"
        shutil.move(str(fp), str(trash_path))
        _undo_push("delete", fp, trash_path)
        console.print(f"[green]{t('deleted_to_trash', name=escape(fp.name))}[/green]")
        pr("[dim]  (undo to restore)[/dim]")
        log("delete", str(fp))
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

# ── Fixed glob rename ─────────────────────────────────────────────────────────
def _glob_to_regex(motif):
    """Convert glob (*, ?) to regex with indexed named groups."""
    parts = []
    idx   = 0
    for ch in motif:
        if ch == "*":
            parts.append(f"(?P<g{idx}>.*)")
            idx += 1
        elif ch == "?":
            parts.append(f"(?P<g{idx}>.)")
            idx += 1
        else:
            parts.append(re.escape(ch))
    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE), idx

def _appliquer_motif(nom, pattern_src, pattern_dst, n_groups):
    """Apply destination pattern using indexed group substitution (fixes * and ? order)."""
    m = pattern_src.match(nom)
    if not m:
        return None
    result = pattern_dst
    for i in range(n_groups):
        grp = m.group(f"g{i}")
        result = re.sub(r'[*?]', lambda _: grp, result, count=1)
    return result

def cmd_rename(dossier, ancien, nouveau):
    d = resoudre(dossier)
    if not d.exists() or not d.is_dir():
        pr(f"[red]Folder not found: {d}[/red]")
        return
    if not confirmer(f"Rename '{ancien}' -> '{nouveau}' in {d.name}"):
        return
    pattern_src, n_groups = _glob_to_regex(ancien)
    cibles = [e for e in d.iterdir() if pattern_src.match(e.name)]
    if not cibles:
        pr("[yellow]No matching files.[/yellow]")
        return
    for c in cibles:
        nouveau_nom = _appliquer_motif(c.name, pattern_src, nouveau, n_groups)
        if not nouveau_nom:
            continue
        dest     = c.parent / nouveau_nom
        old_name = c.name
        c.rename(dest)
        _undo_push("rename", dest, c)
        console.print(f"[green]{escape(old_name)} -> {escape(nouveau_nom)}[/green]")
        log("rename", f"{c} -> {dest}")

def cmd_move(source, dest):
    src, dst = resoudre(source), resoudre(dest)
    if not src.exists():
        console.print(f"[red]{t('not_found')}{escape(str(src))}[/red]")
        return
    # Auto-create parent dirs if needed
    # If dest looks like a file path (has suffix), ensure its parent exists
    # If dest looks like a folder (no suffix), create it
    dest_is_file = bool(dst.suffix)
    dir_to_create = dst.parent if dest_is_file else dst
    if not dir_to_create.exists():
        try:
            dir_to_create.mkdir(parents=True, exist_ok=True)
            console.print(f"[dim]  Dossier créé : {escape(str(dir_to_create))}[/dim]")
        except Exception as e:
            console.print(f"[red]{t('error')}[/red]", end="")
            console.print(str(e), markup=False)
            return
    original_dst = dst / src.name if dst.is_dir() else dst
    if not confirmer(f"Move {src.name} to {dst}"):
        return
    try:
        shutil.move(str(src), str(dst))
        _undo_push("move", original_dst, src)
        console.print(f"[green]{escape(src.name)} -> {escape(str(dst))}[/green]")
        log("move", f"{src} -> {dst}")
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

def cmd_duplicate(source, dest=""):
    src = resoudre(source)
    if not src.exists():
        console.print(f"[red]{t('not_found')}{escape(str(src))}[/red]")
        return
    dst = resoudre(dest) if dest else src.parent / f"{src.stem}_copy{src.suffix}"
    try:
        shutil.copy2(str(src), str(dst))
        console.print(f"[green]Copy -> {escape(str(dst))}[/green]")
        log("duplicate", f"{src} -> {dst}")
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

def cmd_sort(dossier="", critere="taille", n="0"):
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists():
        console.print(f"[red]{t('not_found')}{escape(str(dp))}[/red]")
        return
    try:
        limit = int(n)
    except (ValueError, TypeError):
        limit = 0
    fichiers = [(str(e), e.stat().st_size, e.stat().st_mtime)
                for e in dp.iterdir() if e.is_file()]
    fichiers.sort(key=lambda x: x[2 if critere in ("date","mtime") else 1], reverse=True)
    affichage = fichiers[:limit] if limit else fichiers
    titre = f"top {limit} " if limit else ""
    console.print(f"[cyan]{escape(str(dp))} -- {titre}sort by {escape(critere)}[/cyan]")
    for chemin, taille, mtime in affichage:
        mod = datetime.fromtimestamp(mtime).strftime("%d/%m/%y")
        console.print(f"  {Path(chemin).name}  {fmt_taille(taille)}  {mod}", markup=False)
    log("sort", f"{dp} by {critere} n={limit}")

def cmd_open(chemin=""):
    fp = resoudre(chemin) if chemin else cwd
    if not fp.exists():
        console.print(f"[red]{t('not_found')}{escape(str(fp))}[/red]")
        return
    try:
        os.startfile(str(fp))
        console.print(f"[green]Opened: {escape(fp.name)}[/green]")
        log("open", str(fp))
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

def cmd_clip(chemin=""):
    fp = resoudre(chemin) if chemin else cwd
    chemin_abs = str(fp.resolve())
    try:
        subprocess.run("clip", input=chemin_abs, text=True, encoding="utf-8",
                       check=True, shell=False)
        console.print(f"[green]Copied: {escape(chemin_abs)}[/green]")
        log("clip", chemin_abs)
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)

_EXEC_MAX_LEN = 2048  # max command length

def cmd_exec(commande):
    # Strip null bytes and limit length
    commande = commande.replace('\x00', '').strip()
    if len(commande) > _EXEC_MAX_LEN:
        pr(f"[red]Command too long (max {_EXEC_MAX_LEN} chars).[/red]")
        return
    if not commande:
        return
    if not confirmer(f"Execute: {commande}"):
        return
    with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), transient=True) as prog:
        prog.add_task("Running...")
        result = subprocess.run(commande, shell=True, capture_output=True, cwd=str(cwd))
    def _decode(b):
        for enc in ("utf-8", _enc, "cp1252", "cp850"):
            try:
                return b.decode(enc)
            except UnicodeDecodeError:
                continue
        return b.decode("utf-8", errors="replace")
    stdout = _decode(result.stdout).strip() if result.stdout else ""
    stderr = _decode(result.stderr).strip() if result.stderr else ""
    if stdout:
        console.print(stdout, markup=False)
    if stderr:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(stderr, markup=False)
    log("exec", commande[:200])

def cmd_diff(f1, f2):
    """Unified diff between two text files with color."""
    p1, p2 = resoudre(f1), resoudre(f2)
    for p in (p1, p2):
        if not p.exists():
            console.print(f"[red]{t('not_found')}{escape(str(p))}[/red]")
            return
    try:
        a = p1.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        b = p2.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except Exception as e:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(str(e), markup=False)
        return
    diff = list(difflib.unified_diff(a, b, fromfile=p1.name, tofile=p2.name))
    if not diff:
        pr(f"[green]{t('diff_same')}[/green]")
        return
    pr(f"[cyan]{t('diff_header', a=p1.name, b=p2.name)}[/cyan]")
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{escape(line)}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{escape(line)}[/red]")
        else:
            console.print(f"[dim]{escape(line)}[/dim]")
    log("diff", f"{p1} vs {p2}")

def cmd_bookmark(action="list", nom="", chemin=""):
    bm = charger_bookmarks()
    if action == "list":
        if not bm:
            pr("[dim]No bookmarks.[/dim]")
            return
        for k, v in bm.items():
            console.print(f"  [cyan]{escape(k)}[/cyan]  {escape(v)}")
    elif action == "add":
        if not nom:
            pr("[red]Usage: bm add [name] [path?][/red]")
            return
        cible = resoudre(chemin) if chemin else cwd
        bm[nom] = str(cible.resolve())
        sauver_bookmarks(bm)
        console.print(f"[green]'{escape(nom)}' -> {escape(str(cible.resolve()))}[/green]")
        log("bm_add", f"{nom}={cible}")
    elif action == "remove":
        if nom not in bm:
            console.print(f"[red]Unknown: {escape(nom)}[/red]")
            return
        del bm[nom]
        sauver_bookmarks(bm)
        console.print(f"[green]Removed: {escape(nom)}[/green]")
        log("bm_remove", nom)
    else:
        pr("[red]Usage: bm [list|add|remove] [name][/red]")

# ── Settings ──────────────────────────────────────────────────────────────────
def cmd_settings(args):
    global MODEL, OLLAMA_URL, LANG, _aliases, _cfg
    cfg = charger_config()

    def _afficher():
        cfg2 = charger_config()
        sudo_status = "[bold yellow]ON ⚡[/bold yellow]" if _auto_confirm else "[dim]off[/dim]"
        pr("[bold cyan]── Paramètres Fennec ──────────────────────────────[/bold cyan]")
        console.print(f"  [cyan]lang[/cyan]        [bold]{cfg2['lang']}[/bold]   [dim](fr / en)[/dim]")
        console.print(f"  [cyan]model[/cyan]       [bold]{cfg2['model']}[/bold]")
        console.print(f"  [cyan]ollama_url[/cyan]  [dim]{cfg2['ollama_url']}[/dim]")
        steps_disp = "[green]auto[/green]" if cfg2['max_steps'] == 0 else f"[yellow]{cfg2['max_steps']}[/yellow]"
        console.print(f"  [cyan]max_steps[/cyan]   {steps_disp}   [dim](0 = auto via Qwen)[/dim]")
        console.print(f"  [cyan]aliases[/cyan]     [bold]{len(cfg2.get('aliases', {}))}[/bold] définis")
        console.print(f"  [cyan]sudo[/cyan]        {sudo_status}")
        pr("[dim]  ↳ tape [bold]lang en[/bold] · [bold]model nom[/bold] · [bold]max_steps 0[/bold] · [bold]exit[/bold][/dim]")

    if not args:
        # Interactive settings mode
        _afficher()
        while True:
            try:
                console.print("[cyan]settings >[/cyan] ", end="")
                saisie = input().strip()
            except (KeyboardInterrupt, EOFError):
                pr(f"\n[dim]{t('chat_back')}[/dim]")
                return
            if not saisie or saisie.lower() in ("exit", "quit", "q"):
                pr(f"[dim]{t('chat_back')}[/dim]")
                return
            try:
                sub_args = shlex.split(saisie)
            except ValueError:
                sub_args = saisie.split()
            cmd_settings(sub_args)
            _afficher()
        return

    key = args[0].lower()
    val = args[1] if len(args) > 1 else ""

    if key == "lang":
        if val not in ("fr","en"):
            pr("[red]Lang must be: fr or en[/red]")
            return
        cfg["lang"] = val
        LANG = val
    elif key == "model":
        if not val:
            r = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
            console.print(r.stdout, markup=False)
            return
        cfg["model"] = val
        MODEL = val
    elif key == "ollama_url":
        cfg["ollama_url"] = val
        OLLAMA_URL = val
    elif key == "max_steps":
        try:
            cfg["max_steps"] = max(0, int(val))
        except ValueError:
            pr("[red]max_steps must be an integer (0 = auto)[/red]")
            return
    else:
        pr(f"[red]Unknown setting: {key}[/red]")
        pr("[dim]Available: lang, model, ollama_url, max_steps[/dim]")
        return

    sauver_config(cfg)
    _cfg = cfg
    pr(f"[green]{t('settings_saved')}[/green]")
    log("settings", f"{key}={val}")

# ── Alias ─────────────────────────────────────────────────────────────────────
def cmd_alias(args):
    global _aliases
    cfg = charger_config()
    als = cfg.get("aliases", {})

    if not args or args[0] == "list":
        if not als:
            pr(f"[dim]{t('alias_none')}[/dim]")
            return
        pr(f"[cyan]{t('alias_list')}[/cyan]")
        for k, v in als.items():
            console.print(f"  [bold]{escape(k)}[/bold]  ->  {escape(v)}")
        return

    if args[0] == "add" and len(args) >= 3:
        k, v = args[1], " ".join(args[2:])
        als[k] = v
        cfg["aliases"] = als
        sauver_config(cfg)
        _aliases = als
        pr(f"[green]{t('alias_added', k=k, v=v)}[/green]")
        log("alias_add", f"{k}={v}")
    elif args[0] == "remove" and len(args) >= 2:
        k = args[1]
        if k not in als:
            pr(f"[red]Unknown alias: {k}[/red]")
            return
        del als[k]
        cfg["aliases"] = als
        sauver_config(cfg)
        _aliases = als
        pr(f"[green]{t('alias_removed', k=k)}[/green]")
        log("alias_remove", k)
    else:
        pr("[red]Usage: alias list | alias add [name] [cmd] | alias remove [name][/red]")

# ── Agent tool executor ───────────────────────────────────────────────────────
def _resoudre_args_agent(cmd, args):
    """Resolve relative paths to absolute for agent tool calls.
    If Qwen passes just a filename, look it up in Downloads and Desktop first.
    Also fixes hallucinated sub-paths like Desktop\\bureau\\X -> Desktop\\X."""
    FILE_CMDS = {"move", "delete", "read", "open", "clip", "duplicate", "rename"}
    if cmd not in FILE_CMDS or not args:
        return args
    home = Path.home()
    desktop = home / "Desktop"
    search_dirs = [cwd, home / "Downloads", desktop, home / "Documents"]

    def _sanitize(arg, is_dest=False):
        p = Path(arg)
        # Strip hallucinated \bureau\ segment that Qwen sometimes adds
        parts = p.parts
        new_parts = []
        skip_next = False
        for i, part in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
            # If previous part is Desktop and current is "bureau", skip "bureau"
            if new_parts and Path(new_parts[-1]).name.lower() == "desktop" and part.lower() == "bureau":
                skip_next = False
                continue
            new_parts.append(part)
        if new_parts != list(parts):
            p = Path(*new_parts) if len(new_parts) > 1 else Path(new_parts[0])

        if p.is_absolute():
            return str(p)
        if is_dest:
            return str(p)
        # Relative — search for it
        for d in search_dirs:
            candidate = d / p.name
            if candidate.exists():
                return str(candidate)
        return str(p)

    resolved = []
    for i, arg in enumerate(args):
        is_dest = (cmd == "move" and i == len(args) - 1)
        resolved.append(_sanitize(arg, is_dest=is_dest))
    return resolved


def _executer_outil(cmd, args):
    """Execute a Fennec tool and capture its output for the agent.
    Uses a local Console buffer. The global swap is safe in this single-threaded
    synchronous application — the finally block guarantees restoration."""
    global console  # declared first — required by Python before any use

    global _agent_mode
    # Auto-resolve relative paths Qwen might pass
    args = _resoudre_args_agent(cmd, args)

    if cmd == "exec":
        commande = " ".join(args).replace('\x00', '').strip()
        if len(commande) > _EXEC_MAX_LEN:
            return "(command too long, refused)"
        result = subprocess.run(commande, shell=True, capture_output=True,
                                text=True, encoding=_enc, errors="replace", cwd=str(cwd))
        out = (result.stdout + result.stderr).strip()
        if out:
            console.print(out[:500], markup=False)
        log("agent_exec", commande[:200])
        return out[:1000] if out else "(no output)"

    buf = io.StringIO()
    cap = Console(file=buf, highlight=False, width=120, markup=False)

    _prev       = console
    console     = cap
    _agent_mode = True
    try:
        dispatcher(cmd, args)
    finally:
        console     = _prev
        _agent_mode = False

    sortie = buf.getvalue().strip()
    if sortie:
        for ligne in sortie.splitlines()[:30]:
            _prev.print(f"  {ligne}", markup=False)
    log("agent_tool", f"{cmd} {args}")
    return sortie[:1500] if sortie else "(command executed)"

# ── Dynamic step estimation ───────────────────────────────────────────────────
_MAX_STEPS_ABSOLU = 20

def _estimer_steps(instruction: str) -> int:
    """Ask Qwen to estimate max steps needed. Fallback to 6."""
    if LANG == "en":
        prompt = (
            "How many tool-use steps maximum does this Windows PC task require? "
            "Reply with a SINGLE INTEGER between 1 and 20, nothing else.\n\n"
            f"Task: {instruction}"
        )
    else:
        prompt = (
            "Combien d'etapes outils maximum necessite cette tache sur un PC Windows ? "
            "Reponds UNIQUEMENT avec un entier entre 1 et 20, rien d'autre.\n\n"
            f"Tache : {instruction}"
        )
    raw = appel_chat([{"role": "user", "content": prompt}])
    try:
        n = int(re.search(r'\d+', raw).group())
        return max(3, min(n + 2, _MAX_STEPS_ABSOLU))  # +2 buffer for unexpected steps
    except Exception:
        return 8

# ── Agent ─────────────────────────────────────────────────────────────────────
def cmd_agent(instruction):
    """ReAct agent: Qwen reasons, acts, observes, repeats."""
    if not verifier_ollama():
        return

    home      = Path.home()
    bureau    = home / "Desktop"
    downloads = home / "Downloads"

    # Sudo mode: unlimited steps (capped at absolute max)
    if _auto_confirm:
        max_steps = _MAX_STEPS_ABSOLU
        console.print(f"[dim][bold yellow]SUDO[/bold yellow] — {t('agent_complexity', n=max_steps)}[/dim]")
    else:
        fixed = _cfg.get("max_steps", 0)
        if fixed > 0:
            max_steps = fixed
            console.print(f"[dim]{t('agent_complexity', n=max_steps)}[/dim]")
        else:
            with Progress(SpinnerColumn(), TextColumn(f"[cyan]{t('agent_estimating')}"),
                          transient=True) as prog:
                prog.add_task("")
                max_steps = _estimer_steps(instruction)
            console.print(f"[dim]{t('agent_complexity', n=max_steps)}[/dim]")

    if LANG == "en":
        system = (
            "You are a Windows assistant. To act, use ONLY these Fennec tools.\n"
            "NEVER use Windows commands in the cmd field. Only the exact tool names below.\n"
            "CRITICAL RULES:\n"
            "- move accepts ONE source file per call. NEVER semicolons or lists in args.\n"
            "- To move N files: make N separate move calls, one file at a time.\n"
            "- To create a folder: exec args:[cmd /c mkdir path]. Do this BEFORE moving files into it.\n"
            "- Desktop path is exactly as shown below. Never invent subfolders.\n"
"- ALWAYS use full ABSOLUTE paths in args (e.g. C:\\Users\\...\\file.ext).\n"
"- NEVER pass just a filename without its full path.\n"
            "- Minimum steps. Never open/read without explicit request.\n"
            "- If failure, report it in done. Stop as soon as task is complete.\n"
            "- If the task needs more steps than planned (e.g. moving several files one by one),"
" add \"need_more\":true in EACH tool reply until ALL files are processed.\n\n"
            "Available tools (cmd = exactly this name):\n"
            "  list      args:[folder]               -> list files and folders\n"
            "  find      args:[glob_pattern, folder] -> search e.g. *.pdf\n"
            "  sort      args:[folder, size|date]    -> sort by size or date\n"
            "  read      args:[file]                 -> read a file\n"
            "  open      args:[path]                 -> open with associated app\n"
            "  exec      args:[full_windows_command] -> run a Windows command\n"
            "  delete    args:[file]                 -> delete (moves to trash)\n"
            "  move      args:[source_path, destination_path] -> move ONE file (if dest ends with a new filename, also renames)\n"
"    e.g. rename+move: move [Downloads\\old.mp4, Desktop\\AXA\\new_name.mp4]\n"
            "  duplicate args:[source]               -> copy\n"
            "  clip      args:[path]                 -> copy path to clipboard\n\n"
            "REQUIRED format at each step:\n"
            "{\"action\":\"tool\",\"cmd\":\"<TOOL>\",\"args\":[\"arg1\"],\"reason\":\"...\"}\n"
            "When you have the final answer:\n"
            "{\"action\":\"done\",\"answer\":\"your answer\"}\n\n"
            f"EXACT paths (use as-is): desktop={bureau}  downloads={downloads}  cwd={cwd}\n"
            f"WARNING: desktop is {bureau}, not {bureau}\\bureau nor {bureau}\\Desktop.\n"
        )
    else:
        system = (
            "Tu es un assistant Windows. Pour agir, utilise UNIQUEMENT ces outils Fennec.\n"
            "JAMAIS de commandes Windows dans le champ cmd. Uniquement les noms d'outils ci-dessous.\n"
            "REGLES CRITIQUES :\n"
            "- move accepte UN seul fichier source par appel. JAMAIS de liste ou point-virgule.\n"
            "- Pour deplacer N fichiers : N appels move separes, un par fichier.\n"
            "- Pour creer un dossier : exec args:[cmd /c mkdir chemin]. Le faire AVANT de deplacer dedans.\n"
            "- Le chemin du bureau est exactement celui indique ci-dessous. Ne pas inventer de sous-dossiers.\n"
            "- TOUJOURS utiliser les chemins ABSOLUS complets dans les args (ex: C:\\Users\\...\\fichier.ext).\n"
            "- JAMAIS passer seulement un nom de fichier sans son chemin complet.\n"
            "- Minimum d'etapes. Ne jamais ouvrir/lire sans demande explicite.\n"
            "- Si echec, le dire dans done. S'arreter des que la tache est finie.\n"
            "- Si la tache necessite plus d'etapes que prevu (ex: deplacer plusieurs fichiers un par un),"
            " ajoute \"need_more\":true dans CHAQUE reponse tool jusqu'a avoir fini TOUS les fichiers.\n\n"
            "Outils disponibles (cmd = exactement ce nom) :\n"
            "  list      args:[dossier]                  -> liste fichiers et dossiers\n"
            "  find      args:[motif_glob, dossier]       -> cherche ex: *.pdf\n"
            "  sort      args:[dossier, taille|date]      -> trie par taille ou date\n"
            "  read      args:[fichier]                   -> lit un fichier\n"
            "  open      args:[chemin]                    -> ouvre avec l'app associee\n"
            "  exec      args:[commande_windows_complete] -> execute une commande Windows\n"
            "  delete    args:[fichier]                   -> supprime (vers corbeille)\n"
            "  move      args:[chemin_source, chemin_destination] -> deplace ET renomme si le chemin dest a un nouveau nom\n"
            "    TOUJOURS renommer avec un nom descriptif en francais/anglais coherent\n"
            "    ex: [C:\\Downloads\\IMG_3677.MOV, C:\\Desktop\\AXA\\video_beach_aout2025.mov]\n"
            "  duplicate args:[source]                    -> copie\n"
            "  clip      args:[chemin]                    -> chemin dans presse-papier\n\n"
            "Format OBLIGATOIRE a chaque etape :\n"
            "{\"action\":\"tool\",\"cmd\":\"<OUTIL>\",\"args\":[\"arg1\"],\"reason\":\"...\"}\n"
            "Quand tu as la reponse finale :\n"
            "{\"action\":\"done\",\"answer\":\"ta reponse\"}\n\n"
            f"Chemins EXACTS (utilise-les tels quels) : bureau={bureau}  downloads={downloads}  cwd={cwd}\n"
            f"ATTENTION : le bureau est {bureau}, pas {bureau}\\bureau ni {bureau}\\Desktop.\n"
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": instruction},
    ]
    pr(f"  [dim]{'─'*54}[/dim]")
    console.print(f"  [cyan]Agent[/cyan]  {escape(instruction)}")
    pr(f"  [dim]{'─'*54}[/dim]")

    etape = 0
    while etape < max_steps:
        etape += 1
        with Progress(SpinnerColumn(),
                      TextColumn(f"[cyan]{t('agent_thinking', s=etape, m=max_steps)}"),
                      transient=True) as prog:
            prog.add_task("")
            raw = appel_chat(messages, fmt_json=True)

        if not raw:
            pr(f"[yellow]{t('no_reply')}[/yellow]")
            break

        try:
            debut = raw.find("{")
            fin   = raw.rfind("}") + 1
            data  = json.loads(raw[debut:fin])
        except (json.JSONDecodeError, ValueError):
            pr("[cyan]Qwen >[/cyan]")
            for ligne in raw.splitlines():
                console.print(f"  {ligne}", markup=False)
            log("agent_text", raw[:200])
            break

        action = data.get("action", "tool")

        # Dynamic extension
        if data.get("need_more") and max_steps < _MAX_STEPS_ABSOLU:
            max_steps = min(max_steps + 3, _MAX_STEPS_ABSOLU)
            console.print(f"[dim]{t('agent_extended', n=max_steps)}[/dim]")

        if action == "done":
            if etape == 1:
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": t("agent_no_tool_first")})
                continue
            answer = data.get("answer", "")
            if answer:
                pr(f"  [dim]{'─'*54}[/dim]")
                pr("[bold green]  ✓ Qwen[/bold green]")
                for ligne in answer.splitlines():
                    console.print(f"    {ligne}", markup=False)
                log("agent_done", answer[:200])
            break

        cmd  = data.get("cmd", "")
        args = [str(a) for a in data.get("args", [])]
        reason = data.get("reason", "")

        if not cmd:
            pr(f"[yellow]{t('agent_no_cmd')}[/yellow]")
            break

        step_color = "yellow" if _auto_confirm else "cyan"
        info = (f"[{step_color}]  [{etape}][/{step_color}] [bold]{escape(str(cmd))}[/bold]"
                f"[dim]({escape(', '.join(args))})"
                + (f"  — {escape(str(reason))}" if reason else "") + "[/dim]")
        console.print(info)

        if cmd in ("delete","move","rename"):
            if not confirmer(f"Agent wants to {cmd} {args}"):
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": t("agent_refused")})
                continue

        if cmd not in AGENT_CMDS_VALIDES:
            pr(f"[dim]  -> unknown command, falling back to exec[/dim]")
            cmd_reel  = "exec"
            args_reel = [cmd + (" " + " ".join(args) if args else "")]
        else:
            cmd_reel, args_reel = cmd, args

        sortie = _executer_outil(cmd_reel, args_reel)

        messages.append({"role": "assistant", "content": raw})
        if not sortie or sortie in ("(command executed)", "(commande executee)"):
            feedback = f"Command {cmd_reel} executed successfully."
        else:
            feedback = f"Result of {cmd_reel}:\n{sortie}"

        # Remind Qwen to keep going if the original task isn't finished
        steps_left = max_steps - etape
        if steps_left <= 3 and steps_left > 0:
            reminder = (
                f" You have {steps_left} steps left. If you are not done yet, add \"need_more\":true NOW."
                if LANG == "en" else
                f" Il te reste {steps_left} etapes. Si tu n'as pas fini, ajoute \"need_more\":true MAINTENANT."
            )
            feedback += reminder

        messages.append({"role": "user", "content": feedback})
        log("agent_step", f"step={etape} cmd={cmd} args={args}")
    else:
        pr(f"[yellow]{t('agent_limit', n=max_steps)}[/yellow]")

# ── Web helpers ───────────────────────────────────────────────────────────────
_WEB_KEYWORDS = {
    "meteo","météo","temperature","température","temps","pluie","soleil","vent",
    "weather","forecast","rain","wind",
    "actualite","actualité","news","aujourd'hui","maintenant","ce soir","cette semaine",
    "today","tonight","this week","breaking",
    "prix","tarif","cours","bourse","bitcoin","euro","dollar","price","stock",
    "score","résultat","résultats","match","classement","result","standings",
    "horaire","horaires","ouvert","fermé","ferme","hours","opening hours",
    "trafic","embouteillage","greve","grève","traffic","strike",
    "sortie","film","concert","evenement","événement","movie","event",
}

def _besoin_web(texte):
    t_low = texte.lower()
    return any(kw in t_low for kw in _WEB_KEYWORDS)

def _web_context(query):
    try:
        resultats = _scrape_ddg(query)
        if not resultats:
            return ""
        parties = [f"- {titre}: {extrait[:200]}"
                   for titre, lien, extrait in resultats[:4] if extrait]
        return ("Web data:\n" + "\n".join(parties)) if parties else ""
    except Exception:
        return ""

def _scrape_ddg(terme):
    import ssl as _ssl
    html_mod = _html
    url = f"https://html.duckduckgo.com/html/?q={urllib.request.quote(terme)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    })
    ctx = _ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        html_content = resp.read().decode("utf-8", errors="replace")
    titres   = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_content)
    extraits = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html_content)
    resultats = []
    for idx, (lien, titre) in enumerate(titres[:6]):
        titre_propre   = html_mod.unescape(re.sub(r'<[^>]+>', '', titre)).strip()
        extrait_propre = ""
        if idx < len(extraits):
            extrait_propre = html_mod.unescape(re.sub(r'<[^>]+>', '', extraits[idx])).strip()
        if "uddg=" in lien:
            try:
                lien = urllib.request.unquote(lien.split("uddg=")[1].split("&")[0])
            except Exception:
                pass
        resultats.append((titre_propre, lien, extrait_propre))
    return resultats

# ── Chat (streaming) ──────────────────────────────────────────────────────────
def cmd_chat():
    if not verifier_ollama():
        return
    pr(f"[green]{t('chat_header')}[/green]")

    lang_rule = (
        "ABSOLUTE RULE: respond EXCLUSIVELY in English, no exceptions."
        if LANG == "en" else
        "REGLE ABSOLUE : reponds EXCLUSIVEMENT en francais, sans exception."
    )
    historique = [
        {"role": "system", "content":
         f"You are a helpful concise personal assistant. {lang_rule} "
         "When a [Web context] is provided in the message, use it to answer precisely. "
         "Without web context, if you do not know a real-time value (weather, prices, scores), "
         "say so and suggest using the search command. Never invent numbers."}
    ]
    CMDS_DIRECTES = {"search","download","install","uninstall","find","list","ls",
                     "read","cat","open","exec","clip","sort","cd","bm","bookmark",
                     "logs","helpchat","diff","undo","settings","alias"}

    while True:
        try:
            if _session:
                saisie = _session.prompt(HTML(f"<prompt>{t('chat_you')} </prompt>")).strip()
            else:
                console.print(f"[green]{t('chat_you')}[/green] ", end="")
                saisie = input().strip()
        except KeyboardInterrupt:
            pr(f"\n[dim]{t('chat_back')}[/dim]")
            break
        except EOFError:
            break
        if not saisie:
            continue
        if saisie.lower() in ("exit","quit","q"):
            pr(f"[dim]{t('chat_back')}[/dim]")
            break

        try:
            tokens = shlex.split(saisie, posix=False)
        except ValueError:
            tokens = saisie.split()
        tokens = [tok.strip("\"'") for tok in tokens]
        if tokens and tokens[0].lower() in CMDS_DIRECTES:
            pr(f"[dim]{t('cmd_detected')}[/dim]")
            dispatcher(tokens[0].lower(), tokens[1:])
            continue

        contenu_user = saisie
        if _besoin_web(saisie):
            with Progress(SpinnerColumn(), TextColumn("[cyan]Web search..."), transient=True) as prog:
                prog.add_task("")
                ctx = _web_context(saisie)
            if ctx:
                contenu_user = saisie + "\n\n[Web context]\n" + ctx
                pr(f"[dim]{t('web_injected')}[/dim]")
            else:
                pr(f"[dim]{t('web_none')}[/dim]")

        historique.append({"role": "user", "content": contenu_user})
        console.print("[cyan]Qwen >[/cyan] ", end="")
        reponse = appel_chat_stream(historique[-10:])
        if not reponse:
            pr(f"[dim]{t('no_reply')}[/dim]")
            historique.pop()
            continue
        historique.append({"role": "assistant", "content": reponse})
        log("chat", saisie[:100])

# ── Install / search ──────────────────────────────────────────────────────────
def cmd_uninstall(nom):
    if not nom:
        pr("[red]Usage: uninstall [program name][/red]")
        return
    console.print(f"[cyan]Looking for '{escape(nom)}' in winget...[/cyan]")
    result = subprocess.run(["winget","list","--name",nom],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    lignes = [l for l in result.stdout.splitlines() if nom.lower() in l.lower()]
    if not lignes:
        console.print(f"[yellow]No match for '{escape(nom)}' in winget.[/yellow]")
        pr("[dim]Try a shorter name or: exec winget list[/dim]")
        return
    pr("[cyan]Found:[/cyan]")
    for l in lignes:
        console.print(f"  {l}", markup=False)
    if not confirmer(f"Uninstall '{nom}' via winget?"):
        return
    pr("[cyan]Uninstalling...[/cyan]")
    with Progress(SpinnerColumn(), TextColumn("[cyan]Uninstalling..."), transient=True) as prog:
        prog.add_task("")
        result = subprocess.run(["winget","uninstall","--name",nom,"--silent"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        console.print(result.stdout.strip(), markup=False)
    if result.returncode != 0 and result.stderr:
        console.print(f"[red]{t('error')}[/red]", end="")
        console.print(result.stderr.strip(), markup=False)
        log("uninstall_error", f"{nom}: {result.stderr[:200]}")
        return
    console.print(f"[green]'{escape(nom)}' uninstalled.[/green]")
    log("uninstall", nom)
    if GEEK_EXE.exists():
        pr("[cyan]Opening Geek Uninstaller to clean leftovers...[/cyan]")
        pr("[dim]  -> Right-click the program then 'Scan for Leftovers'[/dim]")
        try:
            ctypes.windll.shell32.ShellExecuteW(None,"runas",str(GEEK_EXE),None,str(BASE_DIR),1)
            log("geek_uninstaller", nom)
        except Exception as e:
            console.print("[red]Cannot launch Geek Uninstaller: [/red]", end="")
            console.print(str(e), markup=False)
    else:
        pr("[yellow]Tip: place geek.exe next to fennec.py for registry cleanup.[/yellow]")
        pr("[dim]  Download at https://geekuninstaller.com (free, portable)[/dim]")

def cmd_search(terme):
    if not terme:
        pr("[red]Usage: search [term][/red]")
        return
    pr(f"[cyan]{t('search_label')}{escape(terme)}[/cyan]")
    resultats = []
    try:
        resultats = _scrape_ddg(terme)
    except Exception as e:
        console.print(f"[yellow]Scraping unavailable: [/yellow]", end="")
        console.print(str(e), markup=False, end="")
        console.print(f"[yellow] {t('opening_browser')}[/yellow]")
        try:
            os.startfile(f"https://duckduckgo.com/?q={urllib.request.quote(terme)}")
        except Exception:
            pass
        log("search", terme)
        return

    if not resultats:
        pr(f"[yellow]{t('no_result')} {t('opening_browser')}[/yellow]")
        try:
            os.startfile(f"https://duckduckgo.com/?q={urllib.request.quote(terme)}")
        except Exception:
            pass
        log("search", terme)
        return

    if ollama_vivant():
        contexte = "\n".join(
            f"[{i+1}] {titre}\n{extrait}"
            for i, (titre, lien, extrait) in enumerate(resultats) if extrait
        )
        lang_instr = "Respond in English." if LANG == "en" else "Reponds en francais."
        messages = [
            {"role": "system", "content":
             f"You are an assistant. From the search excerpts, answer the question "
             f"in 2-4 sentences max. Be factual and concise. {lang_instr} "
             "If excerpts are insufficient, say so."},
            {"role": "user", "content": f"Question: {terme}\n\nExcerpts:\n{contexte}"},
        ]
        with Progress(SpinnerColumn(), TextColumn("[cyan]Qwen synthesis..."), transient=True) as prog:
            prog.add_task("")
            reponse = appel_chat(messages)
        if reponse:
            pr("[bold cyan]Answer >[/bold cyan]")
            for ligne in reponse.splitlines():
                console.print(f"  {ligne}", markup=False)
            console.print("")

    pr("[dim]Sources:[/dim]")
    for i, (titre, lien, extrait) in enumerate(resultats, 1):
        console.print(f"  [bold]{i}.[/bold] {escape(titre)}")
        console.print(f"     [dim]{escape(lien)}[/dim]")

    mots_logiciel = {"install","download","logiciel","app","programme","gratuit",
                     "windows","software","telecharger"}
    if any(m in terme.lower() for m in mots_logiciel):
        result = subprocess.run(["winget","search",terme],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        utiles = [l for l in result.stdout.strip().splitlines() if l.strip()][:6]
        if utiles and not any(x in " ".join(utiles).lower() for x in ("no package","aucun")):
            pr("[dim]Winget:[/dim]")
            for l in utiles:
                console.print(f"  {l}", markup=False)
    log("search", terme)

def cmd_download(url, dest=""):
    if not url:
        pr("[red]Usage: download [url] [dest?][/red]")
        return
    if not url.startswith(("http://","https://")):
        pr("[red]Invalid URL: must start with http:// or https://[/red]")
        return
    nom_fichier = Path(url.split("?")[0]).name or "downloaded_file"
    dest_path   = (resoudre(dest) if dest else cwd / nom_fichier)
    console.print(f"[cyan]Downloading: {escape(url)}[/cyan]")
    console.print(f"[dim]  -> {escape(str(dest_path))}[/dim]")
    dest_tmp = dest_path.with_suffix(dest_path.suffix + ".tmp")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Fennec/2.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            read  = 0
            with open(dest_tmp, "wb") as f:
                while True:
                    bloc = resp.read(65536)
                    if not bloc:
                        break
                    f.write(bloc)
                    read += len(bloc)
                    if total:
                        pct = min(100, int(read * 100 / total))
                        print(f"\r  {pct}%  {fmt_taille(read)} / {fmt_taille(total)}   ", end="", flush=True)
        print()
        dest_tmp.replace(dest_path)
        console.print(f"[green]Downloaded: {escape(dest_path.name)}  ({fmt_taille(dest_path.stat().st_size)})[/green]")
        log("download", f"{url} -> {dest_path}")
    except Exception as e:
        if dest_tmp.exists():
            dest_tmp.unlink(missing_ok=True)
        console.print("[red]Download error: [/red]", end="")
        console.print(str(e), markup=False)
        log("download_error", str(e))

def cmd_install(nom):
    if not nom:
        pr("[red]Usage: install [program][/red]")
        return
    console.print(f"[cyan]Searching '{escape(nom)}' in winget...[/cyan]")
    result = subprocess.run(["winget","search",nom],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    lignes = [l for l in result.stdout.strip().splitlines() if l.strip()]
    if not lignes:
        console.print(f"[yellow]No results for '{escape(nom)}'.[/yellow]")
        return
    for l in lignes[:10]:
        console.print(f"  {l}", markup=False)
    if not confirmer(f"Install '{nom}' via winget?"):
        return
    pr("[cyan]Installing...[/cyan]")
    with Progress(SpinnerColumn(), TextColumn("[cyan]Installing..."), transient=True) as prog:
        prog.add_task("")
        result = subprocess.run(
            ["winget","install","--name",nom,"--silent",
             "--accept-package-agreements","--accept-source-agreements"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    if result.stdout:
        console.print(result.stdout.strip(), markup=False)
    if result.returncode != 0:
        if result.stderr:
            console.print(f"[red]{t('error')}[/red]", end="")
            console.print(result.stderr.strip(), markup=False)
        pr(f"[yellow]{t('install_tip')}[/yellow]")
        log("install_error", nom)
        return
    console.print(f"[green]'{escape(nom)}' installed successfully.[/green]")
    log("install", nom)

def cmd_redate(dossier="", mode="creation"):
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists() or not dp.is_dir():
        console.print(f"[red]{t('not_found')}{escape(str(dp))}[/red]")
        return
    fichiers = [e for e in dp.iterdir() if e.is_file()]
    if not fichiers:
        pr("[yellow]No files in this folder.[/yellow]")
        return
    def get_date(f):
        st = f.stat()
        ts = st.st_ctime if mode == "creation" else st.st_mtime
        return datetime.fromtimestamp(ts)
    fichiers.sort(key=get_date)
    plan = []
    compteurs = {}
    for f in fichiers:
        d     = get_date(f)
        annee = str(d.year)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        plan.append((f, dp / f"{annee}_{compteurs[annee]:02d}{f.suffix.lower()}"))
    pr(f"[cyan]Rename plan ({len(plan)} files) -- date: {mode}[/cyan]")
    for src, dst in plan[:20]:
        console.print(f"  {src.name:<40} -> {dst.name}", markup=False)
    if len(plan) > 20:
        pr(f"[dim]  ... and {len(plan)-20} more[/dim]")
    if not confirmer(f"Rename {len(plan)} files in {dp.name}?"):
        return
    tmp_plan = []
    try:
        for src, dst in plan:
            tmp = src.parent / (src.name + ".redate_tmp")
            src.rename(tmp)
            tmp_plan.append((tmp, dst))
    except Exception:
        for tmp, _ in tmp_plan:
            try: tmp.rename(tmp.parent / tmp.name.removesuffix(".redate_tmp"))
            except Exception: pass
        pr("[yellow]Interrupted -- files restored.[/yellow]")
        return
    erreurs = 0
    for tmp, dst in tmp_plan:
        try:
            final = dst
            if final.exists():
                final = dst.parent / f"{dst.stem}_dup{dst.suffix}"
            tmp.rename(final)
            console.print(f"[green]  {escape(final.name)}[/green]")
        except Exception as e:
            console.print("[red]  Error: [/red]", end="")
            console.print(str(e), markup=False)
            erreurs += 1
    pr(f"[bold green]{len(plan)-erreurs} files renamed.[/bold green]")
    if erreurs:
        pr(f"[red]{erreurs} error(s).[/red]")
    log("redate", f"{dp} mode={mode} n={len(plan)}")

# ── Helpchat ──────────────────────────────────────────────────────────────────
FENNEC_DOC = r"""
Fennec is a Windows file management shell powered by AI (Qwen2.5 via Ollama).

=== NAVIGATION ===
cd [folder]         Change directory. Without argument shows current folder.
list [folder?]      List files and folders.
ls                  Alias for list.
sort [folder?] [size|date]  Sort files by size (default) or date.
find [pattern] [folder?] [depth?]  Recursive search by glob. Optional depth limit.
                    Examples: find *.pdf   find *.jpg Downloads 3

=== FILES ===
read [file] [n?]    Read a file (max n lines). Supports .txt .py .pdf .docx etc.
cat                 Alias for read.
write [file] [text?]  Write text to file. Interactive mode if no text given.
delete [file]       Moves to .fennec_trash folder (recoverable with undo). Requires confirmation.
rename [folder] [old] [new]  Mass rename with glob patterns. * captures and reinjects.
move [source] [dest]  Move a file. Requires confirmation.
duplicate [source] [dest?]  Copy a file.
diff [file1] [file2]  Compare two text files side by side (color diff).
undo                Undo the last delete/move/rename operation.

=== SYSTEM ===
open [path?]        Open with associated Windows app. No arg: opens current folder.
clip [path?]        Copy absolute path to clipboard.
exec [command]      Run any CMD command. Requires confirmation.
redate [folder?] [creation|modif]  Rename files by date+number.

=== WEB & INSTALL ===
search [term]       Web search (DuckDuckGo) + Qwen synthesis + winget check.
download [url] [dest?]  Download a file with progress bar.
install [program]   Install via winget. Requires confirmation.
uninstall [program] Uninstall via winget + optional Geek Uninstaller cleanup.

=== BOOKMARKS ===
bm list             List bookmarks.
bm add [name] [path?]  Save current folder (or given path) as a short name.
bm remove [name]    Remove a bookmark.
bookmark            Alias for bm.

=== ALIASES ===
alias list              List all aliases.
alias add [name] [cmd]  Create a shortcut (e.g. alias add ll list).
alias remove [name]     Remove an alias.

=== SETTINGS ===
settings                Show current settings.
settings lang en        Switch interface and AI to English.
settings lang fr        Switch interface and AI to French.
settings model [name]   Change Ollama model. No arg: list installed models.
settings max_steps 0    Auto-estimate steps per agent task (0=auto, n=fixed).

=== AI ===
agent [instruction] Qwen analyses your request and acts step by step.
                    Step count is estimated automatically by Qwen.
                    Confirmation required for delete/move/rename.
                    Examples:
                      agent list the 5 heaviest files on my desktop
                      agent find all PDFs in Downloads and count them
                      agent delete all .tmp files from current folder
chat                Free conversation with Qwen (streaming). exit to return.
helpchat [question] This help bot.

=== MISC ===
logs [n?]           Show last n logged actions (default 30).
help                Show command list.
exit / quit / q     Quit Fennec.

=== TIPS ===
- Tab: autocomplete commands and paths.
- Up/Down arrows: recall previous commands (history).
- Paths with spaces: use quotes -> cd "My Folder"
- Unknown command: Fennec tries it as a Windows CMD command.
- Commands marked ! always ask for confirmation before acting.
- . = current folder, .. = parent folder.
- delete is safe: files go to .fennec_trash, use undo to recover.
"""

def cmd_helpchat(question=""):
    """If called with a question, answer it directly.
    If called without args, enter interactive help mode."""
    if not verifier_ollama():
        return
    lang_instr = "Answer in English." if LANG == "en" else "Reponds en francais."
    system_msg = {
        "role": "system", "content":
        f"You are the built-in help bot for Fennec, an AI-powered Windows shell. "
        f"Use only the documentation below to answer. Be concise and always give a concrete command example. "
        f"{lang_instr}\n\n=== FENNEC DOCUMENTATION ===\n{FENNEC_DOC}"
    }

    def _ask(q):
        console.print("[bold cyan]Help > [/bold cyan]", end="")
        reponse = appel_chat_stream([system_msg, {"role": "user", "content": q}])
        if not reponse:
            pr(f"[yellow]{t('no_reply')}[/yellow]")
        log("helpchat", q[:100])

    if question:
        _ask(question)
        return

    # Interactive mode
    pr("[cyan]-- Fennec Help  (exit to quit) --[/cyan]")
    pr("[dim]Ask anything about Fennec commands.[/dim]")
    while True:
        try:
            console.print("[cyan]help >[/cyan] ", end="")
            q = input().strip()
        except (KeyboardInterrupt, EOFError):
            pr(f"\n[dim]{t('chat_back')}[/dim]")
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            pr(f"[dim]{t('chat_back')}[/dim]")
            break
        _ask(q)

# ── Logs & help ───────────────────────────────────────────────────────────────
def cmd_logs(n=30):
    if not LOG_FILE.exists():
        pr("[dim]No logs.[/dim]")
        return
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        lignes = f.readlines()
    for ligne in lignes[-n:]:
        console.print(f"[dim]{escape(ligne.rstrip())}[/dim]")

def cmd_help():
    if LANG == "en":
        lignes = [
            ("cd",        "[folder]",                       "Change directory"),
            ("list/ls",   "[folder?]",                      "List files"),
            ("find",      "[*.ext] [folder?] [depth?]",     "Recursive search"),
            ("sort",      "[folder?] [size|date]",          "Sort files"),
            ("read/cat",  "[file] [lines?]",                "Read a file"),
            ("write",     "[file] [text?]",                 "Write file !"),
            ("delete",    "[file]",                         "Move to trash (undo restores) !"),
            ("rename",    "[folder] [old] [new]",           "Mass rename with glob !"),
            ("move",      "[source] [dest]",                "Move !"),
            ("duplicate", "[source] [dest?]",               "Copy"),
            ("diff",      "[file1] [file2]",                "Compare two files"),
            ("undo",      "",                               "Undo last destructive op"),
            ("open",      "[path?]",                        "Open with Windows app"),
            ("clip",      "[path?]",                        "Copy path to clipboard"),
            ("exec",      "[command]",                      "Run CMD command !"),
            ("redate",    "[folder?] [creation|modif]",     "Rename files by date !"),
            ("search",    "[term]",                         "Web search + Qwen"),
            ("download",  "[url] [dest?]",                  "Download a file"),
            ("install",   "[program]",                      "Install via winget !"),
            ("uninstall", "[program]",                      "Uninstall + cleanup !"),
            ("bm",        "[list|add|remove] [name]",       "Bookmarks"),
            ("alias",     "[list|add|remove] [name] [cmd]", "Aliases"),
        ("sudo",      "[on|off]",                      "Auto-confirm mode (no more y/n)"),
            ("settings",  "[key] [value?]",                 "Settings (lang, model, ...)"),
            ("agent",     "[instruction]",                  "AI agent (auto steps)"),
            ("chat",      "",                               "Chat with Qwen (streaming)"),
            ("helpchat",  "[question?]",                    "Built-in help bot"),
            ("logs",      "[n=30]",                         "Last logs"),
            ("help",      "",                               "This help"),
            ("exit",      "",                               "Quit"),
        ]
        footer = "  ! = confirmation required"
        header = "-- Fennec commands --"
    else:
        lignes = [
            ("cd",        "[dossier]",                          "Changer de dossier"),
            ("list/ls",   "[dossier?]",                         "Lister les fichiers"),
            ("find",      "[*.ext] [dossier?] [profondeur?]",   "Recherche recursive"),
            ("sort",      "[dossier?] [taille|date]",           "Trier"),
            ("read/cat",  "[fichier] [lignes?]",                "Lire un fichier"),
            ("write",     "[fichier] [texte?]",                 "Ecrire (interactif) !"),
            ("delete",    "[fichier]",                          "Corbeille (undo restaure) !"),
            ("rename",    "[dossier] [ancien] [nouveau]",       "Renommer en masse !"),
            ("move",      "[source] [dest]",                    "Deplacer !"),
            ("duplicate", "[source] [dest?]",                   "Copier"),
            ("diff",      "[fichier1] [fichier2]",              "Comparer deux fichiers"),
            ("undo",      "",                                   "Annuler derniere action"),
            ("open",      "[chemin?]",                          "Ouvrir avec app Windows"),
            ("clip",      "[chemin?]",                          "Chemin dans presse-papier"),
            ("exec",      "[commande]",                         "Executer commande CMD !"),
            ("redate",    "[dossier?] [creation|modif]",        "Renommer par date !"),
            ("search",    "[terme]",                            "Recherche web + Qwen"),
            ("download",  "[url] [dest?]",                      "Telecharger un fichier"),
            ("install",   "[programme]",                        "Installer via winget !"),
            ("uninstall", "[programme]",                        "Desinstaller + nettoyage !"),
            ("bm",        "[list|add|remove] [nom]",            "Favoris"),
            ("alias",     "[list|add|remove] [nom] [cmd]",      "Alias"),
            ("sudo",      "[on|off]",                               "Mode auto-validation (plus de o/n)"),
            ("settings",  "[cle] [valeur?]",                    "Parametres (lang, model...)"),
            ("agent",     "[instruction]",                      "Agent IA (etapes auto)"),
            ("chat",      "",                                   "Chat avec Qwen (streaming)"),
            ("helpchat",  "[question?]",                        "Bot d'aide integre"),
            ("logs",      "[n=30]",                             "Derniers logs"),
            ("help",      "",                                   "Cette aide"),
            ("exit",      "",                                   "Quitter"),
        ]
        footer = "  ! = confirmation requise"
        header = "-- Commandes Fennec --"
    # Split into sections
    NAV   = {"cd","list/ls","find","sort"}
    FILES = {"read/cat","write","delete","rename","move","duplicate","diff","undo"}
    SYS   = {"open","clip","exec","redate"}
    WEB   = {"search","download","install","uninstall"}
    AI    = {"agent","chat","helpchat"}
    CFG   = {"bm","alias","sudo","settings","logs","help","exit"}

    sec_label = {
        "NAV":   "  Navigation",
        "FILES": "  Fichiers",
        "SYS":   "  Systeme",
        "WEB":   "  Web & Install",
        "AI":    "  Intelligence artificielle",
        "CFG":   "  Config & divers",
    } if LANG != "en" else {
        "NAV":   "  Navigation",
        "FILES": "  Files",
        "SYS":   "  System",
        "WEB":   "  Web & Install",
        "AI":    "  AI",
        "CFG":   "  Config & misc",
    }
    sec_map = [("NAV",NAV),("FILES",FILES),("SYS",SYS),("WEB",WEB),("AI",AI),("CFG",CFG)]

    pr("")
    pr(f"[bold cyan]  🦊 {header}[/bold cyan]")
    pr(f"  [dim]{'─'*54}[/dim]")

    for sec_key, sec_cmds in sec_map:
        sec_lines = [(c,a,d) for c,a,d in lignes if c in sec_cmds]
        if not sec_lines:
            continue
        pr(f"  [bold white]{sec_label[sec_key]}[/bold white]")
        for cmd, args, desc in sec_lines:
            is_danger = "!" in desc
            is_ai     = sec_key == "AI"
            is_sudo   = cmd == "sudo"
            desc_clean = desc.rstrip(" !")
            danger_tag = " [red]![/red]" if is_danger else ""
            if is_ai:
                cmd_color = f"[bold green]{cmd:<14}[/bold green]"
            elif is_sudo:
                cmd_color = f"[bold yellow]{cmd:<14}[/bold yellow]"
            else:
                cmd_color = f"[bold cyan]{cmd:<14}[/bold cyan]"
            pr(f"    {cmd_color}[dim]{args:<32}[/dim] {desc_clean}{danger_tag}")
        pr("")

    pr(f"  [dim][red]![/red] = {footer.replace('! = ', '')}   [yellow]sudo on[/yellow] = auto-valider toutes les actions[/dim]")
    pr("")

# ── Autocomplete ──────────────────────────────────────────────────────────────
CMDS_CHEMIN = {"cd","list","ls","find","read","cat","write","delete","rm","move",
               "mv","duplicate","cp","open","clip","exec","sort","rename","bm","diff"}
CMDS_TOUTES = ["cd","list","ls","find","read","cat","write","delete","rm","rename",
               "move","mv","duplicate","cp","sort","open","clip","exec","redate",
               "search","download","install","uninstall","bookmark","bm","agent",
               "helpchat","chat","logs","help","exit","diff","undo","settings","alias","sudo"]

class FennecCompleter(Completer):
    def get_completions(self, document, complete_event):
        texte = document.text_before_cursor
        try:
            tokens = shlex.split(texte, posix=False)
        except ValueError:
            tokens = texte.split()

        if not tokens or (len(tokens) == 1 and not texte.endswith(" ")):
            prefix   = tokens[0].lower() if tokens else ""
            all_cmds = list(CMDS_TOUTES) + list(_aliases.keys())
            for cmd in all_cmds:
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
            return

        cmd = tokens[0].lower()
        if cmd not in CMDS_CHEMIN:
            return

        if texte.endswith(" "):
            fragment = ""
            base_dir = cwd
        else:
            fragment = tokens[-1].strip("\"'")
            p = Path(fragment)
            if p.is_absolute():
                base_dir = p.parent if not fragment.endswith(("/","\\")) else p
            else:
                base_dir = (cwd/p).parent if not fragment.endswith(("/","\\")) else cwd/p

        try:
            entries = sorted(base_dir.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except (PermissionError, OSError):
            return

        for entry in entries:
            nom = entry.name
            typed_name = Path(fragment).name if fragment and not fragment.endswith(("/","\\")) else ""
            if typed_name and not nom.lower().startswith(typed_name.lower()):
                continue
            display   = nom + ("/" if entry.is_dir() else "")
            full_path = str(base_dir / nom)
            if " " in full_path:
                insert = f'"{full_path}{"/" if entry.is_dir() else ""}"'
                start  = -(len(tokens[-1]) if not texte.endswith(" ") else 0)
            else:
                insert = display
                start  = -len(typed_name) if typed_name else 0
            yield Completion(insert, start_position=start, display=display,
                             display_meta="[dir]" if entry.is_dir() else "")

def _make_bindings():
    kb = _KB()
    @kb.add("tab")
    def _tab(event):
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.apply_completion(buf.complete_state.current_completion)
        else:
            buf.start_completion(select_first=True)
    return kb

# ── Dispatcher ────────────────────────────────────────────────────────────────
def dispatcher(cmd, args):
    # Alias resolution before dispatch
    if cmd in _aliases:
        try:
            aliased = shlex.split(_aliases[cmd])
        except ValueError:
            aliased = _aliases[cmd].split()
        cmd  = aliased[0].lower()
        args = aliased[1:] + list(args)

    def a(i, d=None): return args[i] if len(args) > i else d
    match cmd:
        case "cd":                   cmd_cd(a(0,""))
        case "list"|"ls":            cmd_list(a(0,""))
        case "find":
            if not args: pr("[red]Usage: find [pattern] [folder?] [depth?][/red]")
            else: cmd_find(a(0,"*"), a(1,""), a(2,""))
        case "read"|"cat":
            if not args: pr("[red]Usage: read [file] [lines?][/red]")
            else:
                try: lim = int(a(1,100))
                except: lim = 100
                cmd_read(a(0), lim)
        case "write":
            if not args: pr("[red]Usage: write [file] [text?][/red]")
            else: cmd_write(a(0), " ".join(args[1:]) if len(args)>=2 else None)
        case "delete"|"del"|"rm":
            if not args: pr("[red]Usage: delete [file][/red]")
            else: cmd_delete(a(0))
        case "rename":
            if len(args) < 2:
                pr("[red]Usage: rename [folder] [old_pattern] [new_pattern][/red]")
                pr("[dim]Example: rename . *.JPG *.jpg[/dim]")
            elif len(args) == 2: cmd_rename(".", a(0), a(1))
            else: cmd_rename(a(0), a(1), a(2))
        case "move"|"mv":
            if len(args)<2: pr("[red]Usage: move [source] [dest][/red]")
            else: cmd_move(a(0), a(1))
        case "duplicate"|"cp"|"copy":
            if not args: pr("[red]Usage: duplicate [source][/red]")
            else: cmd_duplicate(a(0), a(1,""))
        case "sort":               cmd_sort(a(0,""), a(1,"taille"), a(2,"0"))
        case "open":               cmd_open(a(0,""))
        case "clip":               cmd_clip(a(0,""))
        case "redate":             cmd_redate(a(0,""), a(1,"creation"))
        case "diff":
            if len(args)<2: pr("[red]Usage: diff [file1] [file2][/red]")
            else: cmd_diff(a(0), a(1))
        case "undo":               cmd_undo()
        case "search":
            if not args: pr("[red]Usage: search [term][/red]")
            else: cmd_search(" ".join(args))
        case "download":
            if not args: pr("[red]Usage: download [url][/red]")
            else: cmd_download(a(0,""), a(1,""))
        case "install":
            if not args: pr("[red]Usage: install [program][/red]")
            else: cmd_install(" ".join(args))
        case "uninstall":
            if not args: pr("[red]Usage: uninstall [program][/red]")
            else: cmd_uninstall(" ".join(args))
        case "exec":
            if not args: pr("[red]Usage: exec [command][/red]")
            else: cmd_exec(" ".join(args))
        case "bookmark"|"bm":      cmd_bookmark(a(0,"list"), a(1,""), a(2,""))
        case "alias":              cmd_alias(args)
        case "sudo":               cmd_sudo(args)
        case "settings":           cmd_settings(args)
        case "agent":
            if not args: pr("[red]Usage: agent [instruction][/red]")
            else: cmd_agent(" ".join(args))
        case "helpchat":
            if not args: pr("[red]Usage: helpchat [question][/red]")
            else: cmd_helpchat(" ".join(args))
        case "chat":               cmd_chat()
        case "logs":               cmd_logs(int(args[0]) if args else 30)
        case "help"|"?":           cmd_help()
        case "exit"|"quit"|"q":    raise SystemExit
        case _:
            cmd_exec(cmd + (" " + " ".join(args) if args else ""))

# ── Prompt label ──────────────────────────────────────────────────────────────
def label():
    if _auto_confirm:
        return "Fennec [SUDO]"
    return "Fennec"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global cwd, _session
    completer = FennecCompleter()
    _session  = PromptSession(
        history=FileHistory(str(HIST_FILE)),
        completer=completer,
        complete_while_typing=False,
        complete_in_thread=True,
        style=Style.from_dict({"prompt": "bold ansicyan"}),
        key_bindings=_make_bindings(),
    )

    pr("")
    pr(f"[bold cyan]  🦊 Fennec[/bold cyan]  [dim]v2  —  {MODEL}[/dim]")
    pr(f"  [dim]{'─'*52}[/dim]")
    pr(f"  [cyan]agent[/cyan] [dim]<instruction>[/dim]   [cyan]chat[/cyan]   [cyan]help[/cyan]   [cyan]settings[/cyan]   [dim]settings lang {'fr' if LANG=='en' else 'en'}[/dim]")
    pr("")
    log("startup", f"lang={LANG} model={MODEL}")

    while True:
        try:
            saisie = _session.prompt(HTML(f"<prompt>{label()} > </prompt>")).strip()
            if not saisie:
                continue
            try:
                tokens = shlex.split(saisie, posix=False)
            except ValueError:
                tokens = saisie.split()
            tokens = [tok.strip("\"'") for tok in tokens]
            dispatcher(tokens[0].lower(), tokens[1:])
        except KeyboardInterrupt:
            pr(f"\n[dim]{t('ctrl_c')}[/dim]")
        except EOFError:
            break
        except SystemExit:
            pr(f"[dim]{t('goodbye')}[/dim]")
            log("shutdown")
            break
        except Exception as e:
            console.print(f"[red]{t('error')}[/red]", end="")
            console.print(str(e), markup=False)
            log("error", str(e))

if __name__ == "__main__":
    main()
