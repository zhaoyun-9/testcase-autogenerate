"""
处理会话API端点 (最终版)
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc, text
from loguru import logger

from app.database.connection import db_manager
from app.database.models.test_case import ProcessingSession, Project, TestCase, MindMap, ExportRecord
from app.core.enums import SessionType, SessionStatus

router = APIRouter()

class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    session_type: SessionType
    status: SessionStatus
    progress: float
    project_id: Optional[str]
    project_name: Optional[str] = None
    agent_type: Optional[str]
    processing_time: Optional[float]
    error_message: Optional[str]
    generated_count: int
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: str
    # 新增统计字段
    test_cases_count: Optional[int] = 0
    mind_map_exists: Optional[bool] = False
    export_records_count: Optional[int] = 0

    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    """会话列表响应"""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_id: Optional[str] = Query(None, description="项目ID过滤"),
    session_type: Optional[SessionType] = Query(None, description="会话类型过滤"),
    status: Optional[SessionStatus] = Query(None, description="状态过滤")
):
    """获取处理会话列表"""
    try:
        from sqlalchemy import text

        async with db_manager.get_session() as session:
            # 构建 WHERE 条件
            where_conditions = []
            params = {}

            if project_id:
                where_conditions.append("ps.project_id = :project_id")
                params["project_id"] = project_id

            if session_type:
                where_conditions.append("ps.session_type = :session_type")
                params["session_type"] = session_type.value

            if status:
                where_conditions.append("ps.status = :status")
                params["status"] = status.value

            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)

            # 获取总数
            count_sql = f"""
                SELECT COUNT(*)
                FROM processing_sessions ps
                {where_clause}
            """

            total_result = await session.execute(text(count_sql), params)
            total = total_result.scalar()

            # 分页查询
            offset = (page - 1) * page_size
            params.update({"offset": offset, "limit": page_size})

            query_sql = f"""
                SELECT
                    ps.id, ps.session_type, ps.status, ps.progress, ps.project_id,
                    ps.agent_type, ps.processing_time, ps.error_message, ps.generated_count,
                    ps.started_at, ps.completed_at, ps.created_at, ps.updated_at,
                    p.name as project_name
                FROM processing_sessions ps
                LEFT JOIN projects p ON ps.project_id = p.id
                {where_clause}
                ORDER BY ps.created_at DESC
                LIMIT :limit OFFSET :offset
            """

            result = await session.execute(text(query_sql), params)
            rows = result.fetchall()

            # 构建响应
            items = []
            for row in rows:
                # 安全地转换枚举值
                try:
                    session_type_enum = SessionType(row.session_type)
                except ValueError:
                    logger.warning(f"未知的会话类型: {row.session_type}")
                    session_type_enum = SessionType.MANUAL_INPUT  # 默认值

                try:
                    status_enum = SessionStatus(row.status)
                except ValueError:
                    logger.warning(f"未知的会话状态: {row.status}")
                    status_enum = SessionStatus.CREATED  # 默认值

                items.append(SessionResponse(
                    id=row.id,
                    session_type=session_type_enum,
                    status=status_enum,
                    progress=float(row.progress) if row.progress else 0.0,
                    project_id=row.project_id,
                    project_name=row.project_name,
                    agent_type=row.agent_type,
                    processing_time=row.processing_time,
                    error_message=row.error_message,
                    generated_count=row.generated_count or 0,
                    started_at=row.started_at.isoformat() if row.started_at else None,
                    completed_at=row.completed_at.isoformat() if row.completed_at else None,
                    created_at=row.created_at.isoformat(),
                    updated_at=row.updated_at.isoformat()
                ))

            return SessionListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )

    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        from sqlalchemy import text

        async with db_manager.get_session() as session:
            query_sql = """
                SELECT
                    ps.id, ps.session_type, ps.status, ps.progress, ps.project_id,
                    ps.agent_type, ps.processing_time, ps.error_message, ps.generated_count,
                    ps.started_at, ps.completed_at, ps.created_at, ps.updated_at,
                    p.name as project_name
                FROM processing_sessions ps
                LEFT JOIN projects p ON ps.project_id = p.id
                WHERE ps.id = :session_id
            """

            result = await session.execute(text(query_sql), {"session_id": session_id})
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="会话不存在")

            # 安全地转换枚举值
            try:
                session_type_enum = SessionType(row.session_type)
            except ValueError:
                logger.warning(f"未知的会话类型: {row.session_type}")
                session_type_enum = SessionType.MANUAL_INPUT  # 默认值

            try:
                status_enum = SessionStatus(row.status)
            except ValueError:
                logger.warning(f"未知的会话状态: {row.status}")
                status_enum = SessionStatus.CREATED  # 默认值

            return SessionResponse(
                id=row.id,
                session_type=session_type_enum,
                status=status_enum,
                progress=float(row.progress) if row.progress else 0.0,
                project_id=row.project_id,
                project_name=row.project_name,
                agent_type=row.agent_type,
                processing_time=row.processing_time,
                error_message=row.error_message,
                generated_count=row.generated_count or 0,
                started_at=row.started_at.isoformat() if row.started_at else None,
                completed_at=row.completed_at.isoformat() if row.completed_at else None,
                created_at=row.created_at.isoformat(),
                updated_at=row.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ProcessingSession).where(ProcessingSession.id == session_id)
            )
            ps = result.scalar_one_or_none()
            
            if not ps:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            # 只能删除已完成或失败的会话
            if ps.status in [SessionStatus.CREATED, SessionStatus.PROCESSING]:
                raise HTTPException(status_code=400, detail="无法删除正在处理的会话")
            
            await session.delete(ps)
            await session.commit()
            
            return {"message": "会话删除成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")

@router.get("/{session_id}/test-cases")
async def get_session_test_cases(session_id: str):
    """获取会话生成的测试用例"""
    try:
        async with db_manager.get_session() as session:
            # 验证会话存在
            session_result = await session.execute(
                select(ProcessingSession).where(ProcessingSession.id == session_id)
            )
            ps = session_result.scalar_one_or_none()
            
            if not ps:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            # 获取关联的测试用例
            from app.database.models.test_case import TestCase
            test_cases_result = await session.execute(
                select(TestCase)
                .where(TestCase.session_id == session_id)
                .order_by(desc(TestCase.created_at))
            )
            test_cases = test_cases_result.scalars().all()
            
            return {
                "session": {
                    "id": ps.id,
                    "session_type": ps.session_type,
                    "status": ps.status,
                    "generated_count": ps.generated_count
                },
                "test_cases": [
                    {
                        "id": tc.id,
                        "title": tc.title,
                        "test_type": tc.test_type,
                        "test_level": tc.test_level,
                        "priority": tc.priority,
                        "status": tc.status,
                        "ai_generated": tc.ai_generated,
                        "ai_confidence": tc.ai_confidence,
                        "created_at": tc.created_at.isoformat()
                    }
                    for tc in test_cases
                ],
                "total": len(test_cases)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话测试用例失败: {str(e)}")

@router.get("/stats/summary")
async def get_session_stats():
    """获取会话统计信息"""
    try:
        async with db_manager.get_session() as session:
            # 总会话数
            total_result = await session.execute(
                select(func.count(ProcessingSession.id))
            )
            total_sessions = total_result.scalar() or 0
            
            # 按状态统计
            status_stats_result = await session.execute(
                select(
                    ProcessingSession.status,
                    func.count(ProcessingSession.id).label('count')
                ).group_by(ProcessingSession.status)
            )
            status_stats = {row.status: row.count for row in status_stats_result}
            
            # 按类型统计
            type_stats_result = await session.execute(
                select(
                    ProcessingSession.session_type,
                    func.count(ProcessingSession.id).label('count')
                ).group_by(ProcessingSession.session_type)
            )
            type_stats = {row.session_type: row.count for row in type_stats_result}
            
            # 总生成测试用例数
            total_generated_result = await session.execute(
                select(func.sum(ProcessingSession.generated_count))
            )
            total_generated = total_generated_result.scalar() or 0
            
            # 平均处理时间
            avg_time_result = await session.execute(
                select(func.avg(ProcessingSession.processing_time))
                .where(ProcessingSession.processing_time.isnot(None))
            )
            avg_processing_time = avg_time_result.scalar() or 0
            
            return {
                "total_sessions": total_sessions,
                "status_stats": status_stats,
                "type_stats": type_stats,
                "total_generated_test_cases": total_generated,
                "avg_processing_time": float(avg_processing_time)
            }
            
    except Exception as e:
        logger.error(f"获取会话统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话统计失败: {str(e)}")

@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str):
    """取消会话处理"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(ProcessingSession).where(ProcessingSession.id == session_id)
            )
            ps = result.scalar_one_or_none()
            
            if not ps:
                raise HTTPException(status_code=404, detail="会话不存在")
            
            # 只能取消正在处理的会话
            if ps.status not in [SessionStatus.CREATED, SessionStatus.PROCESSING]:
                raise HTTPException(status_code=400, detail="会话无法取消")
            
            # 更新状态
            ps.status = SessionStatus.FAILED
            ps.error_message = "用户取消"
            
            await session.commit()
            
            return {"message": "会话已取消"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消会话失败: {str(e)}")

@router.get("/{session_id}/test-cases")
async def get_session_test_cases(
    session_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取会话的测试用例列表"""
    try:
        async with db_manager.get_session() as session:
            # 验证会话存在
            session_result = await session.execute(
                select(ProcessingSession).where(ProcessingSession.id == session_id)
            )
            if not session_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="会话不存在")

            # 查询测试用例
            query = select(TestCase).where(TestCase.session_id == session_id)

            # 获取总数
            count_result = await session.execute(
                select(func.count(TestCase.id)).where(TestCase.session_id == session_id)
            )
            total = count_result.scalar()

            # 分页查询
            query = query.order_by(desc(TestCase.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            test_cases = result.scalars().all()

            # 转换为响应格式
            test_case_list = []
            for tc in test_cases:
                test_case_list.append({
                    "id": tc.id,
                    "title": tc.title,
                    "description": tc.description,
                    "test_type": tc.test_type.value,
                    "test_level": tc.test_level.value,
                    "priority": tc.priority.value,
                    "status": tc.status.value,
                    "created_at": tc.created_at.isoformat(),
                    "updated_at": tc.updated_at.isoformat()
                })

            total_pages = (total + page_size - 1) // page_size

            return {
                "items": test_case_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话测试用例失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话测试用例失败: {str(e)}")

@router.get("/{session_id}/mindmap")
async def get_session_mindmap(session_id: str):
    """获取会话的思维导图"""
    try:
        async with db_manager.get_session() as session:
            # 验证会话存在 - 使用原始SQL避免枚举转换问题
            session_check_sql = "SELECT id FROM processing_sessions WHERE id = :session_id"
            session_result = await session.execute(text(session_check_sql), {"session_id": session_id})
            if not session_result.fetchone():
                raise HTTPException(status_code=404, detail="会话不存在")

            # 查询思维导图 - 使用原始SQL
            mindmap_sql = """
                SELECT id, name, session_id, project_id, mind_map_data, layout_config, created_at, updated_at
                FROM mind_maps
                WHERE session_id = :session_id
            """
            result = await session.execute(text(mindmap_sql), {"session_id": session_id})
            mindmap_row = result.fetchone()

            if not mindmap_row:
                raise HTTPException(status_code=404, detail="该会话没有关联的思维导图")

            return {
                "id": mindmap_row.id,
                "name": mindmap_row.name,
                "session_id": mindmap_row.session_id,
                "project_id": mindmap_row.project_id,
                "mind_map_data": mindmap_row.mind_map_data,
                "layout_config": mindmap_row.layout_config,
                "created_at": mindmap_row.created_at.isoformat(),
                "updated_at": mindmap_row.updated_at.isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话思维导图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话思维导图失败: {str(e)}")
