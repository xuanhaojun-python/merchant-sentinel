"""元素扫描：解析 <root>/pages 下 Page Object 类中的大写字符串常量（选择器、路径、按钮名等）。

只做静态 AST 解析，不导入工程代码。
"""
import ast
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from sentinel.backend.models import Element, Project

PAGES_DIR = "pages"
SEARCH_DIRS = ("pages", "tests")
_CONST = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _value(node: ast.AST) -> tuple[str, bool] | None:
    """返回 (字符串值, 是否正则)；不是字符串常量返回 None。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, False
    # re.compile("...")
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "compile"
            and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
        return node.args[0].value, True
    return None


def classify(name: str, value: str, is_regex: bool) -> str:
    v = value.strip()
    if is_regex:
        return "regex"
    if name == "PATH" or name.endswith("_PATH") or (v.startswith("/") and not v.startswith("//") and " " not in v):
        return "path"
    if v.startswith(("//", "xpath=", "(//")):
        return "xpath"
    if v.startswith("text=") or name.endswith(("_TEXT", "_NAME", "_LABEL", "_TITLE")):
        return "text"
    return "css"


def scan(root: str) -> tuple[list[dict], list[dict]]:
    base = Path(root)
    pages = base / PAGES_DIR
    items, errors = [], []
    classes: dict[str, tuple[str, list[str]]] = {}  # 类名 -> (文件, 基类名)
    if not pages.is_dir():
        return items, [{"file": PAGES_DIR, "error": "工程下没有 pages/ 目录"}]
    for path in sorted(pages.rglob("*.py")):
        rel = path.relative_to(base).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append({"file": rel, "error": str(exc)})
            continue
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            classes[cls.name] = (rel, [b.id for b in cls.bases if isinstance(b, ast.Name)])
            for stmt in cls.body:
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target] if isinstance(stmt, ast.AnnAssign) and stmt.value else []
                for t in targets:
                    if not (isinstance(t, ast.Name) and _CONST.match(t.id)):
                        continue
                    val = _value(stmt.value)
                    if val is None:
                        continue
                    items.append({"page": cls.name, "name": t.id, "selector": val[0], "kind": classify(t.id, *val),
                                  "file": rel, "line": stmt.lineno})
    _count_refs(base, items, classes)
    return items, errors


def _descendant_files(cls: str, classes: dict[str, tuple[str, list[str]]]) -> set[str]:
    """cls 自身及所有（传递）子类所在的文件：子类里的 self.常量 也算对父类常量的引用。"""
    files, todo, seen = set(), [cls], set()
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        if c in classes:
            files.add(classes[c][0])
        todo += [name for name, (_, bases) in classes.items() if c in bases]
    return files


def _count_refs(base: Path, items: list[dict], classes: dict | None = None) -> None:
    """引用次数（近似值）：自身及子类所在文件内的 self./cls./类名. 访问 + 其它文件中 类名.常量 访问。"""
    sources = {}
    for d in SEARCH_DIRS:
        for p in (base / d).rglob("*.py") if (base / d).is_dir() else []:
            try:
                sources[p.relative_to(base).as_posix()] = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
    for it in items:
        own_files = _descendant_files(it["page"], classes or {}) or {it["file"]}
        own = re.compile(rf"\b(?:self|cls|{re.escape(it['page'])})\.{re.escape(it['name'])}\b")
        other = re.compile(rf"\b{re.escape(it['page'])}\.{re.escape(it['name'])}\b")
        it["refs"] = sum(len((own if f in own_files else other).findall(src)) for f, src in sources.items())


def sync_elements(db: Session, project: Project) -> dict:
    items, errors = scan(project.root_path)
    now = datetime.now()
    existing = {(e.page, e.name): e for e in db.query(Element).filter(Element.project_id == project.id)}
    seen, added, updated = set(), 0, 0
    for it in items:
        key = (it["page"], it["name"])
        seen.add(key)  # 同一类中重复赋值时以最后一次为准
        el = existing.get(key)
        if el is None:
            el = Element(project_id=project.id, **it)
            db.add(el)
            existing[key] = el
            added += 1
            continue
        changed = any(getattr(el, k) != v for k, v in it.items() if k not in ("line", "refs")) or el.status != "active"
        for k, v in it.items():
            setattr(el, k, v)
        el.status, el.synced_at = "active", now
        updated += int(changed)
    error_files = {e["file"] for e in errors}
    removed = 0
    for key, el in existing.items():
        if key not in seen and el.status != "removed" and el.file not in error_files:
            el.status = "removed"
            removed += 1
    db.commit()
    return {"added": added, "updated": updated, "removed": removed, "errors": errors}
