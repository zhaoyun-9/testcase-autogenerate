"""
测试用例数据库保存智能体 - 优化版本
专门负责将测试用例数据保存到数据库
遵循单一职责原则，专注于数据持久化操作
"""
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import TestCaseData
from app.database.connection import db_manager
from app.database.repositories.test_case_repository import TestCaseRepository
from app.database.repositories.requirement_repository import RequirementRepository, TestCaseRequirementRepository
from app.database.models.test_case import (
    TestCaseCreateRequest, TestCaseResponse
)
from app.database.models.requirement import (
    TestCaseRequirementCreateRequest
)
from app.core.enums import (
    TestType, TestLevel, Priority, InputSource
)


class TestCaseSaveRequest(BaseModel):
    """测试用例保存请求"""
    session_id: str = Field(..., description="会话ID")
    test_cases: List[TestCaseData] = Field(..., description="测试用例数据列表")
    project_id: Optional[str] = Field(None, description="项目ID")
    created_by: Optional[str] = Field(None, description="创建人ID")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="源数据元信息")
    requirement_mappings: Optional[Dict[str, List[str]]] = Field(None, description="测试用例与需求的映射关系")


class TestCaseSaveResponse(BaseModel):
    """测试用例保存响应"""
    session_id: str = Field(..., description="会话ID")
    success: bool = Field(..., description="是否成功")
    saved_count: int = Field(0, description="保存成功的数量")
    failed_count: int = Field(0, description="保存失败的数量")
    saved_test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="保存成功的测试用例")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    processing_time: float = Field(0.0, description="处理时间")


@type_subscription(topic_type=TopicTypes.TEST_CASE_SAVER.value)
class TestCaseSaverAgent(BaseAgent):
    """
    测试用例数据库保存智能体 - 优化版本

    职责：
    1. 接收测试用例保存请求
    2. 数据验证和转换
    3. 批量保存操作
    4. 事务管理和错误处理
    5. 保存结果反馈

    设计原则：
    - 单一职责：专注于数据持久化
    - 事务安全：确保数据一致性
    - 批量处理：支持高效的批量操作
    - 错误恢复：完善的错误处理和回滚机制
    """

    def __init__(self, **kwargs):
        """初始化测试用例保存智能体"""
        super().__init__(
            agent_id=AgentTypes.TEST_CASE_SAVER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.TEST_CASE_SAVER.value, "测试用例保存智能体"),
            **kwargs
        )

        # 初始化仓储
        self.test_case_repository = TestCaseRepository()
        self.requirement_repository = RequirementRepository()
        self.test_case_requirement_repository = TestCaseRequirementRepository()

        # 初始化性能指标
        self.save_metrics = {
            "total_requests": 0,
            "successful_saves": 0,
            "failed_saves": 0,
            "total_test_cases_saved": 0,
            "average_processing_time": 0.0,
            "batch_sizes": []
        }

        # 保存配置
        self.save_config = {
            "batch_size": 50,   # 批量保存大小
            "commit_interval": 10,  # 每处理多少个测试用例提交一次
            "max_retries": 3,   # 最大重试次数
            "retry_delay": 1.0, # 重试延迟（秒）
            "enable_transaction": True,  # 启用事务
            "enable_parallel_processing": False,  # 启用并行处理
            "max_concurrent_saves": 5,  # 最大并发保存数
            "enable_batch_validation": True,  # 启用批量验证
            "rollback_on_error": True  # 错误时回滚
        }

        logger.info(f"测试用例保存智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_test_case_save_request(
        self,
        message: TestCaseSaveRequest,
        ctx: MessageContext
    ) -> TestCaseSaveResponse:
        """
        处理测试用例保存请求 - 优化版本

        流程：
        1. 数据验证
        2. 批量保存处理
        3. 事务管理
        4. 错误处理和重试
        5. 结果反馈
        """
        start_time = datetime.now()
        self.save_metrics["total_requests"] += 1

        try:
            logger.info(f"开始处理测试用例保存请求: {message.session_id}")

            await self.send_response(
                f"💾 开始保存 {len(message.test_cases)} 个测试用例到数据库...",
                region="process"
            )

            # 数据验证
            if not await self._validate_save_request(message):
                return await self._handle_validation_error(message, start_time)

            # 批量保存处理
            save_result = await self._save_test_cases_with_retry(message)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            save_result.processing_time = processing_time

            # 更新指标
            if save_result.success:
                self.save_metrics["successful_saves"] += 1
                self.save_metrics["total_test_cases_saved"] += save_result.saved_count
            else:
                self.save_metrics["failed_saves"] += 1

            self.save_metrics["batch_sizes"].append(len(message.test_cases))
            self._update_average_processing_time(start_time)

            # 发送响应
            await self._send_save_response(save_result)

            # 发布保存结果到流式输出
            await self.publish_message(
                save_result,
                topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
            )

            return save_result

        except Exception as e:
            return await self._handle_save_error(message, e, start_time)

    async def _validate_save_request(self, message: TestCaseSaveRequest) -> bool:
        """验证保存请求"""
        if not message.test_cases:
            logger.warning(f"保存请求中没有测试用例数据: {message.session_id}")
            return False

        if len(message.test_cases) > 1000:  # 限制批量大小
            logger.warning(f"批量保存数量过大: {len(message.test_cases)}")
            return False

        return True

    async def _handle_validation_error(
        self,
        message: TestCaseSaveRequest,
        start_time: datetime
    ) -> TestCaseSaveResponse:
        """处理验证错误"""
        error_response = TestCaseSaveResponse(
            session_id=message.session_id,
            success=False,
            saved_count=0,
            failed_count=len(message.test_cases),
            errors=["数据验证失败"],
            processing_time=(datetime.now() - start_time).total_seconds()
        )

        await self.send_response(
            "❌ 数据验证失败，无法保存测试用例",
            is_final=True
        )

        return error_response

    async def _save_test_cases_with_retry(
        self,
        message: TestCaseSaveRequest
    ) -> TestCaseSaveResponse:
        """带重试的保存测试用例"""
        last_error = None

        for attempt in range(self.save_config["max_retries"]):
            try:
                if attempt > 0:
                    await self.send_response(f"🔄 第 {attempt + 1} 次重试保存...")
                    import asyncio
                    await asyncio.sleep(self.save_config["retry_delay"])

                return await self._save_test_cases_to_database(message)

            except Exception as e:
                last_error = e
                logger.warning(f"保存尝试 {attempt + 1} 失败: {str(e)}")

        # 所有重试都失败
        return TestCaseSaveResponse(
            session_id=message.session_id,
            success=False,
            saved_count=0,
            failed_count=len(message.test_cases),
            errors=[f"重试 {self.save_config['max_retries']} 次后仍然失败: {str(last_error)}"]
        )

    async def _send_save_response(self, save_result: TestCaseSaveResponse):
        """发送保存响应"""
        if save_result.success:
            await self.send_response(
                f"✅ 测试用例保存完成，成功保存 {save_result.saved_count} 个用例",
                is_final=True,
                result=save_result.model_dump()
            )
        else:
            await self.send_response(
                f"❌ 测试用例保存失败，成功 {save_result.saved_count} 个，失败 {save_result.failed_count} 个",
                is_final=True,
                result=save_result.model_dump()
            )

    async def _handle_save_error(
        self,
        message: TestCaseSaveRequest,
        error: Exception,
        start_time: datetime
    ) -> TestCaseSaveResponse:
        """处理保存错误"""
        logger.error(f"测试用例保存失败: {str(error)}")
        self.save_metrics["failed_saves"] += 1

        error_response = TestCaseSaveResponse(
            session_id=message.session_id,
            success=False,
            saved_count=0,
            failed_count=len(message.test_cases),
            errors=[str(error)],
            processing_time=(datetime.now() - start_time).total_seconds()
        )

        await self.send_response(
            f"❌ 测试用例保存异常: {str(error)}",
            is_final=True,
        )

        await self.publish_message(
            error_response,
            topic_id=TopicId(type=TopicTypes.STREAM_OUTPUT.value, source=self.id.key)
        )

        return error_response

    async def _save_test_cases_to_database(self, message: TestCaseSaveRequest) -> TestCaseSaveResponse:
        """保存测试用例到数据库 - 优化版本"""
        response = TestCaseSaveResponse(
            session_id=message.session_id,
            success=False
        )

        try:
            # 批量验证（如果启用）
            if self.save_config["enable_batch_validation"]:
                await self.send_response("🔍 正在进行批量数据验证...")
                validation_results = await self._batch_validate_test_cases(message.test_cases)
                valid_test_cases = [tc for tc, valid in zip(message.test_cases, validation_results) if valid["is_valid"]]
                invalid_count = len(message.test_cases) - len(valid_test_cases)

                if invalid_count > 0:
                    await self.send_response(f"⚠️ 发现 {invalid_count} 个无效测试用例，将跳过保存")
            else:
                valid_test_cases = message.test_cases

            # 分批处理
            batch_size = self.save_config["batch_size"]
            total_batches = (len(valid_test_cases) + batch_size - 1) // batch_size

            all_saved_test_cases = []
            all_errors = []

            for batch_index in range(total_batches):
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, len(valid_test_cases))
                batch_test_cases = valid_test_cases[start_idx:end_idx]

                await self.send_response(f"📦 正在处理第 {batch_index + 1}/{total_batches} 批数据 ({len(batch_test_cases)} 个测试用例)...")

                # 处理当前批次
                batch_result = await self._save_test_case_batch(
                    batch_test_cases, message, start_idx
                )

                all_saved_test_cases.extend(batch_result["saved_test_cases"])
                all_errors.extend(batch_result["errors"])

                # 批次间短暂休息，避免数据库压力过大
                if batch_index < total_batches - 1:
                    import asyncio
                    await asyncio.sleep(0.1)

            # 构建最终响应
            response.success = len(all_saved_test_cases) > 0
            response.saved_count = len(all_saved_test_cases)
            response.failed_count = len(all_errors)
            response.saved_test_cases = all_saved_test_cases
            response.errors = all_errors

            logger.info(f"批量保存完成: 成功 {response.saved_count} 个，失败 {response.failed_count} 个")

        except Exception as e:
            logger.error(f"批量保存测试用例异常: {str(e)}")
            response.success = False
            response.failed_count = len(message.test_cases)
            response.errors = [str(e)]

        return response

    async def _batch_validate_test_cases(self, test_cases: List[TestCaseData]) -> List[Dict[str, Any]]:
        """批量验证测试用例"""
        validation_results = []

        for test_case_data in test_cases:
            validation_result = await self.validate_test_case_data(test_case_data)
            validation_results.append(validation_result)

        return validation_results

    async def _save_test_case_batch(
        self,
        batch_test_cases: List[TestCaseData],
        message: TestCaseSaveRequest,
        start_index: int
    ) -> Dict[str, Any]:
        """保存一批测试用例"""
        saved_test_cases = []
        errors = []

        try:
            async with db_manager.get_session() as session:
                for i, test_case_data in enumerate(batch_test_cases):
                    global_index = start_index + i + 1

                    try:
                        # 数据验证（如果未进行批量验证）
                        if not self.save_config["enable_batch_validation"]:
                            validation_result = await self.validate_test_case_data(test_case_data)
                            if not validation_result["is_valid"]:
                                error_msg = f"第 {global_index} 个测试用例数据验证失败: {'; '.join(validation_result['errors'])}"
                                errors.append(error_msg)
                                logger.warning(error_msg)
                                continue

                        # 数据清理和标准化
                        cleaned_test_case_data = await self.clean_and_normalize_test_case_data(test_case_data)

                        # 转换为数据库创建请求
                        create_request = await self._convert_to_create_request(cleaned_test_case_data, message)

                        # 保存到数据库
                        saved_test_case = await self.test_case_repository.create_test_case(
                            session,
                            create_request
                        )

                        # 保存测试用例与需求的关联关系
                        await self._save_test_case_requirements(
                            session, saved_test_case.id, cleaned_test_case_data, message
                        )

                        # 记录成功保存的测试用例
                        saved_test_case_info = {
                            "id": saved_test_case.id,
                            "title": saved_test_case.title,
                            "test_type": saved_test_case.test_type.value,
                            "test_level": saved_test_case.test_level.value,
                            "priority": saved_test_case.priority.value,
                            "status": saved_test_case.status.value,
                            "created_at": saved_test_case.created_at.isoformat() if saved_test_case.created_at else None,
                            "ai_confidence": saved_test_case.ai_confidence,
                            "input_source": saved_test_case.input_source.value if saved_test_case.input_source else None
                        }
                        saved_test_cases.append(saved_test_case_info)

                        logger.info(f"成功保存测试用例: {saved_test_case.title}")

                        # 按配置的间隔提交
                        if (i + 1) % self.save_config["commit_interval"] == 0:
                            await session.commit()

                    except Exception as e:
                        error_msg = f"保存第 {global_index} 个测试用例失败: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)

                        # 记录详细错误信息
                        await self._log_save_error(test_case_data, e, global_index)

                        # 如果启用错误回滚，回滚当前事务
                        if self.save_config["rollback_on_error"]:
                            await session.rollback()
                            break
                        continue

                # 最终提交
                await session.commit()

        except Exception as e:
            logger.error(f"批次保存异常: {str(e)}")
            errors.append(f"批次保存异常: {str(e)}")

        return {
            "saved_test_cases": saved_test_cases,
            "errors": errors
        }

    async def _validate_project_id(self, project_id: Optional[str]) -> Optional[str]:
        """
        验证项目ID是否存在

        Args:
            project_id: 项目ID

        Returns:
            Optional[str]: 有效的项目ID，如果无效则返回None使用默认项目
        """
        if not project_id or not project_id.strip():
            return None

        try:
            async with db_manager.get_session() as session:
                # 检查项目是否存在
                from sqlalchemy import text
                result = await session.execute(
                    text("SELECT COUNT(*) FROM projects WHERE id = :project_id"),
                    {"project_id": project_id.strip()}
                )

                if result.scalar() > 0:
                    return project_id.strip()
                else:
                    logger.warning(f"项目ID不存在: {project_id}，将使用默认项目")
                    return None

        except Exception as e:
            logger.error(f"验证项目ID失败: {str(e)}，将使用默认项目")
            return None

    def _normalize_string_field(self, field_value) -> Optional[str]:
        """
        标准化字符串字段，处理可能的列表类型

        Args:
            field_value: 字段值，可能是字符串、列表或None

        Returns:
            Optional[str]: 标准化后的字符串值
        """
        if field_value is None:
            return None
        elif isinstance(field_value, list):
            # 如果是列表，用换行符连接
            return "\n".join(str(item) for item in field_value if item is not None)
        else:
            # 其他类型转换为字符串
            return str(field_value)

    async def _convert_to_create_request(
        self,
        test_case_data: TestCaseData,
        message: TestCaseSaveRequest
    ) -> TestCaseCreateRequest:
        """转换测试用例数据为数据库创建请求"""
        # 使用辅助函数标准化字符串字段
        preconditions = self._normalize_string_field(test_case_data.preconditions)
        expected_results = self._normalize_string_field(test_case_data.expected_results)
        description = self._normalize_string_field(test_case_data.description)

        # 验证项目ID - 如果为空或无效，使用None让Repository处理默认项目
        project_id = await self._validate_project_id(message.project_id)

        return TestCaseCreateRequest(
            title=test_case_data.title,
            description=description,
            preconditions=preconditions,
            test_steps=test_case_data.test_steps,
            expected_results=expected_results,
            test_type=test_case_data.test_type,
            test_level=test_case_data.test_level,
            priority=test_case_data.priority,
            project_id=project_id,  # 使用处理后的项目ID
            session_id=message.session_id,
            input_source=test_case_data.input_source,
            source_file_path=test_case_data.source_file_path,
            ai_generated=True,
            ai_confidence=test_case_data.ai_confidence,
            ai_model_info={
                "model": "deepseek-chat",
                "generation_time": datetime.now().isoformat(),
                "agent_version": "2.0",
                "session_id": message.session_id
            },
            tags=getattr(test_case_data, 'tags', None) or ["AI生成"]
        )

    async def get_test_cases_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取测试用例"""
        try:
            async with db_manager.get_session() as session:
                # 直接查询指定会话ID的测试用例
                from app.database.models.test_case import TestCase
                from sqlalchemy import select

                stmt = select(TestCase).where(TestCase.session_id == session_id)
                result = await session.execute(stmt)
                test_cases = result.scalars().all()

                # 构建返回数据
                filtered_cases = []
                for test_case in test_cases:
                    filtered_cases.append({
                        "id": test_case.id,
                        "title": test_case.title,
                        "test_type": test_case.test_type.value,
                        "priority": test_case.priority.value,
                        "status": test_case.status.value,
                        "created_at": test_case.created_at.isoformat()
                    })

                return filtered_cases
                
        except Exception as e:
            logger.error(f"获取会话测试用例失败: {str(e)}")
            return []

    async def update_test_case_status_batch(
        self, 
        test_case_ids: List[str], 
        status: str,
        updated_by: str
    ) -> Dict[str, Any]:
        """批量更新测试用例状态"""
        try:
            async with db_manager.get_session() as session:
                success_count = 0
                failed_count = 0
                
                for test_case_id in test_case_ids:
                    try:
                        success = await self.test_case_repository.update_test_case_status(
                            session, test_case_id, status, updated_by
                        )
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"更新测试用例 {test_case_id} 状态失败: {str(e)}")
                        failed_count += 1
                
                return {
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_count": len(test_case_ids)
                }
                
        except Exception as e:
            logger.error(f"批量更新测试用例状态失败: {str(e)}")
            return {
                "success_count": 0,
                "failed_count": len(test_case_ids),
                "total_count": len(test_case_ids),
                "error": str(e)
            }

    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.save_metrics["average_processing_time"]
        total_requests = self.save_metrics["total_requests"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.save_metrics["average_processing_time"] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total_requests = max(self.save_metrics["total_requests"], 1)
        successful_saves = self.save_metrics["successful_saves"]

        return {
            **self.save_metrics,
            "success_rate": (successful_saves / total_requests) * 100,
            "average_batch_size": (
                sum(self.save_metrics["batch_sizes"]) /
                max(len(self.save_metrics["batch_sizes"]), 1)
            ),
            "average_test_cases_per_request": (
                self.save_metrics["total_test_cases_saved"] /
                max(successful_saves, 1)
            ),
            "agent_name": self.agent_name,
            "agent_id": self.id.key
        }

    def reset_metrics(self):
        """重置性能指标"""
        self.save_metrics = {
            "total_requests": 0,
            "successful_saves": 0,
            "failed_saves": 0,
            "total_test_cases_saved": 0,
            "average_processing_time": 0.0,
            "batch_sizes": []
        }
        logger.info(f"已重置 {self.agent_name} 的性能指标")

    def update_save_config(self, config_updates: Dict[str, Any]):
        """更新保存配置"""
        for key, value in config_updates.items():
            if key in self.save_config:
                old_value = self.save_config[key]
                self.save_config[key] = value
                logger.info(f"更新保存配置 {key}: {old_value} → {value}")
            else:
                logger.warning(f"未知的配置项: {key}")

    def get_save_config(self) -> Dict[str, Any]:
        """获取当前保存配置"""
        return self.save_config.copy()

    async def validate_test_case_data(self, test_case_data: TestCaseData) -> Dict[str, Any]:
        """验证测试用例数据的完整性和有效性"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

        # 必填字段验证
        if not test_case_data.title or not test_case_data.title.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("测试用例标题不能为空")

        # 标题长度验证
        if test_case_data.title and len(test_case_data.title) > 500:
            validation_result["is_valid"] = False
            validation_result["errors"].append("测试用例标题长度不能超过500字符")

        # 测试步骤验证
        if not test_case_data.test_steps:
            validation_result["warnings"].append("测试步骤为空，建议添加详细的测试步骤")
        elif isinstance(test_case_data.test_steps, list) and len(test_case_data.test_steps) == 0:
            validation_result["warnings"].append("测试步骤列表为空")

        # 预期结果验证
        if not test_case_data.expected_results:
            validation_result["warnings"].append("预期结果为空，建议添加明确的预期结果")

        # 枚举值验证
        try:
            if test_case_data.test_type not in [t.value for t in TestType]:
                validation_result["errors"].append(f"无效的测试类型: {test_case_data.test_type}")
        except:
            validation_result["errors"].append("测试类型格式错误")

        try:
            if test_case_data.test_level not in [l.value for l in TestLevel]:
                validation_result["errors"].append(f"无效的测试级别: {test_case_data.test_level}")
        except:
            validation_result["errors"].append("测试级别格式错误")

        try:
            if test_case_data.priority not in [p.value for p in Priority]:
                validation_result["errors"].append(f"无效的优先级: {test_case_data.priority}")
        except:
            validation_result["errors"].append("优先级格式错误")

        # AI置信度验证
        if hasattr(test_case_data, 'ai_confidence') and test_case_data.ai_confidence is not None:
            if not (0 <= test_case_data.ai_confidence <= 1):
                validation_result["warnings"].append("AI置信度应该在0-1之间")

        # 提供改进建议
        if test_case_data.title and len(test_case_data.title) < 10:
            validation_result["suggestions"].append("建议测试用例标题更加详细和描述性")

        if not test_case_data.description:
            validation_result["suggestions"].append("建议添加测试用例描述以提高可读性")

        return validation_result

    async def clean_and_normalize_test_case_data(self, test_case_data: TestCaseData) -> TestCaseData:
        """清理和标准化测试用例数据"""
        try:
            # 清理标题
            if test_case_data.title:
                test_case_data.title = test_case_data.title.strip()
                # 移除多余的空格
                test_case_data.title = ' '.join(test_case_data.title.split())

            # 清理描述
            if test_case_data.description:
                test_case_data.description = test_case_data.description.strip()

            # 清理前置条件
            if test_case_data.preconditions:
                test_case_data.preconditions = self._normalize_string_field(test_case_data.preconditions)

            # 清理预期结果
            if test_case_data.expected_results:
                test_case_data.expected_results = self._normalize_string_field(test_case_data.expected_results)

            # 标准化测试步骤
            if test_case_data.test_steps:
                test_case_data.test_steps = await self._normalize_test_steps(test_case_data.test_steps)

            # 标准化标签
            if hasattr(test_case_data, 'tags') and test_case_data.tags:
                test_case_data.tags = self._normalize_tags(test_case_data.tags)

            return test_case_data

        except Exception as e:
            logger.warning(f"清理测试用例数据失败: {str(e)}")
            return test_case_data

    async def _normalize_test_steps(self, test_steps) -> List[Dict[str, Any]]:
        """标准化测试步骤格式"""
        if not test_steps:
            return []

        normalized_steps = []

        if isinstance(test_steps, str):
            # 如果是字符串，按行分割
            lines = test_steps.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    normalized_steps.append({
                        "step_number": i,
                        "action": line.strip(),
                        "data": "",
                        "expected": ""
                    })
        elif isinstance(test_steps, list):
            for i, step in enumerate(test_steps, 1):
                if isinstance(step, dict):
                    # 确保包含必要字段
                    normalized_step = {
                        "step_number": step.get("step_number", i),
                        "action": step.get("action", ""),
                        "data": step.get("data", ""),
                        "expected": step.get("expected", "")
                    }
                    normalized_steps.append(normalized_step)
                elif isinstance(step, str):
                    normalized_steps.append({
                        "step_number": i,
                        "action": step.strip(),
                        "data": "",
                        "expected": ""
                    })

        return normalized_steps

    def _normalize_tags(self, tags) -> List[str]:
        """标准化标签"""
        if not tags:
            return []

        normalized_tags = []

        if isinstance(tags, str):
            # 如果是字符串，按逗号分割
            tag_list = tags.split(',')
            for tag in tag_list:
                clean_tag = tag.strip()
                if clean_tag and clean_tag not in normalized_tags:
                    normalized_tags.append(clean_tag)
        elif isinstance(tags, list):
            for tag in tags:
                clean_tag = str(tag).strip()
                if clean_tag and clean_tag not in normalized_tags:
                    normalized_tags.append(clean_tag)

        return normalized_tags[:10]  # 限制最多10个标签

    async def validate_test_case_data(self, test_case_data: TestCaseData) -> Dict[str, Any]:
        """验证测试用例数据的完整性和有效性"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }

        # 必填字段验证
        if not test_case_data.title or not test_case_data.title.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("测试用例标题不能为空")

        # 标题长度验证
        if test_case_data.title and len(test_case_data.title) > 500:
            validation_result["is_valid"] = False
            validation_result["errors"].append("测试用例标题长度不能超过500字符")

        # 测试步骤验证
        if not test_case_data.test_steps:
            validation_result["warnings"].append("测试步骤为空，建议添加详细的测试步骤")
        elif isinstance(test_case_data.test_steps, list) and len(test_case_data.test_steps) == 0:
            validation_result["warnings"].append("测试步骤列表为空")

        # 预期结果验证
        if not test_case_data.expected_results:
            validation_result["warnings"].append("预期结果为空，建议添加明确的预期结果")

        # 枚举值验证
        try:
            if test_case_data.test_type not in [t.value for t in TestType]:
                validation_result["errors"].append(f"无效的测试类型: {test_case_data.test_type}")
        except:
            validation_result["errors"].append("测试类型格式错误")

        try:
            if test_case_data.test_level not in [l.value for l in TestLevel]:
                validation_result["errors"].append(f"无效的测试级别: {test_case_data.test_level}")
        except:
            validation_result["errors"].append("测试级别格式错误")

        try:
            if test_case_data.priority not in [p.value for p in Priority]:
                validation_result["errors"].append(f"无效的优先级: {test_case_data.priority}")
        except:
            validation_result["errors"].append("优先级格式错误")

        # AI置信度验证
        if hasattr(test_case_data, 'ai_confidence') and test_case_data.ai_confidence is not None:
            if not (0 <= test_case_data.ai_confidence <= 1):
                validation_result["warnings"].append("AI置信度应该在0-1之间")

        # 提供改进建议
        if test_case_data.title and len(test_case_data.title) < 10:
            validation_result["suggestions"].append("建议测试用例标题更加详细和描述性")

        if not test_case_data.description:
            validation_result["suggestions"].append("建议添加测试用例描述以提高可读性")

        return validation_result

    async def clean_and_normalize_test_case_data(self, test_case_data: TestCaseData) -> TestCaseData:
        """清理和标准化测试用例数据"""
        try:
            # 清理标题
            if test_case_data.title:
                test_case_data.title = test_case_data.title.strip()
                # 移除多余的空格
                test_case_data.title = ' '.join(test_case_data.title.split())

            # 清理描述
            if test_case_data.description:
                test_case_data.description = test_case_data.description.strip()

            # 清理前置条件
            if test_case_data.preconditions:
                test_case_data.preconditions = self._normalize_string_field(test_case_data.preconditions)

            # 清理预期结果
            if test_case_data.expected_results:
                test_case_data.expected_results = self._normalize_string_field(test_case_data.expected_results)

            # 标准化测试步骤
            if test_case_data.test_steps:
                test_case_data.test_steps = await self._normalize_test_steps(test_case_data.test_steps)

            # 标准化标签
            if hasattr(test_case_data, 'tags') and test_case_data.tags:
                test_case_data.tags = self._normalize_tags(test_case_data.tags)

            return test_case_data

        except Exception as e:
            logger.warning(f"清理测试用例数据失败: {str(e)}")
            return test_case_data

    async def _normalize_test_steps(self, test_steps) -> List[Dict[str, Any]]:
        """标准化测试步骤格式"""
        if not test_steps:
            return []

        normalized_steps = []

        if isinstance(test_steps, str):
            # 如果是字符串，按行分割
            lines = test_steps.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    normalized_steps.append({
                        "step_number": i,
                        "action": line.strip(),
                        "data": "",
                        "expected": ""
                    })
        elif isinstance(test_steps, list):
            for i, step in enumerate(test_steps, 1):
                if isinstance(step, dict):
                    # 确保包含必要字段
                    normalized_step = {
                        "step_number": step.get("step_number", i),
                        "action": step.get("action", ""),
                        "data": step.get("data", ""),
                        "expected": step.get("expected", "")
                    }
                    normalized_steps.append(normalized_step)
                elif isinstance(step, str):
                    normalized_steps.append({
                        "step_number": i,
                        "action": step.strip(),
                        "data": "",
                        "expected": ""
                    })

        return normalized_steps

    def _normalize_tags(self, tags) -> List[str]:
        """标准化标签"""
        if not tags:
            return []

        normalized_tags = []

        if isinstance(tags, str):
            # 如果是字符串，按逗号分割
            tag_list = tags.split(',')
            for tag in tag_list:
                clean_tag = tag.strip()
                if clean_tag and clean_tag not in normalized_tags:
                    normalized_tags.append(clean_tag)
        elif isinstance(tags, list):
            for tag in tags:
                clean_tag = str(tag).strip()
                if clean_tag and clean_tag not in normalized_tags:
                    normalized_tags.append(clean_tag)

        return normalized_tags[:10]  # 限制最多10个标签

    async def _save_test_case_requirements(
        self,
        session,
        test_case_id: str,
        test_case_data: TestCaseData,
        message: TestCaseSaveRequest
    ) -> None:
        """保存测试用例与需求的关联关系"""
        try:
            # 从测试用例数据中提取需求关联信息
            requirement_ids = []

            # 方法1: 从source_metadata中获取需求ID
            if hasattr(test_case_data, 'source_metadata') and test_case_data.source_metadata:
                if 'requirement_id' in test_case_data.source_metadata:
                    requirement_ids.append(test_case_data.source_metadata['requirement_id'])
                elif 'requirement_ids' in test_case_data.source_metadata:
                    requirement_ids.extend(test_case_data.source_metadata['requirement_ids'])

            # 方法2: 从message的requirement_mappings中获取
            if message.requirement_mappings:
                test_case_title = test_case_data.title
                if test_case_title in message.requirement_mappings:
                    requirement_ids.extend(message.requirement_mappings[test_case_title])

            # 方法3: 根据会话ID查找相关需求
            if not requirement_ids and message.session_id:
                session_requirements = await self.requirement_repository.get_requirements_by_session(
                    session, message.session_id
                )
                # 如果找到需求，建立关联（简单策略：关联所有同会话的需求）
                requirement_ids = [req.id for req in session_requirements]

            # 方法4: 智能匹配需求（基于关键词匹配）
            if not requirement_ids:
                requirement_ids = await self._smart_match_requirements(
                    session, test_case_data, message
                )

            # 去重并验证需求ID
            requirement_ids = await self._validate_requirement_ids(session, requirement_ids)

            # 保存关联关系
            if requirement_ids:
                await self.send_response(
                    f"🔗 正在关联 {len(requirement_ids)} 个需求到测试用例..."
                )

                await self.test_case_requirement_repository.batch_create_test_case_requirements(
                    session,
                    test_case_id,
                    requirement_ids,
                    coverage_type="full"
                )

                logger.info(f"成功关联 {len(requirement_ids)} 个需求到测试用例 {test_case_id}")
            else:
                logger.info(f"测试用例 {test_case_id} 没有找到相关需求进行关联")

        except Exception as e:
            logger.error(f"保存测试用例需求关联失败: {str(e)}")
            # 不抛出异常，避免影响测试用例的保存

    async def _smart_match_requirements(
        self,
        session,
        test_case_data: TestCaseData,
        message: TestCaseSaveRequest
    ) -> List[str]:
        """智能匹配相关需求"""
        try:
            # 提取测试用例关键词
            keywords = self._extract_keywords_from_test_case(test_case_data)

            if not keywords:
                return []

            # 搜索匹配的需求
            matched_requirements = await self.requirement_repository.search_requirements_by_keywords(
                session, keywords, message.project_id
            )

            return [req.id for req in matched_requirements[:5]]  # 最多关联5个需求

        except Exception as e:
            logger.warning(f"智能匹配需求失败: {str(e)}")
            return []

    def _extract_keywords_from_test_case(self, test_case_data: TestCaseData) -> List[str]:
        """从测试用例中提取关键词"""
        keywords = []

        # 从标题中提取关键词
        if test_case_data.title:
            title_words = test_case_data.title.split()
            keywords.extend([word for word in title_words if len(word) > 2])

        # 从描述中提取关键词
        if test_case_data.description:
            desc_words = test_case_data.description.split()
            keywords.extend([word for word in desc_words if len(word) > 2])

        # 去重并返回前10个关键词
        return list(set(keywords))[:10]

    async def _validate_requirement_ids(self, session, requirement_ids: List[str]) -> List[str]:
        """验证需求ID的有效性"""
        if not requirement_ids:
            return []

        try:
            # 去重
            unique_ids = list(set(requirement_ids))

            # 验证需求是否存在
            valid_ids = []
            for req_id in unique_ids:
                if await self.requirement_repository.requirement_exists(session, req_id):
                    valid_ids.append(req_id)
                else:
                    logger.warning(f"需求ID不存在: {req_id}")

            return valid_ids

        except Exception as e:
            logger.error(f"验证需求ID失败: {str(e)}")
            return []

    async def _log_save_error(self, test_case_data: TestCaseData, error: Exception, index: int):
        """记录保存错误的详细信息"""
        try:
            error_info = {
                "index": index,
                "title": test_case_data.title,
                "test_type": test_case_data.test_type,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.now().isoformat()
            }

            # 记录到日志文件
            logger.error(f"测试用例保存错误详情: {json.dumps(error_info, ensure_ascii=False, indent=2)}")

        except Exception as e:
            logger.error(f"记录保存错误失败: {str(e)}")

    async def get_save_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取保存统计信息"""
        try:
            async with db_manager.get_session() as session:
                from app.database.models.test_case import TestCase
                from sqlalchemy import select, func

                # 总数统计
                total_count_query = select(func.count(TestCase.id))
                if session_id:
                    total_count_query = total_count_query.where(TestCase.session_id == session_id)

                total_result = await session.execute(total_count_query)
                total_count = total_result.scalar()

                # AI生成统计
                ai_generated_query = select(func.count(TestCase.id)).where(
                    TestCase.ai_generated == True
                )
                if session_id:
                    ai_generated_query = ai_generated_query.where(TestCase.session_id == session_id)

                ai_result = await session.execute(ai_generated_query)
                ai_generated_count = ai_result.scalar()

                return {
                    "total_count": total_count,
                    "ai_generated_count": ai_generated_count,
                    "manual_count": total_count - ai_generated_count,
                    "session_id": session_id,
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"获取保存统计信息失败: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

    async def _log_save_error(self, test_case_data: TestCaseData, error: Exception, index: int):
        """记录保存错误的详细信息"""
        try:
            error_info = {
                "index": index,
                "title": test_case_data.title,
                "test_type": test_case_data.test_type,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.now().isoformat()
            }

            # 记录到日志文件
            logger.error(f"测试用例保存错误详情: {json.dumps(error_info, ensure_ascii=False, indent=2)}")

        except Exception as e:
            logger.error(f"记录保存错误失败: {str(e)}")

    async def get_save_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取保存统计信息"""
        try:
            async with db_manager.get_session() as session:
                from app.database.models.test_case import TestCase
                from sqlalchemy import select, func

                # 基础查询
                base_query = select(TestCase)
                if session_id:
                    base_query = base_query.where(TestCase.session_id == session_id)

                # 总数统计
                total_count_query = select(func.count(TestCase.id))
                if session_id:
                    total_count_query = total_count_query.where(TestCase.session_id == session_id)

                total_result = await session.execute(total_count_query)
                total_count = total_result.scalar()

                # 按状态统计
                status_query = select(
                    TestCase.status,
                    func.count(TestCase.id).label('count')
                ).group_by(TestCase.status)

                if session_id:
                    status_query = status_query.where(TestCase.session_id == session_id)

                status_result = await session.execute(status_query)
                status_stats = {row.status.value: row.count for row in status_result}

                # AI生成统计
                ai_generated_query = select(func.count(TestCase.id)).where(
                    TestCase.ai_generated == True
                )
                if session_id:
                    ai_generated_query = ai_generated_query.where(TestCase.session_id == session_id)

                ai_result = await session.execute(ai_generated_query)
                ai_generated_count = ai_result.scalar()

                return {
                    "total_count": total_count,
                    "ai_generated_count": ai_generated_count,
                    "manual_count": total_count - ai_generated_count,
                    "status_distribution": status_stats,
                    "session_id": session_id,
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"获取保存统计信息失败: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
