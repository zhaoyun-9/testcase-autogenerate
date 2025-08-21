"""
数据库Schema解析智能体
负责解析数据库表结构，生成数据测试用例
"""
import uuid
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from autogen_core import message_handler, type_subscription, MessageContext, TopicId
from loguru import logger
from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.types import TopicTypes, AgentTypes, AGENT_NAMES
from app.core.messages.test_case import (
    DatabaseSchemaParseRequest, DatabaseSchemaParseResponse,
    TestCaseData
)
from app.core.enums import TestType, TestLevel, Priority, InputSource


class DatabaseColumn(BaseModel):
    """数据库列信息"""
    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")
    is_nullable: bool = Field(True, description="是否可为空")
    is_primary_key: bool = Field(False, description="是否主键")
    is_foreign_key: bool = Field(False, description="是否外键")
    default_value: Optional[str] = Field(None, description="默认值")
    max_length: Optional[int] = Field(None, description="最大长度")
    constraints: List[str] = Field(default_factory=list, description="约束条件")
    comment: str = Field("", description="列注释")


class DatabaseTable(BaseModel):
    """数据库表信息"""
    name: str = Field(..., description="表名")
    schema: str = Field("", description="模式名")
    columns: List[DatabaseColumn] = Field(default_factory=list, description="列信息")
    primary_keys: List[str] = Field(default_factory=list, description="主键列")
    foreign_keys: List[Dict[str, str]] = Field(default_factory=list, description="外键关系")
    indexes: List[Dict[str, Any]] = Field(default_factory=list, description="索引信息")
    comment: str = Field("", description="表注释")


class DatabaseSchemaParseResult(BaseModel):
    """数据库Schema解析结果"""
    database_type: str = Field("", description="数据库类型")
    database_name: str = Field("", description="数据库名称")
    tables: List[DatabaseTable] = Field(default_factory=list, description="表列表")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="表关系")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="约束信息")
    confidence_score: float = Field(0.0, description="解析置信度")


@type_subscription(topic_type=TopicTypes.DATABASE_SCHEMA_PARSER.value)
class DatabaseSchemaParserAgent(BaseAgent):
    """数据库Schema解析智能体，负责解析数据库表结构"""

    def __init__(self, model_client_instance=None, **kwargs):
        """初始化数据库Schema解析智能体"""
        super().__init__(
            agent_id=AgentTypes.DATABASE_SCHEMA_PARSER.value,
            agent_name=AGENT_NAMES.get(AgentTypes.DATABASE_SCHEMA_PARSER.value, "数据库Schema解析智能体"),
            model_client_instance=model_client_instance,
            **kwargs
        )
        
        # 支持的数据库类型
        self.supported_databases = {
            'mysql': self._parse_mysql_schema,
            'postgresql': self._parse_postgresql_schema,
            'oracle': self._parse_oracle_schema,
            'sqlserver': self._parse_sqlserver_schema,
            'sqlite': self._parse_sqlite_schema
        }
        
        logger.info(f"数据库Schema解析智能体初始化完成: {self.agent_name}")

    @message_handler
    async def handle_database_schema_parse_request(
        self, 
        message: DatabaseSchemaParseRequest, 
        ctx: MessageContext
    ) -> None:
        """处理数据库Schema解析请求"""
        try:
            logger.info(f"开始处理数据库Schema解析请求: {message.session_id}")
            
            await self.send_response(
                f"🔍 开始解析数据库Schema: {message.database_name}",
                region="process"
            )
            
            # 解析数据库Schema
            parse_result = await self._parse_database_schema(message)
            
            # 生成测试用例
            test_cases = await self._generate_test_cases_from_schema(
                parse_result, message
            )
            
            # 构建响应
            response = DatabaseSchemaParseResponse(
                session_id=message.session_id,
                schema_id=str(uuid.uuid4()),
                database_name=message.database_name,
                database_type=message.database_type,
                parse_result=parse_result.model_dump(),
                test_cases=test_cases,
                processing_time=0.0,
                created_at=datetime.now().isoformat()
            )
            
            await self.send_response(
                f"✅ 数据库Schema解析完成，发现 {len(parse_result.tables)} 个表",
                is_final=True,
                result=response.model_dump()
            )
            
            # 发送到测试点提取智能体
            await self._send_to_test_point_extractor(response)
            
        except Exception as e:
            logger.error(f"数据库Schema解析失败: {str(e)}")
            await self.send_response(
                f"❌ 数据库Schema解析失败: {str(e)}",
                is_final=True,
                error=str(e)
            )

    async def _parse_database_schema(
        self, 
        message: DatabaseSchemaParseRequest
    ) -> DatabaseSchemaParseResult:
        """解析数据库Schema"""
        try:
            database_type = message.database_type.lower()
            
            if database_type not in self.supported_databases:
                raise ValueError(f"不支持的数据库类型: {database_type}")
            
            await self.send_response(f"📊 正在解析 {database_type} 数据库Schema...")
            
            # 根据输入类型选择解析方法
            if message.schema_file_path:
                # 从文件解析
                parse_result = await self._parse_schema_from_file(message)
            elif message.connection_string:
                # 从数据库连接解析
                parse_result = await self._parse_schema_from_connection(message)
            elif message.schema_sql:
                # 从SQL语句解析
                parse_result = await self._parse_schema_from_sql(message)
            else:
                raise ValueError("缺少Schema数据源")
            
            return parse_result
            
        except Exception as e:
            logger.error(f"数据库Schema解析失败: {str(e)}")
            raise

    async def _parse_schema_from_file(
        self, 
        message: DatabaseSchemaParseRequest
    ) -> DatabaseSchemaParseResult:
        """从文件解析Schema"""
        try:
            with open(message.schema_file_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            return await self._parse_schema_content(schema_content, message)
            
        except Exception as e:
            logger.error(f"从文件解析Schema失败: {str(e)}")
            raise

    async def _parse_schema_from_connection(
        self, 
        message: DatabaseSchemaParseRequest
    ) -> DatabaseSchemaParseResult:
        """从数据库连接解析Schema"""
        try:
            # 这里需要实现实际的数据库连接逻辑
            # 暂时返回模拟结果
            await self.send_response("⚠️ 数据库连接解析功能开发中，使用模拟数据")
            
            return DatabaseSchemaParseResult(
                database_type=message.database_type,
                database_name=message.database_name,
                tables=[],
                relationships=[],
                constraints=[],
                confidence_score=0.5
            )
            
        except Exception as e:
            logger.error(f"从数据库连接解析Schema失败: {str(e)}")
            raise

    async def _parse_schema_from_sql(
        self, 
        message: DatabaseSchemaParseRequest
    ) -> DatabaseSchemaParseResult:
        """从SQL语句解析Schema"""
        try:
            return await self._parse_schema_content(message.schema_sql, message)
            
        except Exception as e:
            logger.error(f"从SQL语句解析Schema失败: {str(e)}")
            raise

    async def _parse_schema_content(
        self, 
        schema_content: str, 
        message: DatabaseSchemaParseRequest
    ) -> DatabaseSchemaParseResult:
        """解析Schema内容"""
        try:
            database_type = message.database_type.lower()
            parser_func = self.supported_databases[database_type]
            
            # 调用对应的解析方法
            tables = await parser_func(schema_content)
            
            # 分析表关系
            relationships = await self._analyze_table_relationships(tables)
            
            # 提取约束信息
            constraints = await self._extract_constraints(tables)
            
            return DatabaseSchemaParseResult(
                database_type=database_type,
                database_name=message.database_name,
                tables=tables,
                relationships=relationships,
                constraints=constraints,
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"解析Schema内容失败: {str(e)}")
            raise

    async def _parse_mysql_schema(self, schema_content: str) -> List[DatabaseTable]:
        """解析MySQL Schema"""
        try:
            tables = []
            
            # 使用正则表达式解析CREATE TABLE语句
            table_pattern = r'CREATE TABLE\s+(?:`?(\w+)`?)\s*\((.*?)\)(?:\s*ENGINE\s*=\s*\w+)?(?:\s*DEFAULT\s+CHARSET\s*=\s*\w+)?(?:\s*COMMENT\s*=\s*[\'"]([^\'"]*)[\'"])?'
            
            for match in re.finditer(table_pattern, schema_content, re.IGNORECASE | re.DOTALL):
                table_name = match.group(1)
                columns_def = match.group(2)
                table_comment = match.group(3) or ""
                
                # 解析列定义
                columns = await self._parse_mysql_columns(columns_def)
                
                # 提取主键和外键
                primary_keys = [col.name for col in columns if col.is_primary_key]
                foreign_keys = [
                    {"column": col.name, "references": "unknown"}
                    for col in columns if col.is_foreign_key
                ]
                
                table = DatabaseTable(
                    name=table_name,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    comment=table_comment
                )
                tables.append(table)
            
            return tables
            
        except Exception as e:
            logger.error(f"解析MySQL Schema失败: {str(e)}")
            return []

    async def _parse_mysql_columns(self, columns_def: str) -> List[DatabaseColumn]:
        """解析MySQL列定义"""
        try:
            columns = []
            
            # 分割列定义
            column_lines = [line.strip() for line in columns_def.split(',')]
            
            for line in column_lines:
                if not line or line.upper().startswith(('PRIMARY KEY', 'FOREIGN KEY', 'KEY', 'INDEX')):
                    continue
                
                # 解析列定义
                column = await self._parse_mysql_column_line(line)
                if column:
                    columns.append(column)
            
            return columns
            
        except Exception as e:
            logger.error(f"解析MySQL列定义失败: {str(e)}")
            return []

    async def _parse_mysql_column_line(self, line: str) -> Optional[DatabaseColumn]:
        """解析MySQL单个列定义"""
        try:
            # 简化的列解析逻辑
            parts = line.split()
            if len(parts) < 2:
                return None
            
            column_name = parts[0].strip('`')
            data_type = parts[1]
            
            # 检查约束
            is_nullable = 'NOT NULL' not in line.upper()
            is_primary_key = 'PRIMARY KEY' in line.upper()
            is_auto_increment = 'AUTO_INCREMENT' in line.upper()
            
            # 提取注释
            comment_match = re.search(r"COMMENT\s+['\"]([^'\"]*)['\"]", line, re.IGNORECASE)
            comment = comment_match.group(1) if comment_match else ""
            
            return DatabaseColumn(
                name=column_name,
                data_type=data_type,
                is_nullable=is_nullable,
                is_primary_key=is_primary_key,
                constraints=['AUTO_INCREMENT'] if is_auto_increment else [],
                comment=comment
            )
            
        except Exception as e:
            logger.warning(f"解析列定义失败: {line}, 错误: {str(e)}")
            return None

    async def _parse_postgresql_schema(self, schema_content: str) -> List[DatabaseTable]:
        """解析PostgreSQL Schema"""
        # 简化实现，实际应该更复杂
        return await self._parse_mysql_schema(schema_content)

    async def _parse_oracle_schema(self, schema_content: str) -> List[DatabaseTable]:
        """解析Oracle Schema"""
        # 简化实现，实际应该更复杂
        return await self._parse_mysql_schema(schema_content)

    async def _parse_sqlserver_schema(self, schema_content: str) -> List[DatabaseTable]:
        """解析SQL Server Schema"""
        # 简化实现，实际应该更复杂
        return await self._parse_mysql_schema(schema_content)

    async def _parse_sqlite_schema(self, schema_content: str) -> List[DatabaseTable]:
        """解析SQLite Schema"""
        # 简化实现，实际应该更复杂
        return await self._parse_mysql_schema(schema_content)

    async def _analyze_table_relationships(
        self, 
        tables: List[DatabaseTable]
    ) -> List[Dict[str, Any]]:
        """分析表关系"""
        try:
            relationships = []
            
            for table in tables:
                for fk in table.foreign_keys:
                    relationship = {
                        "from_table": table.name,
                        "from_column": fk["column"],
                        "to_table": fk.get("references", "unknown"),
                        "relationship_type": "one_to_many"
                    }
                    relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"分析表关系失败: {str(e)}")
            return []

    async def _extract_constraints(
        self, 
        tables: List[DatabaseTable]
    ) -> List[Dict[str, Any]]:
        """提取约束信息"""
        try:
            constraints = []
            
            for table in tables:
                for column in table.columns:
                    if column.constraints:
                        constraint = {
                            "table": table.name,
                            "column": column.name,
                            "constraints": column.constraints
                        }
                        constraints.append(constraint)
            
            return constraints
            
        except Exception as e:
            logger.error(f"提取约束信息失败: {str(e)}")
            return []

    async def _generate_test_cases_from_schema(
        self, 
        parse_result: DatabaseSchemaParseResult,
        message: DatabaseSchemaParseRequest
    ) -> List[TestCaseData]:
        """从数据库Schema生成测试用例"""
        test_cases = []
        
        try:
            # 为每个表生成测试用例
            for table in parse_result.tables:
                # 数据插入测试
                insert_test_case = TestCaseData(
                    title=f"测试 {table.name} 表数据插入",
                    description=f"测试向 {table.name} 表插入数据的功能",
                    test_type=TestType.DATABASE,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P1,
                    input_source=InputSource.DATABASE_SCHEMA,
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(insert_test_case)
                
                # 数据查询测试
                select_test_case = TestCaseData(
                    title=f"测试 {table.name} 表数据查询",
                    description=f"测试从 {table.name} 表查询数据的功能",
                    test_type=TestType.DATABASE,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P2,
                    input_source=InputSource.DATABASE_SCHEMA,
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(select_test_case)
                
                # 数据更新测试
                update_test_case = TestCaseData(
                    title=f"测试 {table.name} 表数据更新",
                    description=f"测试更新 {table.name} 表数据的功能",
                    test_type=TestType.DATABASE,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P2,
                    input_source=InputSource.DATABASE_SCHEMA,
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(update_test_case)
                
                # 数据删除测试
                delete_test_case = TestCaseData(
                    title=f"测试 {table.name} 表数据删除",
                    description=f"测试删除 {table.name} 表数据的功能",
                    test_type=TestType.DATABASE,
                    test_level=TestLevel.INTEGRATION,
                    priority=Priority.P2,
                    input_source=InputSource.DATABASE_SCHEMA,
                    source_metadata={
                        "database_name": message.database_name,
                        "table_name": table.name,
                        "test_focus": "delete"
                    },
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(delete_test_case)
                
                # 约束验证测试
                if any(col.constraints for col in table.columns):
                    constraint_test_case = TestCaseData(
                        title=f"测试 {table.name} 表约束验证",
                        description=f"测试 {table.name} 表的数据约束验证",
                        test_type=TestType.DATABASE,
                        test_level=TestLevel.INTEGRATION,
                        priority=Priority.P1,
                        input_source=InputSource.DATABASE_SCHEMA,
                        source_metadata={
                            "database_name": message.database_name,
                            "table_name": table.name,
                            "test_focus": "constraints"
                        },
                        ai_confidence=parse_result.confidence_score
                    )
                    test_cases.append(constraint_test_case)
            
            # 关系完整性测试
            if parse_result.relationships:
                relationship_test_case = TestCaseData(
                    title=f"测试 {parse_result.database_name} 数据库关系完整性",
                    description="测试数据库表之间的关系完整性",
                    test_type=TestType.DATABASE,
                    test_level=TestLevel.SYSTEM,
                    priority=Priority.P1,
                    input_source=InputSource.DATABASE_SCHEMA,
                    ai_confidence=parse_result.confidence_score
                )
                test_cases.append(relationship_test_case)
            
            logger.info(f"从数据库Schema生成了 {len(test_cases)} 个测试用例")
            return test_cases
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}")
            return []

    async def _send_to_test_point_extractor(self, response: DatabaseSchemaParseResponse):
        """发送到测试点提取智能体"""
        try:
            from app.core.messages.test_case import TestPointExtractionRequest

            # 构建需求解析结果
            requirement_analysis_result = {
                "source_type": "database_schema",
                "database_name": response.database_name,
                "database_type": response.database_type,
                "schema_analysis": response.parse_result,
                "requirements": [tc.model_dump() for tc in response.test_cases],
                "tables": response.parse_result.get("tables", []),
                "relationships": response.parse_result.get("relationships", []),
                "constraints": response.parse_result.get("constraints", []),
                "indexes": response.parse_result.get("indexes", []),
                "data_types": response.parse_result.get("data_types", [])
            }

            extraction_request = TestPointExtractionRequest(
                session_id=response.session_id,
                requirement_analysis_result=requirement_analysis_result,
                extraction_config={
                    "enable_functional_testing": True,
                    "enable_non_functional_testing": True,
                    "enable_integration_testing": True,
                    "enable_acceptance_testing": True,
                    "enable_boundary_testing": True,
                    "enable_exception_testing": True,
                    "test_depth": "comprehensive",
                    "focus_areas": ["data_integrity", "performance", "security", "backup_recovery"]
                },
                test_strategy="database_driven"
            )

            await self.publish_message(
                extraction_request,
                topic_id=TopicId(type=TopicTypes.TEST_POINT_EXTRACTOR.value, source=self.id.key)
            )

            logger.info(f"已发送到测试点提取智能体: {response.session_id}")

        except Exception as e:
            logger.error(f"发送到测试点提取智能体失败: {str(e)}")
