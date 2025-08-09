"""
智能体选择服务
负责根据文件类型和内容智能选择合适的智能体
"""
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import mimetypes
from loguru import logger

from app.core.types import AgentTypes, FILE_TYPE_TO_AGENT_MAPPING


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    content_type: str
    confidence: float
    features: Dict[str, Any]
    reasoning: str
    metadata: Dict[str, Any]


@dataclass
class AgentRecommendation:
    """智能体推荐结果"""
    primary_agent: str
    alternative_agents: List[str]
    confidence: float
    reasoning: str
    analysis: ContentAnalysis


class ContentAnalyzer:
    """内容分析器基类"""
    
    def __init__(self):
        self.api_spec_keywords = [
            'openapi', 'swagger', 'paths', 'info', 'components', 'servers',
            'definitions', 'parameters', 'responses', 'schemes', 'host'
        ]
        self.database_keywords = [
            'tables', 'schema', 'database', 'columns', 'indexes', 'constraints',
            'foreign_keys', 'primary_key', 'table_name', 'column_name'
        ]
        self.sql_keywords = [
            'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE', 'INSERT INTO',
            'SELECT', 'UPDATE', 'DELETE', 'PRIMARY KEY', 'FOREIGN KEY'
        ]
        self.requirement_keywords = [
            '需求', '功能', '用例', '测试', '验证', '场景', '流程',
            'requirement', 'feature', 'scenario', 'test case'
        ]
    
    async def analyze_json(self, content: bytes) -> ContentAnalysis:
        """分析JSON内容"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            # API规范检测
            api_score = self._calculate_api_score(data)
            
            # 数据库Schema检测
            db_score = self._calculate_db_score(data)
            
            # 确定最佳匹配
            scores = {'api_spec': api_score, 'database_schema': db_score}
            best_match = max(scores, key=scores.get)
            confidence = scores[best_match]
            
            features = {
                'structure_depth': self._get_depth(data),
                'key_count': len(data) if isinstance(data, dict) else 0,
                'scores': scores
            }
            
            reasoning = f"JSON分析: {best_match}，置信度: {confidence:.2f}"
            
            return ContentAnalysis(
                content_type=best_match,
                confidence=confidence,
                features=features,
                reasoning=reasoning,
                metadata={'file_size': len(content)}
            )
            
        except json.JSONDecodeError:
            return ContentAnalysis(
                content_type='unknown',
                confidence=0.0,
                features={},
                reasoning="无效的JSON格式",
                metadata={}
            )
    
    async def analyze_text(self, content: bytes) -> ContentAnalysis:
        """分析文本内容"""
        try:
            text = content.decode('utf-8', errors='ignore')
            
            # SQL脚本检测
            sql_score = self._calculate_sql_score(text)
            
            # 需求文档检测
            req_score = self._calculate_requirement_score(text)
            
            scores = {'sql_script': sql_score, 'requirement_document': req_score}
            best_match = max(scores, key=scores.get)
            confidence = scores[best_match]
            
            features = {
                'line_count': len(text.split('\n')),
                'word_count': len(text.split()),
                'scores': scores
            }
            
            reasoning = f"文本分析: {best_match}，置信度: {confidence:.2f}"
            
            return ContentAnalysis(
                content_type=best_match,
                confidence=confidence,
                features=features,
                reasoning=reasoning,
                metadata={'encoding': 'utf-8'}
            )
            
        except Exception as e:
            logger.error(f"文本分析失败: {e}")
            return ContentAnalysis(
                content_type='unknown',
                confidence=0.0,
                features={},
                reasoning=f"分析失败: {str(e)}",
                metadata={}
            )
    
    def _calculate_api_score(self, data: Any) -> float:
        """计算API规范匹配分数"""
        if not isinstance(data, dict):
            return 0.0
        
        score = 0.0
        for keyword in self.api_spec_keywords:
            if keyword in data:
                score += 1.0
        
        # 特殊检查
        if 'paths' in data and isinstance(data['paths'], dict):
            score += 2.0
        if 'info' in data and isinstance(data['info'], dict):
            if 'title' in data['info'] and 'version' in data['info']:
                score += 1.0
        
        return min(score / (len(self.api_spec_keywords) + 3), 1.0)
    
    def _calculate_db_score(self, data: Any) -> float:
        """计算数据库Schema匹配分数"""
        if not isinstance(data, dict):
            return 0.0
        
        score = 0.0
        for keyword in self.database_keywords:
            if keyword in data:
                score += 1.0
        
        if 'tables' in data and isinstance(data['tables'], (list, dict)):
            score += 2.0
        
        return min(score / (len(self.database_keywords) + 2), 1.0)
    
    def _calculate_sql_score(self, text: str) -> float:
        """计算SQL脚本匹配分数"""
        text_upper = text.upper()
        score = 0.0
        
        for keyword in self.sql_keywords:
            if keyword in text_upper:
                score += 1.0
        
        return min(score / len(self.sql_keywords), 1.0)
    
    def _calculate_requirement_score(self, text: str) -> float:
        """计算需求文档匹配分数"""
        text_lower = text.lower()
        score = 0.0
        
        for keyword in self.requirement_keywords:
            if keyword in text_lower:
                score += 1.0
        
        return min(score / len(self.requirement_keywords), 1.0)
    
    def _get_depth(self, data: Any, current_depth: int = 0) -> int:
        """计算数据结构深度"""
        if current_depth > 10:
            return current_depth
        
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(self._get_depth(v, current_depth + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(self._get_depth(item, current_depth + 1) for item in data)
        else:
            return current_depth


class AgentSelector:
    """智能体选择器"""
    
    def __init__(self):
        self.analyzer = ContentAnalyzer()
        
        # 内容类型到智能体的映射
        self.content_agent_mapping = {
            'api_spec': AgentTypes.API_SPEC_PARSER.value,
            'database_schema': AgentTypes.DATABASE_SCHEMA_PARSER.value,
            'sql_script': AgentTypes.DATABASE_SCHEMA_PARSER.value,
            'requirement_document': AgentTypes.DOCUMENT_PARSER.value,
            'test_case': AgentTypes.TEST_CASE_GENERATOR.value
        }
    
    async def select_agent(self, file_path: str, file_content: bytes, 
                          file_extension: str) -> AgentRecommendation:
        """选择最适合的智能体"""
        try:
            # 基础文件类型判断
            base_agent = FILE_TYPE_TO_AGENT_MAPPING.get(file_extension.lower())
            
            # 内容深度分析
            analysis = await self._analyze_content(file_content, file_extension)
            
            # 智能体推荐
            primary_agent = self._get_primary_agent(base_agent, analysis)
            alternative_agents = self._get_alternative_agents(analysis)
            
            # 置信度计算
            confidence = self._calculate_confidence(analysis)
            
            # 推理说明
            reasoning = self._generate_reasoning(base_agent, analysis)
            
            return AgentRecommendation(
                primary_agent=primary_agent,
                alternative_agents=alternative_agents,
                confidence=confidence,
                reasoning=reasoning,
                analysis=analysis
            )
            
        except Exception as e:
            logger.error(f"智能体选择失败: {e}")
            return AgentRecommendation(
                primary_agent=base_agent or AgentTypes.DOCUMENT_PARSER.value,
                alternative_agents=[],
                confidence=0.5,
                reasoning=f"使用默认选择: {str(e)}",
                analysis=ContentAnalysis(
                    content_type='unknown',
                    confidence=0.0,
                    features={},
                    reasoning=str(e),
                    metadata={}
                )
            )
    
    async def _analyze_content(self, content: bytes, file_extension: str) -> ContentAnalysis:
        """分析文件内容"""
        if file_extension.lower() == '.json':
            return await self.analyzer.analyze_json(content)
        elif file_extension.lower() in ['.txt', '.md', '.sql']:
            return await self.analyzer.analyze_text(content)
        else:
            return ContentAnalysis(
                content_type='file_extension_based',
                confidence=0.8,
                features={'file_extension': file_extension},
                reasoning=f"基于文件扩展名 {file_extension}",
                metadata={'file_size': len(content)}
            )
    
    def _get_primary_agent(self, base_agent: Optional[str], 
                          analysis: ContentAnalysis) -> str:
        """获取主要推荐智能体"""
        if analysis.confidence > 0.7:
            content_agent = self.content_agent_mapping.get(analysis.content_type)
            if content_agent:
                return content_agent
        
        return base_agent or AgentTypes.DOCUMENT_PARSER.value
    
    def _get_alternative_agents(self, analysis: ContentAnalysis) -> List[str]:
        """获取备选智能体"""
        alternatives = []
        
        if hasattr(analysis.features, 'scores'):
            scores = analysis.features.get('scores', {})
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            for content_type, score in sorted_scores:
                if score > 0.3:
                    agent = self.content_agent_mapping.get(content_type)
                    if agent and agent not in alternatives:
                        alternatives.append(agent)
        
        return alternatives[:3]
    
    def _calculate_confidence(self, analysis: ContentAnalysis) -> float:
        """计算最终置信度"""
        base_confidence = analysis.confidence
        
        if analysis.features:
            feature_count = len(analysis.features)
            if feature_count > 3:
                base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _generate_reasoning(self, base_agent: Optional[str], 
                           analysis: ContentAnalysis) -> str:
        """生成推理说明"""
        reasoning = analysis.reasoning
        
        if base_agent:
            reasoning += f"。基础推荐: {base_agent}"
        
        if analysis.confidence > 0.8:
            reasoning += "。高置信度推荐"
        elif analysis.confidence > 0.6:
            reasoning += "。中等置信度推荐"
        else:
            reasoning += "。低置信度推荐，建议人工确认"
        
        return reasoning


# 全局实例
agent_selector = AgentSelector()
