"""套件展开：静态 nodeid 列表 ∪ marker 表达式匹配到的有效用例。"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sentinel.backend.models import TestCase

try:  # pytest 内部实现，与 `pytest -m` 语义一致
    from _pytest.mark.expression import Expression, ParseError
except ImportError:  # pragma: no cover
    Expression = ParseError = None


def compile_expr(expr: str):
    expr = (expr or "").strip()
    if not expr:
        return None
    try:
        return Expression.compile(expr)
    except ParseError as exc:
        raise HTTPException(400, f"marker 表达式不合法：{exc}")


def _matches(compiled, markers: list[str]) -> bool:
    names = set(markers or [])
    # pytest 8 的 evaluate 回调签名为 (name) 或 (name, **kwargs)，兼容两种
    return compiled.evaluate(lambda name, **_: name in names)


def expand(db: Session, project_id: int, nodeids: list[str], marker_expr: str) -> tuple[list[str], list[str]]:
    """返回 (按文件排序的可执行 nodeid, 静态列表中失效的 nodeid)。"""
    active = {c.nodeid: c for c in db.query(TestCase).filter(TestCase.project_id == project_id, TestCase.status == "active")}
    picked = {n for n in nodeids if n in active}
    missing = [n for n in nodeids if n not in active]
    compiled = compile_expr(marker_expr)
    if compiled is not None:
        picked |= {n for n, c in active.items() if _matches(compiled, c.markers)}
    order = {n: (c.file, c.id) for n, c in active.items()}
    return sorted(picked, key=lambda n: order[n]), missing
