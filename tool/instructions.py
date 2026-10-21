"""Does everything the instructions name still exist? A renamed command, flag, file or function then
fails the self-test, not a session that trusts the instructions.

    python -m tool.instructions                 prints what's missing, or one line: all present
    python -m tool.instructions --root <folder>  the same for a concept's repo: its docs against its own package
                                                 (the Lab's lab/, its page/) and the tools'

The self-test runs it on the working tree. The instructions are what a session reads: CLAUDE.md,
RULES.md, the queue (IMPROVEMENTS.md), the rules, skills and agents in .claude/, the car in words
(car/anatomy.md), and the hooks in .claude/settings.json. What each names, in backticks:

- a command (`PY -m tool.snap <name> --cams`, `tool.close <name>`): its module, and the word after
  it and every flag as strings in the module's code. A flag alone (`--before`), or a word and what
  it takes (`tile "<words>"`), belongs to the last command named in the same paragraph, list item
  or table row.
- a file or folder (`tool/skin.py`, `skins/<name>/design.py`, `viewer.js`): it exists, `<...>` and
  `*` matching anything, a bare file name anywhere in the repo, `../` beside it (a concept naming the
  tools' files); one the tool makes as it runs (`build/<name>_views.png`, `/api/health`) has its
  fixed words in the tool's code.
- a name in the code (`paintbox.Skin`, `Skin.step`, `s.scatter`, `parts.load().mask`): each step
  is defined there (read with ast, nothing imported). `X` in `file` (`SPOTS` in `tool/paintbox.py`):
  the file holds the word. A setting (`TSC_PAINTS=<n>`): the code reads it.

Anything else in backticks (the game's file names, words to say) isn't checked. Standard library
only.
"""

import ast
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
READ = ("CLAUDE.md", "RULES.md", "IMPROVEMENTS.md", ".claude/rules/*.md", ".claude/skills/*/*.md",
        ".claude/agents/*.md", "car/anatomy.md")
CODE = ("tool/*.py", "viewer/*.js", "viewer/*.html")  # the tools' code; a concept's is its package and its page
CONCEPT = {"lab": ("lab/*.py", "page/*.js", "page/*.html")}
FILE = re.compile(r"\.(?:md|py|js|json|html|png|jpg|txt|zip|tga|lock|rar|css)$")
SPAN = re.compile(r"`([^`]+)`")
COMMAND = re.compile(r"(?:^|\s)(?:PY|python) -m (tool|lab)\.(\w+)(.*)|^(tool|lab)\.(\w+)(.*)")
FLAG = re.compile(r"(?<![\w-])(--?[a-z][\w-]*)")
CHAIN = re.compile(r"(?<![\w.])([A-Za-z_]\w*)((?:\.[A-Za-z_]\w*|\([^()]*\))+)")


class Code:
    """The code the instructions may name, read once: each package's modules (the tools' tool/, and a concept's own
    package under its root), each module's names, its strings, and every class's names."""

    def __init__(self, root):
        self.root = root
        self.packages = {"tool": REPO / "tool"}
        self.packages.update({k: root / k for k in CONCEPT if (root / k).is_dir()})
        self.stems = {k: {p.stem for p in folder.glob("*.py")} for k, folder in self.packages.items()}  # the Mac's disk ignores case
        self.modules, self.classes = {}, {}
        patterns = [(REPO, p) for p in CODE] + [(root, p) for k in self.packages if k != "tool" for p in CONCEPT[k]]
        self.text = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                              for base, pattern in patterns for p in sorted(base.glob(pattern)))
        # the repo's own folders, not the ones git leaves out: a file named in one must be there
        ignore = root / ".gitignore"
        left_out = set(re.findall(r"^/?([^\s/*]+)/$", ignore.read_text(encoding="utf-8"), re.M)) if ignore.exists() else set()
        self.kept = {p.name for p in root.iterdir() if p.is_dir() and p.name not in left_out | {".git"}}
        self.zipped = set()  # the files in Nadeo's and the model's zips (resources/official/), by name
        for z in root.glob("resources/official/*.zip"):
            with zipfile.ZipFile(z) as f:
                self.zipped |= {Path(n).name for n in f.namelist()}

    def module(self, name, package=None):
        """{"names", "strings", "classes": {name: its names}}, or None when there's no <package>/<name>.py; without a
        package, the concept's module of that name first, then the tools'."""
        for pkg in ([package] if package else [k for k in self.packages if k != "tool"] + ["tool"]):
            if name in self.stems.get(pkg, ()):
                break
        else:
            return None
        key = f"{pkg}/{name}"
        if key not in self.modules:
            self.modules[key] = read(self.packages[pkg] / f"{name}.py")
            for cls, names in self.modules[key]["classes"].items():
                self.classes.setdefault(cls, set()).update(names)
        return self.modules[key]

    def every_class(self):
        for pkg, stems in self.stems.items():
            for stem in sorted(stems):
                self.module(stem, pkg)
        return self.classes


def read(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names, strings, classes = set(), set(), {}
    for node in tree.body:
        names |= defined(node)
        if isinstance(node, ast.ClassDef):
            classes[node.name] = set().union(*(defined(n) for n in node.body)) | {
                t.attr for n in ast.walk(node) if isinstance(n, (ast.Assign, ast.AnnAssign))
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return {"names": names, "strings": strings, "classes": classes}


def defined(node):
    """The names a statement at a module's or a class's top level defines."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {(a.asname or a.name).split(".")[0] for a in node.names}
    if isinstance(node, (ast.If, ast.Try)):
        return set().union(*(defined(n) for n in node.body + getattr(node, "orelse", [])))
    return set()


def spans(text):
    """(line, the text in backticks, the block it's in) for every span. A block is a paragraph, a
    list item or a table row: a flag alone belongs to the command named before it in its block."""
    block, start, out = [], 1, []

    def close():
        joined = "\n".join(block)
        for m in SPAN.finditer(joined):
            out.append((start + joined.count("\n", 0, m.start()), " ".join(m.group(1).split()), start))

    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip() or re.match(r"\s*([-*]|\d+\.)\s|\||#", line):
            close()
            block, start = [], i
        if line.strip():
            block.append(line)
    close()
    return out


def check(root=REPO):
    """(how many things the instructions name, by kind; what's missing: [(where, what, why)])."""
    code, counts, missing = Code(root), {"commands": 0, "files": 0, "names": 0}, []
    for where, kind, s, why in named(root, code):
        counts[kind] += 1
        if why:
            missing.append((where, s, why))
    return counts, missing


def named(root, code):
    """(where, kind, what, why it's missing or None) for everything the instructions name."""
    for doc in [p for pattern in READ for p in sorted(root.glob(pattern))]:
        where = doc.relative_to(root).as_posix()
        text = doc.read_text(encoding="utf-8")
        head = re.match(r"---\n(.*?)\n---", text, re.S)  # a rule loads with the files its paths: match
        for pattern in re.findall(r'^\s*-\s*"([^"]+)"', head.group(1) if head else "", re.M):
            yield where, "files", f"paths: {pattern}", None if next(root.glob(pattern), None) else "matches nothing"
        last = {}  # block -> (the package, the module) the last command in it named
        for line, s, block in spans(text):
            for kind, why in name(s, code, last, block):
                yield f"{where}:{line}", kind, s, why
        for m in re.finditer(r"`(\w+)`\s+in\s+`([^`]+)`", text):
            word, target = m.groups()
            if (root / target).is_file():
                said = re.search(rf"\b{word}\b", (root / target).read_text(encoding="utf-8", errors="replace"))
                yield (f"{where}:{text.count(chr(10), 0, m.start()) + 1}", "names", f"{word}` in `{target}",
                       None if said else f"{target} doesn't say {word}")
    yield from hooks(root)


def name(s, code, last, block):
    """(kind, why it's missing or None) for each thing one span names."""
    m = COMMAND.search(s)
    if m:
        pkg, module, rest = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(4), m.group(5), m.group(6))
        last[block] = (pkg, module)
        yield "commands", command(pkg, module, rest, code)
        return
    if re.fullmatch(r"--?[a-z][\w-]*(?: <\w+>)?|[a-z]+ (?:<|\"|--|\[).*", s):
        if block in last:
            yield "commands", command(*last[block], " " + s, code)
        return
    if re.match(r"[A-Z][A-Z0-9_]+=", s):
        yield "names", None if s.split("=")[0] in code.text else "the tool's code never reads it"
        return
    if s.startswith("/"):
        yield "files", None if made(s, code, url=True) else "the tool's code never serves it"
        return
    if s.startswith("../"):  # a concept's docs name the tools' files by their place beside it
        pattern = re.sub(r"<[^>]*>", "*", s.split("?")[0][3:]).rstrip("/")
        yield "files", None if next((code.root / "..").glob(pattern), None) else "no such file beside this repo"
        return
    if path_like(s, code.root):
        yield "files", place(s, code)
        return
    for m in CHAIN.finditer(s):
        why = chain(m.group(1), m.group(2), code)
        if why is not False:
            yield "names", why


def command(pkg, module, rest, code):
    found = code.module(module, pkg)
    if found is None:
        return f"there's no {pkg}/{module}.py"
    lost = []
    sub = re.match(r"\s+([a-z][a-z_]*)(?=\s|$)", rest)
    if sub and sub.group(1) not in found["strings"]:
        lost.append(sub.group(1))
    lost += [f for f in FLAG.findall(re.split(r"\s\d*>", rest)[0]) if f not in found["strings"]]  # not past "> /dev/null"
    return f"{pkg}/{module}.py takes no {', '.join(lost)}" if lost else None


def path_like(s, root):
    s = s.split("?")[0]
    if re.search(r"[\s\"'\\$%@=|(]", s):
        return False
    return bool(FILE.search(s)) or s.endswith("/") or ("/" in s and (root / s.split("/")[0]).exists())


def place(s, code):
    """A file or folder: in the repo. One named by a pattern, by its bare name or in a folder git
    leaves out may instead be made by the tool's code as it runs."""
    s = s.split("?")[0]
    pattern = re.sub(r"<[^>]*>", "*", s).rstrip("/")
    if "/" not in s and s in code.zipped:
        return None
    if next(code.root.glob(pattern) if "/" in pattern else code.root.rglob(pattern), None):
        return None
    if "<" not in s and "*" not in s and s.split("/")[0] in code.kept:
        return "no such file"
    return None if made(s, code) else "no such file, and the tool's code never makes it"


def made(s, code, url=False):
    """Every fixed piece of a name the tool makes as it runs is in its code: an address whole but
    for its <...>, a file's folders and name each."""
    pieces = [p for p in re.split(r"<[^>]*>|[*?]" + ("" if url else "|/"), s.split("?")[0]) if p]
    return all(p in code.text for p in pieces)


def chain(head, rest, code):
    """`module.name...`, `Class.name` or `s.name` (a paintbox.Skin): why a step isn't defined, None if
    every step is, False if the head isn't the tool's. A module's class leads to its names, a call of
    a module's function to any of the module's classes' names; past anything else nothing is known."""
    mod = code.module(head)
    if head == "s":
        names, where = code.module("paintbox", "tool")["classes"]["Skin"], "paintbox.Skin"
    elif mod:
        names, where = mod["names"], f"{head}.py"
    elif head in code.every_class():
        names, where = code.classes[head], head
    else:
        return False
    called = False  # just past a module's function
    for attr, call in re.findall(r"\.([A-Za-z_]\w*)|(\([^()]*\))", rest):
        if call:
            names, where = (set().union(*mod["classes"].values()), f"a class in {head}.py") if called else (None, where)
            called = False
        elif names is None:
            return None
        elif attr not in names:
            return f"{where} has no {attr}"
        elif mod and names is mod["names"] and attr in mod["classes"]:
            names, where = mod["classes"][attr], f"{head}.{attr}"
        else:
            called, names = bool(mod) and names is mod["names"], None
    return None


def hooks(root):
    """The modules the hooks in .claude/settings.json run (as files, `tool/guard.py folder`, or as modules, `-m
    lab.notes --hook`), and the word each is given."""
    settings = json.loads((root / ".claude/settings.json").read_text(encoding="utf-8"))
    where = ".claude/settings.json"
    code = Code(root)
    for event in settings.get("hooks", {}).values():
        for entry in event:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                runs = {(path, arg) for path, arg in re.findall(r"\$\{CLAUDE_PROJECT_DIR\}/(\w+/\w+\.py)\\?\"?\s+([\w-]+)", cmd)}
                runs |= {(f"{pkg}/{mod}.py", arg) for pkg, mod, arg in re.findall(r"-m (\w+)\.(\w+)\s+([\w-]+)", cmd)}
                for path, arg in sorted(runs):
                    pkg, mod = path.split("/")[0], path.split("/")[1][:-3]
                    found = code.module(mod, pkg) if pkg in code.packages else None
                    if found is None:
                        yield where, "files", path, "no such file"
                    else:
                        yield where, "commands", f"{path} {arg}", None if arg in found["strings"] else f"{path} takes no {arg}"


def line(counts, missing):
    total = sum(counts.values())
    what = f"{counts['commands']} commands and flags, {counts['files']} files, {counts['names']} names in the code"
    if not missing:
        return f"instructions: {total} things named ({what}), all present"
    return f"instructions: {len(missing)} of {total} things named are missing:\n" + "\n".join(
        f"    {where}  `{s}`: {why}" for where, s, why in missing)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[1]).resolve() if argv[:1] == ["--root"] and len(argv) == 2 else REPO
    if argv and root is REPO:
        sys.exit(__doc__)
    counts, missing = check(root)
    print(line(counts, missing))
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
