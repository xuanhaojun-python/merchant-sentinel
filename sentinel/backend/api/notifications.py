
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sentinel.backend.db import get_db
from sentinel.backend.models import Notification, NotifyChannel, Run, Schedule
from sentinel.backend.schemas import ChannelIn, ChannelOut, NotificationOut, NotifyRunIn, Page
from sentinel.backend.services import notifier

router = APIRouter(prefix="/api", tags=["notifications"])


def _get(db: Session, channel_id: int) -> NotifyChannel:
    ch = db.get(NotifyChannel, channel_id)
    if ch is None:
        raise HTTPException(404, "通知渠道不存在")
    return ch


@router.get("/channels", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    return db.query(NotifyChannel).order_by(NotifyChannel.id).all()


@router.post("/channels", response_model=ChannelOut, status_code=201)
def create_channel(body: ChannelIn, db: Session = Depends(get_db)):
    if db.query(NotifyChannel).filter(NotifyChannel.name == body.name).first():
        raise HTTPException(400, "渠道名称已存在")
    ch = NotifyChannel(**body.model_dump())
    db.add(ch)
    db.commit()
    return ch


@router.put("/channels/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: int, body: ChannelIn, db: Session = Depends(get_db)):
    ch = _get(db, channel_id)
    if db.query(NotifyChannel).filter(NotifyChannel.name == body.name, NotifyChannel.id != channel_id).first():
        raise HTTPException(400, "渠道名称已存在")
    for k, v in body.model_dump().items():
        setattr(ch, k, v)
    db.commit()
    return ch


@router.delete("/channels/{channel_id}", status_code=204)
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    ch = _get(db, channel_id)
    for sch in db.query(Schedule).all():  # 从定时任务中摘掉该渠道
        if channel_id in (sch.channel_ids or []):
            sch.channel_ids = [c for c in sch.channel_ids if c != channel_id]
    db.delete(ch)
    db.commit()


@router.post("/channels/{channel_id}/test", response_model=NotificationOut)
def test_channel(channel_id: int, db: Session = Depends(get_db)):
    ch = _get(db, channel_id)
    return notifier.send(ch, "[Web3Rec] 测试消息", ["这是一条来自 Web3Rec 测试平台的测试通知，收到说明渠道配置正确。"],
                         notifier.settings.PUBLIC_URL)


@router.post("/runs/{run_id}/notify", response_model=list[NotificationOut])
def notify_run(run_id: int, body: NotifyRunIn, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(404, "执行记录不存在")
    if run.status in ("queued", "running"):
        raise HTTPException(400, "执行尚未结束")
    return notifier.notify_run(run_id, body.channel_ids)


@router.get("/notifications", response_model=Page)
def list_notifications(project_id: int | None = None, channel_id: int | None = None, status: str | None = None,
                       page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    q = db.query(Notification)
    if project_id:
        # 渠道测试消息不属于任何项目，一并展示
        q = q.filter((Notification.project_id == project_id) | (Notification.project_id.is_(None)))
    if channel_id:
        q = q.filter(Notification.channel_id == channel_id)
    if status:
        q = q.filter(Notification.status == status)
    total = q.count()
    items = q.order_by(Notification.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [NotificationOut.model_validate(n) for n in items], "total": total}


@router.post("/notifications/{notification_id}/resend", response_model=NotificationOut)
def resend(notification_id: int, db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    if n is None:
        raise HTTPException(404, "通知记录不存在")
    ch = _get(db, n.channel_id) if n.channel_id else None
    if ch is None:
        raise HTTPException(400, "原渠道已删除，无法重发")
    if n.run_id and db.get(Run, n.run_id):
        result = notifier.notify_run(n.run_id, [ch.id])
        if not result:
            raise HTTPException(400, "渠道已停用")
        return result[0]
    lines = n.content.splitlines()
    return notifier.send(ch, n.title, lines[:-1], lines[-1] if lines else "", project_id=n.project_id)


