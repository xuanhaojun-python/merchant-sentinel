from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from sentinel.backend.api.projects import get_project
from sentinel.backend.db import get_db
from sentinel.backend.models import Element
from sentinel.backend.schemas import ElementOut, ElementSyncResult, ElementUpdate
from sentinel.backend.services.element_scanner import sync_elements

router = APIRouter(prefix="/api", tags=["elements"])


@router.post("/projects/{project_id}/elements/sync", response_model=ElementSyncResult)
def sync(project_id: int, db: Session = Depends(get_db)):
    return sync_elements(db, get_project(db, project_id))


@router.get("/projects/{project_id}/elements", response_model=list[ElementOut])
def list_elements(project_id: int, page: str | None = None, kind: str | None = None, keyword: str | None = None,
                  status: str = "active", db: Session = Depends(get_db)):
    get_project(db, project_id)
    q = db.query(Element).filter(Element.project_id == project_id)
    if status != "all":
        q = q.filter(Element.status == status)
    if page:
        q = q.filter(Element.page == page)
    if kind:
        q = q.filter(Element.kind == kind)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(Element.name.like(like), Element.selector.like(like), Element.remark.like(like)))
    return q.order_by(Element.file, Element.page, Element.line).all()


@router.put("/elements/{element_id}", response_model=ElementOut)
def update_element(element_id: int, body: ElementUpdate, db: Session = Depends(get_db)):
    el = db.get(Element, element_id)
    if el is None:
        raise HTTPException(404, "元素不存在")
    el.remark = body.remark
    db.commit()
    return el
