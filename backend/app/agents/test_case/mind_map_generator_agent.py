"""
思维导图生成智能体 - 优化版本
专门负责根据测试用例生成专业的思维导图数据
遵循单一职责原则，专注于思维导图的生成和布局计算
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
from app.core.messages.test_case import (
    MindMapGenerationRequest, MindMapGenerationResponse,
    MindMapData, MindMapNode, MindMapEdge
)
from app.database.models.test_case import MindMap
from app.database.connection import db_manager

class MindMapGenerationResult(BaseModel):
    """思维导图生成结果"""
    mind_map_id: str = Field(..., description="思维导图ID")
    nodes_count: int = Field(0, description="节点数量")
    edges_count: int = Field(0, description="边数量")
    layout_type: str = Field("hierarchical", description="布局类型")
    processing_time: float = Field(0.0, description="处理时间")
    nodes: List[MindMapNode] = Field(default_factory=list, description="思维导图节点列表")
    edges: List[MindMapEdge] = Field(default_factory=list, description="思维导图边列表")
    layout_config: Dict[str, Any] = Field(default_factory=dict, description="布局配置")


@type_subscription(topic_type=TopicTypes.MIND_MAP_GENERATOR.value)
class MindMapGeneratorAgent(BaseAgent):
    """
    思维导图生成智能体 - 优化版本

    职责：
    1. 接收思维导图生成请求
    2. 分析测试用例结构
    3. 生成节点和边数据
    4. 计算布局配置
    5. 保存思维导图到数据库

    设计原则：
    - 单一职责：专注于思维导图生成
    - 模块化设计：布局算法可扩展
    - 错误处理：统一的异常处理机制
    - 性能优化：支持大量测试用例的处理
    """

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化思维导图生成智能体"""
        super().__init__(
            agent_id=AgentTypes.MIND_MAP_GENERATOR.value,
            agent_name=AGENT_NAMES.get(AgentTypes.MIND_MAP_GENERATOR.value, "思维导图生成智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )

        # 支持的布局类型
        self.layout_types = {
            "hierarchical": self._generate_hierarchical_layout,
            "radial": self._generate_radial_layout,
            "force": self._generate_force_layout,
            "tree": self._generate_tree_layout
        }

        # 初始化性能指标
        self.mind_map_metrics = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0,
            "total_nodes_generated": 0,
            "total_edges_generated": 0
        }

        # 布局配置
        self.layout_config = {
            "max_nodes_per_level": 20,
            "node_spacing": {"x": 80, "y": 60},
            "level_spacing": 120,
            "default_layout": "hierarchical"
        }

        logger.info(f"思维导图生成智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_mind_map_generation_request(
        self,
        message: MindMapGenerationRequest,
        ctx: MessageContext
    ) -> None:
        """
        处理思维导图生成请求 - 优化版本

        流程：
        1. 获取测试用例数据
        2. 分析测试用例结构
        3. 生成思维导图节点和边
        4. 计算布局配置
        5. 保存到数据库
        6. 返回响应
        """
        start_time = datetime.now()
        self.mind_map_metrics["total_requests"] += 1

        try:
            logger.info(f"开始处理思维导图生成请求: {message.session_id}")

            await self.send_response(
                f"🧠 开始生成思维导图，测试用例数量: {len(message.test_case_ids)}",
                region="process"
            )

            # 步骤1: 获取测试用例数据
            test_cases_data = await self._fetch_test_cases_data(message.test_case_ids)

            if not test_cases_data:
                await self._handle_empty_test_cases(message)
                return

            # 步骤2: 生成思维导图
            mind_map_result = await self._generate_mind_map(test_cases_data, message)

            # 步骤3: 保存思维导图
            saved_mind_map = await self._save_mind_map_to_database(mind_map_result, message)

            # 步骤4: 发送成功响应
            await self._send_success_response(message, mind_map_result, saved_mind_map)

            # 更新成功指标
            self.mind_map_metrics["successful_generations"] += 1
            self.mind_map_metrics["total_nodes_generated"] += mind_map_result.nodes_count
            self.mind_map_metrics["total_edges_generated"] += mind_map_result.edges_count
            self._update_average_processing_time(start_time)

        except Exception as e:
            await self._handle_generation_error(message, e)
            self.mind_map_metrics["failed_generations"] += 1

    async def _handle_empty_test_cases(self, message: MindMapGenerationRequest):
        """处理空测试用例情况"""
        await self.send_response(
            "⚠️ 未找到测试用例数据，无法生成思维导图",
            is_final=True
        )
        logger.warning(f"思维导图生成请求中没有测试用例数据: {message.session_id}")

    async def _send_success_response(
        self,
        message: MindMapGenerationRequest,
        mind_map_result: MindMapGenerationResult,
        saved_mind_map: Dict[str, Any]
    ):
        """发送成功响应"""
        response = MindMapGenerationResponse(
            session_id=message.session_id,
            mind_map_id=mind_map_result.mind_map_id,
            mind_map_data=saved_mind_map["mind_map_data"],
            layout_config=saved_mind_map["layout_config"],
            nodes_count=mind_map_result.nodes_count,
            edges_count=mind_map_result.edges_count,
            processing_time=mind_map_result.processing_time,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            f"✅ 思维导图生成完成，包含 {mind_map_result.nodes_count} 个节点",
            is_final=False,
            result=response.model_dump()
        )

    async def _handle_generation_error(self, message: MindMapGenerationRequest, error: Exception):
        """处理生成错误"""
        error_response = MindMapGenerationResponse(
            session_id=message.session_id,
            mind_map_id="",
            mind_map_data={"nodes": [], "edges": []},
            layout_config={},
            nodes_count=0,
            edges_count=0,
            processing_time=0.0,
            created_at=datetime.now().isoformat()
        )

        await self.send_response(
            f"❌ 思维导图生成失败: {str(error)}",
            is_final=True,
            result=error_response.model_dump()
        )

        logger.error(f"思维导图生成失败: {message.session_id}, 错误: {str(error)}")

    def _update_average_processing_time(self, start_time: datetime):
        """更新平均处理时间"""
        processing_time = (datetime.now() - start_time).total_seconds()
        current_avg = self.mind_map_metrics["average_processing_time"]
        total_requests = self.mind_map_metrics["total_requests"]

        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.mind_map_metrics["average_processing_time"] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.mind_map_metrics,
            "success_rate": (
                self.mind_map_metrics["successful_generations"] /
                max(self.mind_map_metrics["total_requests"], 1)
            ) * 100,
            "average_nodes_per_map": (
                self.mind_map_metrics["total_nodes_generated"] /
                max(self.mind_map_metrics["successful_generations"], 1)
            ),
            "average_edges_per_map": (
                self.mind_map_metrics["total_edges_generated"] /
                max(self.mind_map_metrics["successful_generations"], 1)
            ),
            "agent_name": self.agent_name,
            "agent_id": self.id.key
        }

    async def _fetch_test_cases_data(self, test_case_ids: List[str]) -> List[Dict[str, Any]]:
        """获取测试用例数据"""
        try:
            test_cases_data = []
            
            async with db_manager.get_session() as session:
                from app.database.models.test_case import TestCase
                from sqlalchemy import select
                
                # 查询测试用例
                stmt = select(TestCase).where(TestCase.id.in_(test_case_ids))
                result = await session.execute(stmt)
                test_cases = result.scalars().all()
                
                for test_case in test_cases:
                    test_cases_data.append({
                        "id": test_case.id,
                        "title": test_case.title,
                        "description": test_case.description,
                        "test_type": test_case.test_type.value,
                        "test_level": test_case.test_level.value,
                        "priority": test_case.priority.value,
                        "test_steps": test_case.test_steps,
                        "tags": []  # TODO: 获取标签
                    })
            
            logger.info(f"获取到 {len(test_cases_data)} 个测试用例数据")
            return test_cases_data
            
        except Exception as e:
            logger.error(f"获取测试用例数据失败: {str(e)}")
            raise

    async def _generate_mind_map(
        self, 
        test_cases_data: List[Dict[str, Any]], 
        message: MindMapGenerationRequest
    ) -> MindMapGenerationResult:
        """生成思维导图"""
        try:
            start_time = datetime.now()
            
            await self.send_response("🎨 正在分析测试用例结构...")
            
            # 分析测试用例结构
            structure_analysis = await self._analyze_test_case_structure(test_cases_data)
            
            await self.send_response("🔗 正在生成节点和连接...")
            
            # 生成节点和边
            nodes, edges = await self._generate_nodes_and_edges(
                test_cases_data, structure_analysis, message
            )
            
            await self.send_response("📐 正在计算布局...")
            
            # 计算布局
            layout_type = message.generation_config.get("layout_type", "hierarchical")
            layout_config = await self._calculate_layout(nodes, edges, layout_type)
            
            # 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = MindMapGenerationResult(
                mind_map_id=str(uuid.uuid4()),
                nodes_count=len(nodes),
                edges_count=len(edges),
                layout_type=layout_type,
                processing_time=processing_time,
                nodes=nodes,
                edges=edges,
                layout_config=layout_config
            )
            
            logger.info(f"思维导图生成完成: {result.nodes_count} 节点, {result.edges_count} 边")
            return result
            
        except Exception as e:
            logger.error(f"生成思维导图失败: {str(e)}")
            raise

    async def _analyze_test_case_structure(
        self,
        test_cases_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析测试用例结构"""
        try:
            structure = {
                "test_types": {},
                "test_levels": {},
                "priorities": {},
                "categories": {},
                "total_count": len(test_cases_data)
            }

            for test_case in test_cases_data:
                # 统计测试类型（兼容不同的字段名）
                test_type = test_case.get("test_type") or test_case.get("type") or "功能测试"
                structure["test_types"][test_type] = structure["test_types"].get(test_type, 0) + 1

                # 统计测试级别（兼容不同的字段名）
                test_level = test_case.get("test_level") or test_case.get("level") or "基础"
                structure["test_levels"][test_level] = structure["test_levels"].get(test_level, 0) + 1

                # 统计优先级
                priority = test_case.get("priority", "P2")
                structure["priorities"][priority] = structure["priorities"].get(priority, 0) + 1

                # 统计分类
                category = test_case.get("category", "其他")
                structure["categories"][category] = structure["categories"].get(category, 0) + 1

            return structure

        except Exception as e:
            logger.error(f"分析测试用例结构失败: {str(e)}")
            raise

    async def _generate_nodes_and_edges(
        self, 
        test_cases_data: List[Dict[str, Any]], 
        structure_analysis: Dict[str, Any],
        message: MindMapGenerationRequest
    ) -> tuple[List[MindMapNode], List[MindMapEdge]]:
        """生成节点和边"""
        try:
            nodes = []
            edges = []
            
            # 创建根节点
            root_node = MindMapNode(
                id="root",
                label="测试用例总览",
                type="root",
                level=0,
                data={
                    "total_count": structure_analysis["total_count"],
                    "description": f"共 {structure_analysis['total_count']} 个测试用例"
                },
                style={
                    "backgroundColor": "#1890ff",
                    "color": "#ffffff",
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            )
            nodes.append(root_node)
            
            # 按测试类型分组
            type_nodes = {}
            for test_type, count in structure_analysis["test_types"].items():
                type_node_id = f"type_{test_type}"
                type_node = MindMapNode(
                    id=type_node_id,
                    label=f"{self._get_test_type_label(test_type)} ({count})",
                    type="category",
                    level=1,
                    data={
                        "test_type": test_type,
                        "count": count
                    },
                    style={
                        "backgroundColor": self._get_test_type_color(test_type),
                        "color": "#ffffff"
                    }
                )
                nodes.append(type_node)
                type_nodes[test_type] = type_node_id
                
                # 连接到根节点
                edges.append(MindMapEdge(
                    id=f"edge_root_{type_node_id}",
                    source="root",
                    target=type_node_id,
                    type="default"
                ))
            
            # 创建测试用例节点
            for test_case in test_cases_data:
                # 获取测试用例的各种属性，提供默认值
                test_case_id = test_case.get("id", str(uuid.uuid4()))
                title = test_case.get("title", "未命名测试用例")
                description = test_case.get("description", "")
                priority = test_case.get("priority", "P2")
                test_level = test_case.get("test_level") or test_case.get("level", "基础")
                test_type = test_case.get("test_type") or test_case.get("type", "功能测试")
                test_steps = test_case.get("test_steps", test_case.get("steps", []))

                test_case_node = MindMapNode(
                    id=test_case_id,
                    label=title,
                    type="test_case",
                    level=2,
                    data={
                        "test_case_id": test_case_id,
                        "description": description,
                        "priority": priority,
                        "test_level": test_level,
                        "test_steps_count": len(test_steps)
                    },
                    style={
                        "backgroundColor": self._get_priority_color(priority),
                        "color": "#333333",
                        "border": f"2px solid {self._get_test_type_color(test_type)}"
                    }
                )
                nodes.append(test_case_node)

                # 连接到对应的类型节点
                parent_type_node = type_nodes[test_type]
                edges.append(MindMapEdge(
                    id=f"edge_{parent_type_node}_{test_case_id}",
                    source=parent_type_node,
                    target=test_case_id,
                    type="default"
                ))
            
            return nodes, edges
            
        except Exception as e:
            logger.error(f"生成节点和边失败: {str(e)}")
            raise

    async def _calculate_layout(
        self, 
        nodes: List[MindMapNode], 
        edges: List[MindMapEdge], 
        layout_type: str
    ) -> Dict[str, Any]:
        """计算布局"""
        try:
            if layout_type in self.layout_types:
                layout_func = self.layout_types[layout_type]
                return await layout_func(nodes, edges)
            else:
                # 默认使用层次布局
                return await self._generate_hierarchical_layout(nodes, edges)
                
        except Exception as e:
            logger.error(f"计算布局失败: {str(e)}")
            # 返回默认布局配置
            return {
                "type": "hierarchical",
                "direction": "TB",
                "spacing": {"node": [50, 50], "rank": 100}
            }

    async def _generate_hierarchical_layout(
        self, 
        nodes: List[MindMapNode], 
        edges: List[MindMapEdge]
    ) -> Dict[str, Any]:
        """生成层次布局"""
        return {
            "type": "hierarchical",
            "direction": "TB",  # Top to Bottom
            "spacing": {
                "node": [80, 60],
                "rank": 120
            },
            "align": "center",
            "sortMethod": "directed"
        }

    async def _generate_radial_layout(
        self, 
        nodes: List[MindMapNode], 
        edges: List[MindMapEdge]
    ) -> Dict[str, Any]:
        """生成放射布局"""
        return {
            "type": "radial",
            "center": "root",
            "radius": 200,
            "spacing": 50
        }

    async def _generate_force_layout(
        self, 
        nodes: List[MindMapNode], 
        edges: List[MindMapEdge]
    ) -> Dict[str, Any]:
        """生成力导向布局"""
        return {
            "type": "force",
            "linkDistance": 150,
            "nodeStrength": -300,
            "edgeStrength": 0.6,
            "collideStrength": 0.8
        }

    async def _generate_tree_layout(
        self, 
        nodes: List[MindMapNode], 
        edges: List[MindMapEdge]
    ) -> Dict[str, Any]:
        """生成树形布局"""
        return {
            "type": "tree",
            "direction": "LR",  # Left to Right
            "spacing": [100, 50],
            "align": "center"
        }

    def _get_test_type_label(self, test_type: str) -> str:
        """获取测试类型标签"""
        labels = {
            "functional": "功能测试",
            "performance": "性能测试",
            "security": "安全测试",
            "compatibility": "兼容性测试",
            "usability": "可用性测试",
            "interface": "接口测试",
            "database": "数据库测试"
        }
        return labels.get(test_type, test_type)

    def _get_test_type_color(self, test_type: str) -> str:
        """获取测试类型颜色"""
        colors = {
            "functional": "#52c41a",
            "performance": "#fa8c16",
            "security": "#f5222d",
            "compatibility": "#722ed1",
            "usability": "#13c2c2",
            "interface": "#1890ff",
            "database": "#eb2f96"
        }
        return colors.get(test_type, "#666666")

    def _get_priority_color(self, priority: str) -> str:
        """获取优先级颜色"""
        colors = {
            "P0": "#ff4d4f",
            "P1": "#ff7a45",
            "P2": "#ffa940",
            "P3": "#ffec3d",
            "P4": "#bae637"
        }
        return colors.get(priority, "#d9d9d9")

    async def _save_mind_map_to_database(
        self, 
        mind_map_result: MindMapGenerationResult,
        message: MindMapGenerationRequest
    ) -> Dict[str, Any]:
        """保存思维导图到数据库"""
        try:
            mind_map_data = {
                "nodes": [node.model_dump() for node in mind_map_result.nodes],
                "edges": [edge.model_dump() for edge in mind_map_result.edges]
            }
            
            async with db_manager.get_session() as session:
                # 创建思维导图记录 (一个会话一个思维导图)
                mind_map = MindMap(
                    id=str(uuid.uuid4()),
                    name=f"测试用例思维导图 - {message.session_id[:8]}",
                    session_id=message.session_id,
                    project_id=getattr(message, 'project_id', None),
                    mind_map_data=mind_map_data,
                    layout_config=mind_map_result.layout_config
                )
                session.add(mind_map)

                await session.commit()
                
            logger.info(f"思维导图已保存到数据库: {mind_map_result.mind_map_id}")
            
            return {
                "mind_map_data": mind_map_data,
                "layout_config": mind_map_result.layout_config
            }
            
        except Exception as e:
            logger.error(f"保存思维导图到数据库失败: {str(e)}")
            raise
