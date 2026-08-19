"""研究任务 REST API。"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ReportOut, ResearchCreate, ResearchOut
from app.core.database import get_db
from app.models.report import Report
from app.models.research import ResearchTask
from app.services.research_service import schedule_research

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=ResearchOut, status_code=201)
async def create_research(body: ResearchCreate, db: AsyncSession = Depends(get_db)):
    """创建研究任务并立即在后台执行。"""
    task = ResearchTask(topic=body.topic.strip(), status="pending")
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await schedule_research(task)
    return task.to_dict()


@router.get("", response_model=list[ResearchOut])
async def list_research(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ResearchTask).order_by(ResearchTask.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return [r.to_dict() for r in rows]


@router.get("/{task_id}", response_model=ResearchOut)
async def get_research(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(ResearchTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="研究任务不存在")
    return task.to_dict()


@router.get("/{task_id}/report", response_model=ReportOut)
async def get_task_report(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Report).where(Report.task_id == task_id).order_by(Report.created_at.desc())
    report = (await db.execute(stmt)).scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="该任务暂无报告")
    return report.to_dict()


@router.delete("/{task_id}")
async def delete_research(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(ResearchTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="研究任务不存在")
    await db.delete(task)
    await db.commit()
    return {"ok": True, "deleted": task_id}
