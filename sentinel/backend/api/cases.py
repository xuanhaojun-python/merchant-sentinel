from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from sentinel.backend.api.projects import get_project
from sentinel.backend.db import get_db
from sentinel.backend.models import CaseResult, TestCase
from sentinel.backend.schemas import CaseOut, CaseUpdate, SyncResult
from sentinel.backend.services.scanner import ScanError, sync_cases

router = APIRouter(prefix="/api", tags=["cases"])


@router.post("/projects/{project_id}/cases/sync", response_model=SyncResult)
def sync(project_id: int, db: Session = Depends(get_db)):
    project = get_project(db, project_id)
    try:
        return sync_cases(db, project)
    except ScanError as exc:
        raise HTTPException(400, str(exc))


@router.get("/projects/{project_id}/cases", response_model=list[CaseOut])
def list_cases(project_id: int, file: str | None = None, marker: str | None = None,
               keyword: str | None = None, status: str = "active", db: Session = Depends(get_db)):
    get_project(db, project_id)
    q = db.query(TestCase).filter(TestCase.project_id == project_id)
    if status != "all":
        q = q.filter(TestCase.status == status)
    if file:
        q = q.filter(TestCase.file == file)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(TestCase.nodeid.like(like), TestCase.docstring.like(like), TestCase.remark.like(like)))
    cases = q.order_by(TestCase.file, TestCase.id).all()
    if marker:
        cases = [c for c in cases if marker in (c.markers or [])]
    # 最近一次结果
    last: dict[int, str] = {}
    ids = [c.id for c in cases]
    if ids:
        for r in (db.query(CaseResult.test_case_id, CaseResult.outcome)
                  .filter(CaseResult.test_case_id.in_(ids)).order_by(CaseResult.id)):
            last[r.test_case_id] = r.outcome
    out = []
    for c in cases:
        o = CaseOut.model_validate(c)
        o.last_outcome = last.get(c.id)
        out.append(o)
    return out


@router.put("/cases/{case_id}", response_model=CaseOut)
def update_case(case_id: int, body: CaseUpdate, db: Session = Depends(get_db)):
    case = db.get(TestCase, case_id)
    if case is None:
        raise HTTPException(404, "用例不存在")
    if body.remark is not None:
        case.remark = body.remark
    if body.tags is not None:
        case.tags = body.tags
    db.commit()
    return CaseOut.model_validate(case)
