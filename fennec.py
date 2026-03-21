"""
Fennec — Assistant fichiers Windows + IA locale
================================================
Dépendances : pip install rich prompt_toolkit
Ollama requis : https://ollama.com  (ollama pull qwen2.5:7b)
"""

import os
import io
import re
import html as _html
import json
import shlex
import shutil
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
    raise SystemExit("Installe rich : pip install rich")

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
except ImportError:
    raise SystemExit("Installe prompt_toolkit : pip install prompt_toolkit")

BASE_DIR       = Path(__file__).parent
LOG_FILE       = BASE_DIR / "fennec_logs.txt"
HIST_FILE      = BASE_DIR / ".fennec_history"
BOOKMARKS_FILE = BASE_DIR / ".fennec_bookmarks.json"
MODEL          = "qwen2.5:7b"
OLLAMA_URL     = "http://localhost:11434"

AGENT_CMDS_VALIDES = {"list","ls","find","sort","read","open","cd","exec",
                      "delete","move","duplicate","clip","rename","write"}

console      = Console(highlight=False)
cwd          = Path.cwd()
_bm_cache    = None  # cache bookmarks

def log(action, details=""):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}]  {action}  |  {details}\n")

def confirmer(msg):
    console.print(f"[yellow]⚠  {escape(msg)}[/yellow]")
    console.print("[yellow]  Confirmer ? (o/n) :[/yellow] ", end="")
    return input().strip().lower() in ("o", "y", "oui", "yes")

def resoudre(chemin):
    bm = charger_bookmarks()
    if chemin in bm:
        return Path(bm[chemin])
    p = Path(chemin)
    return p if p.is_absolute() else cwd / p

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
    for u in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}To"

def pr(txt):
    console.print(txt)


def ollama_vivant():
    try:
        urllib.request.urlopen(OLLAMA_URL, timeout=3)
        return True
    except Exception:
        return False

def verifier_ollama():
    if not ollama_vivant():
        pr("[red]Ollama ne repond pas. Lance : ollama serve[/red]")
        return False
    return True

def appel_chat(messages, fmt_json=False):
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
        console.print(f"[red]Erreur Ollama : [/red]", end=""); console.print(str(e), markup=False)
        return ""

def cmd_cd(dest=""):
    global cwd
    if not dest:
        pr(str(cwd))
        return
    np = resoudre(dest)
    if not np.exists() or not np.is_dir():
        console.print(f"[red]Introuvable : {escape(str(np))}[/red]")
        return
    cwd = np.resolve()
    pr(f"[green]> {cwd}[/green]")
    log("cd", str(cwd))

def cmd_list(dossier=""):
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists():
        console.print(f"[red]Introuvable : {escape(str(dp))}[/red]")
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
            console.print(f"  {e.name}  (acces refuse)", markup=False)
    log("list", str(dp))

def cmd_find(motif, dossier=""):
    racine = resoudre(dossier) if dossier else cwd
    if not racine.exists():
        console.print(f"[red]Introuvable : {escape(str(racine))}[/red]")
        return
    LIMITE_AFFICHAGE = 500
    with Progress(SpinnerColumn(), TextColumn("[cyan]Recherche..."), transient=True) as prog:
        prog.add_task("")
        resultats = sorted(racine.rglob(motif))
    if not resultats:
        pr(f"[yellow]Aucun resultat : {motif}[/yellow]")
        return
    pr(f"[cyan]{len(resultats)} resultat(s) — {motif}[/cyan]")
    for r in resultats[:LIMITE_AFFICHAGE]:
        try:
            console.print(f"  {r}  {fmt_taille(r.stat().st_size)}", markup=False)
        except Exception:
            console.print(f"  {r}", markup=False)
    if len(resultats) > LIMITE_AFFICHAGE:
        pr(f"[dim]... {len(resultats)-LIMITE_AFFICHAGE} resultats supplementaires non affiches[/dim]")
    log("find", f"{motif} dans {racine}")

def _lire_pdf(fp):
    try:
        import pdfplumber
        with pdfplumber.open(str(fp)) as pdf:
            texte = "\n".join(p.extract_text() or "" for p in pdf.pages)
        return texte.strip() or "(PDF sans texte extractible)"
    except ImportError:
        return "(pip install pdfplumber pour lire les PDF)"
    except Exception as e:
        return f"(Erreur PDF : {e})"

def _lire_docx(fp):
    try:
        from docx import Document
        doc = Document(str(fp))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return "(pip install python-docx pour lire les DOCX)"
    except Exception as e:
        return f"(Erreur DOCX : {e})"

def cmd_read(chemin, limite=100):
    fp = resoudre(chemin)
    if not fp.exists():
        console.print(f"[red]Introuvable : {escape(str(fp))}[/red]")
        return
    ext = fp.suffix.lower()
    console.print(f"[cyan]-- {escape(fp.name)} --[/cyan]")
    try:
        if ext == ".pdf":
            texte = _lire_pdf(fp)
        elif ext == ".docx":
            texte = _lire_docx(fp)
        elif ext in (".csv", ".json", ".md", ".html", ".htm", ".xml",
                     ".txt", ".log", ".bat", ".py", ".js", ".ts", ".css"):
            texte = fp.read_text(encoding="utf-8", errors="replace")
        else:
            # Tentative UTF-8 generique
            try:
                texte = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                texte = f"(Format non pris en charge : {ext})"
        # Tronque si trop long
        lignes = texte.splitlines()
        if len(lignes) > limite:
            for l in lignes[:limite]:
                console.print(f"  {l}", markup=False)
            pr(f"[dim]... ({len(lignes)-limite} lignes de plus — read [fichier] [n] pour voir plus)[/dim]")
        else:
            for l in lignes:
                console.print(f"  {l}", markup=False)
        pr("[cyan]-- fin --[/cyan]")
        log("read", str(fp))
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_write(chemin, contenu=None):
    fp = resoudre(chemin)
    if contenu is None:
        pr("[dim]Saisir le contenu (terminer avec une ligne vide) :[/dim]")
        lignes = []
        try:
            while True:
                ligne = input()
                if ligne == "":
                    break
                lignes.append(ligne)
        except (KeyboardInterrupt, EOFError):
            pr("[dim]Annulé.[/dim]")
            return
        contenu = "\n".join(lignes)
    if not confirmer(f"Ecraser/creer {fp}"):
        return
    try:
        fp.write_text(contenu, encoding="utf-8")
        console.print(f"[green]OK {escape(str(fp))}[/green]")
        log("write", str(fp))
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_delete(chemin):
    fp = resoudre(chemin)
    if not fp.exists():
        console.print(f"[red]Introuvable : {escape(str(fp))}[/red]")
        return
    label = "dossier" if fp.is_dir() else "fichier"
    extra = " et tout son contenu" if fp.is_dir() else ""
    if not confirmer(f"Supprimer {label} {escape(fp.name)}{extra}"):
        return
    try:
        if fp.is_dir():
            shutil.rmtree(str(fp))
        else:
            fp.unlink()
        console.print(f"[green]Supprime : {escape(fp.name)}[/green]")
        log("delete", str(fp))
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def _glob_to_regex(motif):
    """Convertit un motif glob simple (*, ?) en regex avec groupe capturant."""
    parts = []
    for ch in motif:
        if ch == "*":
            parts.append("(.*)")
        elif ch == "?":
            parts.append("(.)")
        else:
            parts.append(re.escape(ch))
    return re.compile("^" + "".join(parts) + "$", re.IGNORECASE)

def _appliquer_motif(nom, pattern_src, pattern_dst):
    """Renvoie le nouveau nom ou None si le nom ne correspond pas."""
    m = pattern_src.match(nom)
    if not m:
        return None
    resultat = pattern_dst
    for i, groupe in enumerate(m.groups(), 1):
        resultat = resultat.replace("*", groupe, 1).replace("?", groupe, 1)
    return resultat

def cmd_rename(dossier, ancien, nouveau):
    d = resoudre(dossier)
    if not d.exists() or not d.is_dir():
        pr(f"[red]Dossier introuvable : {d}[/red]")
        return
    if not confirmer(f"Renommer '{ancien}' -> '{nouveau}' dans {d.name}"):
        return
    pattern_src = _glob_to_regex(ancien)
    cibles = [e for e in d.iterdir() if pattern_src.match(e.name)]
    if not cibles:
        pr("[yellow]Aucun fichier correspondant.[/yellow]")
        return
    for c in cibles:
        nouveau_nom = _appliquer_motif(c.name, pattern_src, nouveau)
        if not nouveau_nom:
            continue
        dest = c.parent / nouveau_nom
        c.rename(dest)
        console.print(f"[green]{escape(c.name)} -> {escape(str(nouveau_nom))}[/green]")
        log("rename", f"{c} -> {dest}")

def cmd_move(source, dest):
    src, dst = resoudre(source), resoudre(dest)
    if not src.exists():
        console.print(f"[red]Introuvable : {escape(str(src))}[/red]")
        return
    if not confirmer(f"Deplacer {src.name} vers {dst}"):
        return
    try:
        shutil.move(str(src), str(dst))
        console.print(f"[green]{escape(src.name)} -> {escape(str(dst))}[/green]")
        log("move", f"{src} -> {dst}")
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_duplicate(source, dest=""):
    src = resoudre(source)
    if not src.exists():
        console.print(f"[red]Introuvable : {escape(str(src))}[/red]")
        return
    dst = resoudre(dest) if dest else src.parent / f"{src.stem}_copie{src.suffix}"
    try:
        shutil.copy2(str(src), str(dst))
        console.print(f"[green]Copie -> {escape(str(dst))}[/green]")
        log("duplicate", f"{src} -> {dst}")
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_sort(dossier="", critere="taille", n="0"):
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists():
        console.print(f"[red]Introuvable : {escape(str(dp))}[/red]")
        return
    try:
        limit = int(n)
    except (ValueError, TypeError):
        limit = 0
    fichiers = [(str(e), e.stat().st_size, e.stat().st_mtime)
                for e in dp.iterdir() if e.is_file()]
    fichiers.sort(key=lambda x: x[2 if critere=="date" else 1], reverse=True)
    affichage = fichiers[:limit] if limit else fichiers
    titre = f"top {limit} " if limit else ""
    console.print(f"[cyan]{escape(str(dp))} — {titre}tri par {escape(critere)}[/cyan]")
    for chemin, taille, mtime in affichage:
        mod = datetime.fromtimestamp(mtime).strftime("%d/%m/%y")
        console.print(f"  {Path(chemin).name}  {fmt_taille(taille)}  {mod}", markup=False)
    log("sort", f"{dp} par {critere} n={limit}")

def cmd_open(chemin=""):
    fp = resoudre(chemin) if chemin else cwd
    if not fp.exists():
        console.print(f"[red]Introuvable : {escape(str(fp))}[/red]")
        return
    try:
        os.startfile(str(fp))
        console.print(f"[green]Ouvert : {escape(fp.name)}[/green]")
        log("open", str(fp))
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_clip(chemin=""):
    fp        = resoudre(chemin) if chemin else cwd
    chemin_abs = str(fp.resolve())
    try:
        subprocess.run(
            "clip",
            input=chemin_abs,
            text=True,
            encoding="utf-8",
            check=True,
            shell=False,          # pas de shell → pas d'injection
        )
        console.print(f"[green]Copie : {escape(chemin_abs)}[/green]")
        log("clip", chemin_abs)
    except Exception as e:
        console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)

def cmd_exec(commande):
    if not confirmer(f"Executer : {commande}"):
        return
    with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), transient=True) as prog:
        prog.add_task("Execution...")
        result = subprocess.run(commande, shell=True, capture_output=True,
                                cwd=str(cwd))
    # Décode la sortie en essayant cp850 (CMD Windows) puis utf-8
    def _decode(b):
        for enc in ("cp850", "cp1252", "utf-8"):
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
        console.print("[red]Erreur : [/red]", end=""); console.print(stderr, markup=False)
    log("exec", commande[:200])

def cmd_bookmark(action="list", nom="", chemin=""):
    bm = charger_bookmarks()
    if action == "list":
        if not bm:
            pr("[dim]Aucun favori.[/dim]")
            return
        for k, v in bm.items():
            console.print(f"  [cyan]{escape(k)}[/cyan]  {escape(v)}")
    elif action == "add":
        if not nom:
            pr("[red]Usage : bm add [nom] [chemin?][/red]")
            return
        cible = resoudre(chemin) if chemin else cwd
        bm[nom] = str(cible.resolve())
        sauver_bookmarks(bm)
        console.print(f"[green]'{escape(nom)}' -> {escape(str(cible.resolve()))}[/green]")
        log("bm_add", f"{nom}={cible}")
    elif action == "remove":
        if nom not in bm:
            console.print(f"[red]Inconnu : {escape(nom)}[/red]")
            return
        del bm[nom]
        sauver_bookmarks(bm)
        console.print(f"[green]Supprime : {escape(nom)}[/green]")
        log("bm_remove", nom)
    else:
        pr("[red]Usage : bm [list|add|remove] [nom][/red]")

def _executer_outil(cmd, args):
    """Execute un outil et capture + affiche sa sortie."""
    global console  # déclaré en tête de fonction, avant toute utilisation

    # exec : capture subprocess directement (pas besoin de Console)
    if cmd == "exec":
        commande = " ".join(args)
        result = subprocess.run(commande, shell=True, capture_output=True,
                                text=True, encoding=_enc, errors="replace", cwd=str(cwd))
        out = (result.stdout + result.stderr).strip()
        if out:
            console.print(out[:500], markup=False)
        log("agent_exec", commande[:200])
        return out[:1000] if out else "(pas de sortie)"

    # Autres commandes : Console temporaire dédiée au buffer
    buf      = io.StringIO()
    cap      = Console(file=buf, highlight=False, width=120, markup=False)

    # On substitue localement la référence dans le module courant
    _ancien_console = console
    console = cap
    try:
        dispatcher(cmd, args)
    finally:
        console = _ancien_console          # restauration garantie

    sortie = buf.getvalue().strip()
    if sortie:
        for ligne in sortie.splitlines()[:30]:
            _ancien_console.print(f"  {ligne}", markup=False)
    log("agent_tool", f"{cmd} {args}")
    return sortie[:1500] if sortie else "(commande executee)"


def cmd_agent(instruction):
    """Agent ReAct : Qwen raisonne, agit, observe, recommence."""
    if not verifier_ollama():
        return

    home      = Path.home()
    bureau    = home / "Desktop"
    downloads = home / "Downloads"
    MAX_STEPS = 8

    system = (
        "Tu es un assistant Windows. Pour agir, utilise UNIQUEMENT ces outils Fennec.\n"
        "JAMAIS de commandes Windows dans le champ cmd. Uniquement les noms d'outils ci-dessous.\n"
        "REGLES : fais le minimum d'etapes. Ne jamais ouvrir/lire sans demande explicite.\n"
        "Si echec, dis-le dans done. Arrete-toi des que la tache est accomplie.\n\n"
        "Outils disponibles (cmd = exactement ce nom) :\n"
        "  list      args:[dossier]                  -> liste fichiers et dossiers\n"
        "  find      args:[motif_glob, dossier]       -> cherche ex: *.pdf\n"
        "  sort      args:[dossier, taille|date]      -> trie par taille ou date\n"
        "  read      args:[fichier]                   -> lit un fichier\n"
        "  open      args:[chemin]                    -> ouvre avec l'app associee\n"
        "  exec      args:[commande_windows_complete] -> execute une commande Windows\n"
        "  delete    args:[fichier]                   -> supprime\n"
        "  move      args:[source, destination]       -> deplace\n"
        "  duplicate args:[source]                    -> copie\n"
        "  clip      args:[chemin]                    -> chemin dans presse-papier\n\n"
        "Format OBLIGATOIRE a chaque etape :\n"
        "{\"action\":\"tool\",\"cmd\":\"<NOM_OUTIL>\",\"args\":[\"arg1\"],\"reason\":\"...\"}\n"
        "Quand tu as la reponse finale :\n"
        "{\"action\":\"done\",\"answer\":\"ta reponse\"}\n\n"
        "EXEMPLES CORRECTS :\n"
        f"  liste bureau -> {{\"action\":\"tool\",\"cmd\":\"list\",\"args\":[\"{bureau}\"],\"reason\":\"lister\"}}\n"
        f"  trouve pdfs  -> {{\"action\":\"tool\",\"cmd\":\"find\",\"args\":[\"*.pdf\",\"{bureau}\"],\"reason\":\"chercher\"}}\n"
        f"  trie downloads -> {{\"action\":\"tool\",\"cmd\":\"sort\",\"args\":[\"{downloads}\",\"taille\"],\"reason\":\"trier\"}}\n"
        "  commande libre -> {\"action\":\"tool\",\"cmd\":\"exec\",\"args\":[\"dir C:\\\\Windows\"],\"reason\":\"...\"}\n\n"
        f"Chemins reels : bureau={bureau}  downloads={downloads}  cwd={cwd}\n"
    )

    messages = [
        {"role": "system",  "content": system},
        {"role": "user",    "content": instruction},
    ]

    console.print(f"[dim]Agent : {escape(instruction)}[/dim]")

    for etape in range(1, MAX_STEPS + 1):
        with Progress(SpinnerColumn(), TextColumn(f"[cyan]Qwen reflechit... (etape {etape}/{MAX_STEPS})"),
                      transient=True) as prog:
            prog.add_task("")
            raw = appel_chat(messages, fmt_json=True)

        if not raw:
            pr("[yellow]Pas de reponse de Qwen.[/yellow]")
            break

        # Parse JSON
        try:
            debut = raw.find("{")
            fin   = raw.rfind("}") + 1
            data  = json.loads(raw[debut:fin])
        except (json.JSONDecodeError, ValueError):
            # Reponse texte brute -> fin
            pr("[cyan]Qwen >[/cyan]")
            for ligne in raw.splitlines():
                console.print(f"  {ligne}", markup=False)
            log("agent_text", raw[:200])
            break

        action = data.get("action", "tool")

        # Reponse finale — refusee si aucun outil n'a encore ete utilise
        if action == "done":
            if etape == 1:
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content":
                    "NON. Tu ne peux pas repondre sans avoir utilise au moins un outil. "
                    "Utilise d'abord list, find, sort ou exec pour obtenir les vraies donnees du PC. "
                    "Reponds avec {\"action\":\"tool\",...} maintenant."})
                continue
            answer = data.get("answer", "")
            if answer:
                pr(f"[bold cyan]Qwen >[/bold cyan]")
                for ligne in answer.splitlines():
                    console.print(f"  {ligne}", markup=False)
                log("agent_done", answer[:200])
            break

        # Execution d'un outil
        cmd  = data.get("cmd", "")
        args = [str(a) for a in data.get("args", [])]
        reason = data.get("reason", "")

        if not cmd:
            pr("[yellow]Qwen n'a pas specifie de commande.[/yellow]")
            break

        _info = f"[dim]  [{etape}] {escape(str(cmd))}({escape(', '.join(args))})" + (f"  — {escape(str(reason))}" if reason else "") + "[/dim]"
        console.print(_info)

        # Confirmation pour actions dangereuses
        if cmd in ("delete", "move", "rename"):
            if not confirmer(f"Agent veut {cmd} {args}"):
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user",      "content": "Action refusee par l'utilisateur. Propose autre chose."})
                continue

        # Commandes reconnues uniquement — sinon on force exec
        if cmd not in AGENT_CMDS_VALIDES:
            pr(f"[dim]  -> commande inconnue, bascule vers exec[/dim]")
            cmd_reel = "exec"
            args_reel = [cmd + (" " + " ".join(args) if args else "")]
        else:
            cmd_reel, args_reel = cmd, args

        sortie = _executer_outil(cmd_reel, args_reel)

        # Feedback enrichi pour le prochain tour
        messages.append({"role": "assistant", "content": raw})
        if not sortie or sortie == "(commande executee)":
            feedback = f"Commande {cmd_reel} executee avec succes."
        else:
            feedback = f"Resultat de {cmd_reel}:\n{sortie}"

        # Apres delete/move/rename reussi -> forcer done immediatement
        if cmd_reel in ("delete", "move", "rename") and "Erreur" not in sortie:
            feedback += "\nTache accomplie. Reponds maintenant avec {\"action\":\"done\",\"answer\":\"<confirmation courte>\"}."

        messages.append({"role": "user", "content": feedback})
        log("agent_step", f"etape={etape} cmd={cmd} args={args}")

    else:
        pr(f"[yellow]Limite de {MAX_STEPS} etapes atteinte.[/yellow]")

# Mots-clés qui indiquent un besoin de données en temps réel
_WEB_KEYWORDS = {
    "météo", "meteo", "temperature", "température", "temps", "pluie", "soleil", "vent",
    "actualité", "actualite", "news", "aujourd'hui", "maintenant", "ce soir", "cette semaine",
    "prix", "tarif", "cours", "bourse", "bitcoin", "euro", "dollar",
    "score", "résultat", "résultats", "match", "classement",
    "horaire", "horaires", "ouvert", "fermé", "ferme",
    "trafic", "embouteillage", "grève", "greve",
    "sortie", "film", "concert", "événement", "evenement",
}

def _besoin_web(texte):
    """Retourne True si la question semble nécessiter des données en temps réel."""
    t = texte.lower()
    return any(kw in t for kw in _WEB_KEYWORDS)

def _web_context(query):
    """Scrape DuckDuckGo et retourne un résumé à injecter dans le contexte du chat."""
    try:
        resultats = _scrape_ddg(query)
        if not resultats:
            return ""
        parties = [f"- {titre} : {extrait[:200]}" for titre, lien, extrait in resultats[:4] if extrait]
        return ("Données web récupérées :\n" + "\n".join(parties)) if parties else ""
    except Exception:
        return ""


def cmd_chat():
    if not verifier_ollama():
        return
    pr("[green]-- Chat Qwen2.5  (exit pour quitter) --[/green]")
    historique = [
        {"role": "system", "content":
         "Tu es un assistant personnel utile et concis. RÈGLE ABSOLUE : réponds EXCLUSIVEMENT en français, sans exception. Jamais de chinois, d'anglais ou d'autre langue. Quand un [Contexte web] est fourni dans le message, utilise-le pour répondre avec précision. Sans contexte web, si tu ne connais pas une donnée en temps réel (météo, prix, score...), dis-le clairement et suggère d'utiliser la commande search. Ne jamais inventer des chiffres."}
    ]
    # Commandes Fennec directement exécutables depuis le chat
    CMDS_DIRECTES = {"search", "download", "install", "uninstall", "find",
                     "list", "ls", "read", "cat", "open", "exec", "clip",
                     "sort", "cd", "bm", "bookmark", "logs", "helpchat"}

    while True:
        try:
            console.print("[green]toi >[/green] ", end="")
            saisie = input().strip()
        except KeyboardInterrupt:
            pr("\n[dim]Retour a Fennec.[/dim]")
            break
        except EOFError:
            break
        if not saisie:
            continue
        if saisie.lower() in ("exit", "quit"):
            pr("[dim]Retour a Fennec.[/dim]")
            break

        # Détection commande Fennec -> exécution directe sans passer par Qwen
        try:
            tokens = shlex.split(saisie, posix=False)
        except ValueError:
            tokens = saisie.split()
        tokens = [t.strip("\"'") for t in tokens]
        if tokens and tokens[0].lower() in CMDS_DIRECTES:
            pr(f"[dim]-> commande Fennec détectée, exécution directe[/dim]")
            dispatcher(tokens[0].lower(), tokens[1:])
            continue

        # Enrichissement web si la question porte sur des données en temps réel
        contenu_user = saisie
        if _besoin_web(saisie):
            with Progress(SpinnerColumn(), TextColumn("[cyan]Recherche web..."), transient=True) as prog:
                prog.add_task("")
                ctx = _web_context(saisie)
            if ctx:
                contenu_user = saisie + "\n\n[Contexte web]\n" + ctx
                pr("[dim]  (données web injectées)[/dim]")
            else:
                pr("[dim]  (pas de résultat web, Qwen répond de mémoire)[/dim]")
        historique.append({"role": "user", "content": contenu_user})
        with Progress(SpinnerColumn(), TextColumn("[cyan]Qwen..."), transient=True) as prog:
            prog.add_task("")
            reponse = appel_chat(historique[-10:])
        if not reponse:
            pr("[dim]Pas de reponse. Retente.[/dim]")
            historique.pop()
            continue
        historique.append({"role": "assistant", "content": reponse})
        pr("[cyan]Qwen >[/cyan]")
        for ligne in reponse.splitlines():
            console.print(f"  {ligne}", markup=False)
        log("chat", saisie[:100])

GEEK_EXE = BASE_DIR / "geek.exe"

def cmd_uninstall(nom):
    """Desinstalle un programme via winget puis ouvre Geek Uninstaller pour nettoyer les restes."""
    if not nom:
        pr("[red]Usage: uninstall [nom du programme][/red]")
        return

    # Recherche dans la liste winget pour confirmer le nom exact
    console.print(f"[cyan]Recherche de '{escape(nom)}' dans winget...[/cyan]")
    result = subprocess.run(
        ["winget", "list", "--name", nom],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    lignes = [l for l in result.stdout.splitlines() if nom.lower() in l.lower()]
    if not lignes:
        console.print(f"[yellow]Aucun programme correspondant a '{escape(nom)}' dans winget.[/yellow]")
        pr("[dim]Essaie avec un nom plus court ou verifie dans : exec winget list[/dim]")
        return

    pr(f"[cyan]Programmes trouves :[/cyan]")
    for l in lignes:
        console.print(f"  {l}", markup=False)

    if not confirmer(f"Desinstaller '{nom}' via winget ?"):
        return

    pr(f"[cyan]Desinstallation en cours...[/cyan]")
    with Progress(SpinnerColumn(), TextColumn("[cyan]Desinstallation..."), transient=True) as prog:
        prog.add_task("")
        result = subprocess.run(
            ["winget", "uninstall", "--name", nom, "--silent"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

    if result.stdout:
        console.print(result.stdout.strip(), markup=False)
    if result.returncode != 0 and result.stderr:
        console.print("[red]Erreur : [/red]", end=""); console.print(result.stderr.strip(), markup=False)
        log("uninstall_error", f"{nom} : {result.stderr[:200]}")
        return

    console.print(f"[green]'{escape(nom)}' desinstalle.[/green]")
    log("uninstall", nom)

    # Nettoyage des restes avec Geek Uninstaller si disponible
    if GEEK_EXE.exists():
        pr(f"[cyan]Ouverture de Geek Uninstaller pour nettoyer les restes...[/cyan]")
        pr(f"[dim]  -> Fais clic droit sur le programme puis 'Scan for Leftovers'[/dim]")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(GEEK_EXE), None, str(BASE_DIR), 1
            )
            log("geek_uninstaller", nom)
        except Exception as e:
            console.print("[red]Impossible de lancer Geek Uninstaller : [/red]", end=""); console.print(str(e), markup=False)
    else:
        pr(f"[yellow]Conseil : place geek.exe a cote de fennec.py pour nettoyer les restes.[/yellow]")
        pr(f"[dim]  Telecharge sur https://geekuninstaller.com (gratuit, portable)[/dim]")


def _scrape_ddg(terme):
    """Scrape DuckDuckGo HTML et retourne une liste de (titre, lien, extrait)."""
    html_mod = _html
    url = f"https://html.duckduckgo.com/html/?q={urllib.request.quote(terme)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
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


def cmd_search(terme):
    """Recherche web DDG + synthèse Qwen + winget si logiciel."""
    if not terme:
        pr("[red]Usage: search [terme][/red]")
        return

    # ── Scraping DDG ──────────────────────────────────────────────────────────
    pr(f"[cyan]Recherche : {escape(terme)}[/cyan]")
    resultats = []
    try:
        resultats = _scrape_ddg(terme)
    except Exception as e:
        console.print("[yellow]Scraping indisponible ([/yellow]", end="")
        console.print(str(e), markup=False, end="")
        console.print("[yellow]). Ouverture navigateur...[/yellow]")
        try:
            os.startfile(f"https://duckduckgo.com/?q={urllib.request.quote(terme)}")
        except Exception:
            pass
        log("search", terme)
        return

    if not resultats:
        pr("[yellow]Aucun résultat. Ouverture navigateur...[/yellow]")
        os.startfile(f"https://duckduckgo.com/?q={urllib.request.quote(terme)}")
        log("search", terme)
        return

    # ── Synthèse Qwen à partir des extraits ───────────────────────────────────
    if ollama_vivant():
        contexte = "\n".join(
            f"[{i+1}] {titre}\n{extrait}"
            for i, (titre, lien, extrait) in enumerate(resultats)
            if extrait
        )
        messages = [
            {"role": "system", "content":
                "Tu es un assistant. À partir des extraits de recherche fournis, "
                "réponds directement à la question en français en 2-4 phrases max. "
                "Sois factuel, concis. Ne mentionne pas les sources par numéro. "
                "Si les extraits ne suffisent pas, dis-le honnêtement."},
            {"role": "user", "content":
                f"Question : {terme}\n\nExtraits de recherche :\n{contexte}"},
        ]
        with Progress(SpinnerColumn(), TextColumn("[cyan]Synthèse Qwen..."), transient=True) as prog:
            prog.add_task("")
            reponse = appel_chat(messages)
        if reponse:
            pr("[bold cyan]Réponse >[/bold cyan]")
            for ligne in reponse.splitlines():
                console.print(f"  {ligne}", markup=False)
            console.print("")

    # ── Affichage des sources ─────────────────────────────────────────────────
    pr("[dim]Sources :[/dim]")
    for i, (titre, lien, extrait) in enumerate(resultats, 1):
        console.print(f"  [bold]{i}.[/bold] {escape(titre)}", markup=True)
        console.print(f"     [dim]{escape(lien)}[/dim]", markup=True)

    # ── Winget si ça ressemble à un logiciel ──────────────────────────────────
    mots_logiciel = {"installer", "telecharger", "logiciel", "app", "programme",
                     "gratuit", "windows", "download", "software"}
    if any(m in terme.lower() for m in mots_logiciel):
        result = subprocess.run(
            ["winget", "search", terme],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        utiles = [l for l in result.stdout.strip().splitlines() if l.strip()][:6]
        if utiles and not any("Aucun" in l for l in utiles):
            pr("[dim]Winget :[/dim]")
            for l in utiles:
                console.print(f"  {l}", markup=False)

    log("search", terme)


def cmd_download(url, dest=""):
    """Telecharge un fichier depuis une URL vers cwd (ou dest)."""
    if not url:
        pr("[red]Usage: download [url] [dest?][/red]")
        return
    if not url.startswith(("http://", "https://")):
        pr("[red]URL invalide : doit commencer par http:// ou https://[/red]")
        return
    nom_fichier = Path(url.split("?")[0]).name or "fichier_telecharge"
    dest_path   = (resoudre(dest) if dest else cwd / nom_fichier)
    console.print(f"[cyan]Telechargement : {escape(url)}[/cyan]")
    console.print(f"[dim]  -> {escape(str(dest_path))}[/dim]")
    dest_path_tmp = dest_path.with_suffix(dest_path.suffix + ".tmp")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Fennec/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            taille_totale = int(resp.headers.get("Content-Length", 0))
            taille_lue    = 0
            BLOC          = 65536
            with open(dest_path_tmp, "wb") as f:
                while True:
                    bloc = resp.read(BLOC)
                    if not bloc:
                        break
                    f.write(bloc)
                    taille_lue += len(bloc)
                    if taille_totale:
                        pct = min(100, int(taille_lue * 100 / taille_totale))
                        print(f"\r  {pct}%  {fmt_taille(taille_lue)} / {fmt_taille(taille_totale)}   ", end="", flush=True)
        print()
        dest_path_tmp.replace(dest_path)
        console.print(f"[green]Telecharge : {escape(dest_path.name)}  ({fmt_taille(dest_path.stat().st_size)})[/green]")
        log("download", f"{url} -> {dest_path}")
    except Exception as e:
        if dest_path_tmp.exists():
            dest_path_tmp.unlink(missing_ok=True)
        console.print(f"[red]Erreur telechargement : [/red]", end=""); console.print(str(e), markup=False)
        log("download_error", str(e))


def cmd_install(nom):
    """Recherche et installe un programme via winget."""
    if not nom:
        pr("[red]Usage: install [programme][/red]")
        return
    console.print(f"[cyan]Recherche de '{escape(nom)}' dans winget...[/cyan]")
    result = subprocess.run(
        ["winget", "search", nom],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    lignes = [l for l in result.stdout.strip().splitlines() if l.strip()]
    if not lignes:
        console.print(f"[yellow]Aucun resultat pour '{escape(nom)}'.[/yellow]")
        return
    for l in lignes[:10]:
        console.print(f"  {l}", markup=False)
    if not confirmer(f"Installer '{escape(nom)}' via winget ?"):
        return
    pr("[cyan]Installation en cours...[/cyan]")
    with Progress(SpinnerColumn(), TextColumn("[cyan]Installation..."), transient=True) as prog:
        prog.add_task("")
        result = subprocess.run(
            ["winget", "install", "--name", nom, "--silent",
             "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    if result.stdout:
        console.print(result.stdout.strip(), markup=False)
    if result.returncode != 0:
        if result.stderr:
            console.print("[red]Erreur : [/red]", end=""); console.print(result.stderr.strip(), markup=False)
        pr("[yellow]Astuce : essaie avec l'ID exact (ex: install VideoLAN.VLC)[/yellow]")
        log("install_error", nom)
        return
    console.print(f"[green]'{escape(nom)}' installe avec succes.[/green]")
    log("install", nom)


def cmd_redate(dossier="", mode="creation"):
    """Renomme tous les fichiers d'un dossier par date+numero : 2024_01, 2024_02..."""
    dp = resoudre(dossier) if dossier else cwd
    if not dp.exists() or not dp.is_dir():
        console.print(f"[red]Dossier introuvable : {escape(str(dp))}[/red]")
        return

    # Liste uniquement les fichiers (pas les sous-dossiers)
    fichiers = [e for e in dp.iterdir() if e.is_file()]
    if not fichiers:
        pr("[yellow]Aucun fichier dans ce dossier.[/yellow]")
        return

    # Recupere la date selon le mode (creation ou modification)
    def get_date(f):
        st = f.stat()
        ts = st.st_ctime if mode == "creation" else st.st_mtime
        return datetime.fromtimestamp(ts)

    # Trie par date
    fichiers.sort(key=get_date)

    # Construit les nouveaux noms : groupe par annee, compteur par annee
    plan = []
    compteurs = {}
    for f in fichiers:
        d     = get_date(f)
        annee = str(d.year)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        numero    = compteurs[annee]
        nouveau   = f"{annee}_{numero:02d}{f.suffix.lower()}"
        plan.append((f, dp / nouveau))

    # Affiche le plan avant confirmation
    pr(f"[cyan]Plan de renommage ({len(plan)} fichiers) — date de {mode} :[/cyan]")
    for src, dst in plan[:20]:
        console.print(f"  {src.name:<40} -> {dst.name}", markup=False)
    if len(plan) > 20:
        pr(f"[dim]  ... et {len(plan)-20} autres[/dim]")

    if not confirmer(f"Renommer {len(plan)} fichiers dans {dp.name} ?"):
        return

    # Passe 1 : renomme vers des noms temporaires pour eviter les collisions
    tmp_plan = []
    try:
        for src, dst in plan:
            tmp = src.parent / (src.name + ".redate_tmp")
            src.rename(tmp)
            tmp_plan.append((tmp, dst))
    except (KeyboardInterrupt, Exception) as _e:
        for tmp, _ in tmp_plan:
            try: tmp.rename(tmp.parent / tmp.name.removesuffix(".redate_tmp"))
            except Exception: pass
        pr("[yellow]Interruption — fichiers restaures.[/yellow]")
        return

    # Passe 2 : renomme vers les noms finaux
    erreurs = 0
    for tmp, dst in tmp_plan:
        try:
            # Si le nom final existe deja, ajoute un suffixe
            final = dst
            if final.exists():
                final = dst.parent / f"{dst.stem}_dup{dst.suffix}"
            tmp.rename(final)
            console.print(f"[green]  {escape(final.name)}[/green]")
        except Exception as e:
            console.print("[red]  Erreur : [/red]", end=""); console.print(f"{escape(tmp.name)} -> {escape(dst.name)} : {escape(str(e))}", markup=False)
            erreurs += 1

    pr(f"[bold green]{len(plan) - erreurs} fichiers renommes.[/bold green]")
    if erreurs:
        pr(f"[red]{erreurs} erreur(s).[/red]")
    log("redate", f"{dp} mode={mode} n={len(plan)}")


# ── Documentation intégrée pour helpchat ─────────────────────────────────────
FENNEC_DOC = r"""
Fennec est un shell de gestion de fichiers Windows assisté par IA (Qwen2.5:7b via Ollama).
Tu es le bot d'aide de Fennec. Réponds uniquement sur son fonctionnement. Sois concis et donne des exemples concrets.

=== NAVIGATION ===
cd [dossier]        : Change de dossier. Sans argument, affiche le dossier actuel.
                      Exemples : cd Desktop   cd ..   cd "C:\Users\<nom>\Documents"
                      Le . désigne le dossier courant, .. le dossier parent.
                      Tu peux aussi utiliser un nom de favori (bm) à la place d'un chemin.

list [dossier?]     : Liste les fichiers et dossiers. Dossiers en bleu avec /.
ls                  : Alias de list.
                      Exemples : list   list Desktop   list "C:\Users\<nom>"

sort [dossier?] [taille|date] : Trie les fichiers par taille (défaut) ou par date de modification.
                      Exemples : sort   sort . date   sort Downloads taille

find [motif] [dossier?] : Recherche récursive par motif glob dans le dossier (ou cwd).
                      Exemples : find *.pdf   find rapport* Documents   find *.jpg Downloads

=== FICHIERS ===
read [fichier]      : Lit et affiche le contenu d'un fichier (max 100 lignes).
cat                 : Alias de read.
                      Supporte : .txt .py .js .csv .json .md .html .bat .log .xml .css
                      Supporte aussi : .pdf (pdfplumber) et .docx (python-docx) si installés.
                      Exemples : read notes.txt   read "C:\rapport.pdf"

write [fichier] [texte?] : Écrit du texte dans un fichier (crée ou écrase). Demande confirmation.
                      Sans texte : passe en mode interactif (une ligne vide pour finir).
                      Exemples : write notes.txt Bonjour monde
                                 write notes.txt   (puis saisie interactive multiligne)

delete [fichier]    : Supprime un fichier. Demande confirmation. ! = dangereux.
del / rm            : Alias de delete.
                      Exemple : delete vieux_fichier.txt

rename [dossier] [ancien] [nouveau] : Renommage en masse avec motifs glob. Demande confirmation.
                      Le * capture la partie variable et la réinjecte.
                      Exemples :
                        rename . * 2024_*              -> ajoute préfixe 2024_ à tout
                        rename . *.jpg *.jpeg          -> change l'extension
                        rename . rapport_* note_*      -> remplace un mot
                        rename Photos *.JPG *.jpg      -> normalise en minuscules
                        rename . facture_2023_* facture_2024_*  -> change une partie

move [source] [dest] : Déplace un fichier ou dossier. Demande confirmation.
mv                  : Alias de move.
                      Exemples : move rapport.pdf Archives   move . Archives/rapport.pdf

duplicate [source] [dest?] : Copie un fichier. Sans dest, crée un _copie dans le même dossier.
cp / copy           : Alias de duplicate.
                      Exemples : duplicate rapport.pdf   duplicate rapport.pdf Archives/

=== SYSTÈME ===
open [chemin?]      : Ouvre un fichier ou dossier avec l'application associée Windows.
                      Sans argument : ouvre le dossier courant dans l'Explorateur.
                      Exemples : open rapport.pdf   open .   open "C:\Users\<nom>\Desktop"
                      DIFFÉRENCE avec read : open lance l'appli Windows (Word, VLC...), read affiche le texte brut dans le terminal.

clip [chemin?]      : Copie le chemin absolu dans le presse-papier Windows.
                      Exemples : clip   clip rapport.pdf

exec [commande]     : Exécute n'importe quelle commande CMD Windows. Demande confirmation.
                      Exemples : exec dir C:\Windows   exec ipconfig   exec python script.py
                      DIFFÉRENCE avec open : exec lance une commande texte, open ouvre avec l'appli associée.

=== WEB & INSTALLATION ===
search [terme]      : Recherche dans winget (logiciels installables) ET sur DuckDuckGo.
                      Si pas de résultat web, ouvre le navigateur.
                      Exemples : search VLC   search convertisseur video   search python

download [url] [dest?] : Télécharge un fichier avec barre de progression.
                      Sans dest : enregistre dans le dossier courant.
                      Exemples : download https://exemple.com/fichier.zip
                                 download https://exemple.com/app.exe Telechargements/

install [programme] : Cherche dans winget, affiche les résultats, installe après confirmation.
                      Astuce : utilise l'ID exact pour plus de précision.
                      Exemples : install VLC   install VideoLAN.VLC   install 7zip   install Git

uninstall [programme] : Désinstalle via winget puis ouvre Geek Uninstaller (geek.exe) pour nettoyer les restes du registre.
                      Place geek.exe dans le même dossier que fennec.py (geekuninstaller.com, gratuit).
                      Exemple : uninstall AnyDesk

=== FAVORIS ===
bm list             : Liste les favoris enregistrés.
bm add [nom] [chemin?] : Enregistre le dossier courant (ou le chemin donné) sous un nom court.
bm remove [nom]     : Supprime un favori.
bookmark            : Alias de bm.
                      Une fois ajouté, utilise le nom comme un chemin dans cd, list, read...
                      Exemples : bm add projets C:\Dev\Projets
                                 cd projets   list projets   find *.py projets

=== IA ===
agent [instruction] : Qwen analyse ta demande, choisit les outils Fennec et agit étape par étape (max 8 étapes).
                      Confirmation demandée pour delete/move/rename.
                      Exemples : agent liste les 5 fichiers les plus lourds du bureau
                                 agent trouve tous les PDF dans Downloads et dis combien il y en a
                                 agent supprime les fichiers .tmp du bureau

chat                : Conversation libre avec Qwen2.5. Garde les 10 derniers messages en mémoire.
                      Tape exit pour revenir à Fennec.

helpchat [question] : Tu y es ! Pose une question sur le fonctionnement de Fennec.

=== DIVERS ===
logs [n?]           : Affiche les n dernières actions enregistrées (défaut : 30).
help                : Affiche la liste des commandes.
exit / quit / q     : Quitte Fennec.

=== ASTUCES ===
- Tab : autocomplétion des commandes et des chemins.
- Historique : flèches haut/bas pour rappeler les commandes précédentes.
- Chemins avec espaces : utilise des guillemets -> cd "Mon Dossier"
- Commande inconnue : Fennec la tente directement comme commande Windows.
- Les commandes marquées ! demandent toujours une confirmation avant d'agir.
- Le . désigne toujours le dossier courant, .. le dossier parent.
"""


def cmd_helpchat(question):
    """Mini bot d'aide sur le fonctionnement de Fennec, propulsé par Qwen."""
    if not question:
        pr("[red]Usage: helpchat [question][/red]")
        pr("[dim]Exemples : helpchat comment renommer des photos[/dim]")
        pr("[dim]           helpchat difference entre exec et open[/dim]")
        return
    if not verifier_ollama():
        return

    messages = [
        {"role": "system", "content":
            "Tu es le bot d'aide intégré de Fennec, un shell Windows assisté par IA. "
            "Utilise uniquement la documentation ci-dessous pour répondre. "
            "Sois concis, direct, et donne toujours un exemple concret de commande. "
            "Réponds en français.\n\n"
            "=== DOCUMENTATION FENNEC ===\n" + FENNEC_DOC},
        {"role": "user", "content": question},
    ]

    with Progress(SpinnerColumn(), TextColumn("[cyan]Qwen cherche dans la doc..."), transient=True) as prog:
        prog.add_task("")
        reponse = appel_chat(messages)

    if not reponse:
        pr("[yellow]Pas de réponse.[/yellow]")
        return

    pr("[bold cyan]Aide >[/bold cyan]")
    for ligne in reponse.splitlines():
        console.print(f"  {ligne}", markup=False)
    log("helpchat", question[:100])


def cmd_logs(n=30):
    if not LOG_FILE.exists():
        pr("[dim]Aucun log.[/dim]")
        return
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        lignes = f.readlines()
    for ligne in lignes[-n:]:
        console.print(f"[dim]{escape(ligne.rstrip())}[/dim]")

def cmd_help():
    lignes = [
        ("cd",        "[dossier]",                    "Changer de dossier"),
        ("list",      "[dossier?]",                   "Lister les fichiers"),
        ("find",      "[*.ext] [dossier?]",           "Recherche recursive"),
        ("sort",      "[dossier?] [taille|date]",     "Trier"),
        ("read",      "[fichier]",                    "Lire un fichier"),
        ("write",     "[fichier] [texte?]",           "Ecrire (texte ou mode interactif) !"),
        ("delete",    "[fichier]",                    "Supprimer  !"),
        ("rename",    "[dossier] [ancien] [nouveau]", "Renommer en masse  !"),
        ("move",      "[source] [dest]",              "Deplacer  !"),
        ("duplicate", "[source] [dest?]",             "Copier"),
        ("open",      "[chemin?]",                    "Ouvrir avec app associee"),
        ("clip",      "[chemin?]",                    "Chemin dans presse-papier"),
        ("exec",      "[commande]",                   "Executer commande CMD  !"),
        ("redate",    "[dossier?] [creation|modif]",   "Renommer par date+numero  !"),
        ("search",    "[terme]",                       "Recherche web + winget"),
        ("download",  "[url] [dest?]",                  "Telecharger un fichier"),
        ("install",   "[programme]",                   "Installer via winget  !"),
        ("uninstall", "[programme]",                  "Desinstaller + nettoyage (Geek)  !"),
        ("bm",        "[list|add|remove] [nom]",      "Favoris"),
        ("agent",     "[instruction]",                "Qwen agit sur tes fichiers"),
        ("helpchat",  "[question]",                   "Bot d'aide sur Fennec"),
        ("chat",      "",                             "Conversation avec Qwen"),
        ("logs",      "[n=30]",                       "Derniers logs"),
        ("help",      "",                             "Cette aide"),
        ("exit",      "",                             "Quitter"),
    ]
    pr("[cyan]-- Fennec commandes --[/cyan]")
    for cmd, args, desc in lignes:
        pr(f"  [bold]{cmd:<12}[/bold][dim]{args:<35}[/dim] {desc}")
    pr("[dim]  ! = confirmation requise[/dim]")

def dispatcher(cmd, args):
    def a(i, d=None): return args[i] if len(args) > i else d
    match cmd:
        case "cd":                   cmd_cd(a(0,""))
        case "list"|"ls":            cmd_list(a(0,""))
        case "find":                 cmd_find(a(0,"*"),a(1,"")) if args else pr("[red]Usage: find [motif][/red]")
        case "read"|"cat":
            if not args: pr("[red]Usage: read [fichier] [lignes?][/red]")
            else:
                try: lim = int(a(1, 100))
                except: lim = 100
                cmd_read(a(0), lim)
        case "write":                cmd_write(a(0), " ".join(args[1:]) if len(args) >= 2 else None) if args else pr("[red]Usage: write [fichier] [texte?][/red]")
        case "delete"|"del"|"rm":    cmd_delete(a(0)) if args else pr("[red]Usage: delete [fichier][/red]")
        case "rename":
            if len(args) < 2:
                pr("[red]Usage : rename [motif_ancien] [motif_nouveau] (dans cwd)[/red]")
                pr("[dim]       rename [dossier] [motif_ancien] [motif_nouveau][/dim]")
                pr("[dim]Exemple : rename C:/photos *.JPG *.jpg[/dim]")
                pr("[dim]Exemple : rename . rapport_* note_*[/dim]")
            elif len(args) == 2: cmd_rename(".", a(0), a(1))
            else: cmd_rename(a(0), a(1), a(2))
        case "move"|"mv":            cmd_move(a(0),a(1)) if len(args)>=2 else pr("[red]Usage: move [source] [dest][/red]")
        case "duplicate"|"cp"|"copy":cmd_duplicate(a(0),a(1,"")) if args else pr("[red]Usage: duplicate [source][/red]")
        case "sort":                 cmd_sort(a(0,""),a(1,"taille"),a(2,"0"))
        case "open":                 cmd_open(a(0,""))
        case "clip":                 cmd_clip(a(0,""))
        case "redate":               cmd_redate(a(0,""), a(1,"creation"))
        case "search":               cmd_search(" ".join(args)) if args else pr("[red]Usage: search [terme][/red]")
        case "download":             cmd_download(a(0,""),a(1,"")) if args else pr("[red]Usage: download [url][/red]")
        case "install":              cmd_install(" ".join(args)) if args else pr("[red]Usage: install [programme][/red]")
        case "uninstall":            cmd_uninstall(" ".join(args)) if args else pr("[red]Usage: uninstall [programme][/red]")
        case "exec":                 cmd_exec(" ".join(args)) if args else pr("[red]Usage: exec [commande][/red]")
        case "bookmark"|"bm":        cmd_bookmark(a(0,"list"),a(1,""),a(2,""))
        case "agent":                cmd_agent(" ".join(args)) if args else pr("[red]Usage: agent [instruction][/red]")
        case "helpchat":             cmd_helpchat(" ".join(args)) if args else pr("[red]Usage: helpchat [question][/red]")
        case "chat":                 cmd_chat()
        case "logs":                 cmd_logs(int(args[0]) if args else 30)
        case "help"|"?":             cmd_help()
        case "exit"|"quit"|"q":      raise SystemExit
        case _:
            # Commande inconnue -> tente comme exec Windows
            cmd_exec(cmd + (" " + " ".join(args) if args else ""))

def label():
    try:
        rel = cwd.relative_to(Path.home())
        s = ("~/" + str(rel).replace("\\", "/")) if str(rel) != "." else "~"
    except ValueError:
        s = str(cwd)
    return ("..." + s[-35:]) if len(s) > 38 else s

from prompt_toolkit.key_binding import KeyBindings as _KB

def _make_bindings():
    """Tab = valider/insérer la complétion. Pas d'espace cassant."""
    kb = _KB()

    @kb.add("tab")
    def _tab(event):
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.apply_completion(buf.complete_state.current_completion)
        else:
            buf.start_completion(select_first=True)

    return kb

# ── Autocomplétion contextuelle ──────────────────────────────────────────────
CMDS_CHEMIN = {"cd", "list", "ls", "find", "read", "cat", "write", "delete",
               "rm", "move", "mv", "duplicate", "cp", "open", "clip", "exec",
               "sort", "rename", "bm"}
CMDS_TOUTES = ["cd","list","ls","find","read","cat","write","delete","rm",
               "rename","move","mv","duplicate","cp","sort","open","clip",
               "exec","redate","search","download","install","uninstall","bookmark","bm","agent","helpchat","chat","logs","help","exit"]

class FennecCompleter(Completer):
    """Propose les commandes en début de ligne, les chemins du cwd ensuite."""

    def get_completions(self, document, complete_event):
        texte = document.text_before_cursor
        try:
            tokens = shlex.split(texte, posix=False)
        except ValueError:
            tokens = texte.split()

        if not tokens or (len(tokens) == 1 and not texte.endswith(" ")):
            prefix = tokens[0].lower() if tokens else ""
            for cmd in CMDS_TOUTES:
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
            fragment = tokens[-1]
            fragment = fragment.strip('"\'')
            p = Path(fragment)
            if p.is_absolute():
                base_dir = p.parent if not fragment.endswith(("/", "\\")) else p
            else:
                base_dir = (cwd / p).parent if not fragment.endswith(("/", "\\")) else cwd / p

        try:
            entries = sorted(base_dir.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except (PermissionError, OSError):
            return

        for entry in entries:
            nom = entry.name
            typed_name = Path(fragment).name if fragment and not fragment.endswith(("/", "\\")) else ""
            if typed_name and not nom.lower().startswith(typed_name.lower()):
                continue
            display = nom + ("/" if entry.is_dir() else "")
            if fragment:
                if fragment.endswith(("/", "\\")):
                    insert = nom + ("/" if entry.is_dir() else "")
                    start = 0
                else:
                    insert = nom + ("/" if entry.is_dir() else "")
                    start = -len(Path(fragment).name)
            else:
                insert = nom + ("/" if entry.is_dir() else "")
                start = 0
            full_path = str(base_dir / nom)
            if " " in full_path:
                insert = f'"{full_path}{"/" if entry.is_dir() else ""}"'
                last_token_len = len(tokens[-1]) if not texte.endswith(" ") else 0
                start = -last_token_len
            yield Completion(
                insert,
                start_position=start,
                display=display,
                display_meta="[dir]" if entry.is_dir() else ""
            )

def main():
    global cwd
    completer = FennecCompleter()
    session = PromptSession(
        history=FileHistory(str(HIST_FILE)),
        completer=completer,
        complete_while_typing=False,
        complete_in_thread=True,
        style=Style.from_dict({"prompt": "bold ansicyan"}),
        key_bindings=_make_bindings(),
    )
    pr("[bold cyan]Fennec[/bold cyan]  [dim]agent[/dim] pour agir  [dim]chat[/dim] pour discuter  [dim]help[/dim] pour la liste")
    log("startup")
    while True:
        try:
            saisie = session.prompt(HTML(f"<prompt>{label()} > </prompt>")).strip()
            if not saisie:
                continue
            try:
                tokens = shlex.split(saisie, posix=False)
            except ValueError:
                tokens = saisie.split()
            tokens = [t.strip("\"'") for t in tokens]
            dispatcher(tokens[0].lower(), tokens[1:])
        except KeyboardInterrupt:
            pr("\n[dim]Ctrl+C — tape exit pour quitter.[/dim]")
        except EOFError:
            break
        except SystemExit:
            pr("[dim]Au revoir.[/dim]")
            log("shutdown")
            break
        except Exception as e:
            console.print(f"[red]Erreur : [/red]", end=""); console.print(str(e), markup=False)
            log("error", str(e))

if __name__ == "__main__":
    main()