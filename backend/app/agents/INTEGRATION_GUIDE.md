# TestCaseAgentManager 集成指南

## 📋 概述

`TestCaseAgentManager` 已成功集成到 `TestCaseAgentOrchestrator` 中，提供了更好的智能体生命周期管理、性能监控和配置管理功能。

## ✅ 集成完成状态

### 已完成的集成
- **✅ 编排器合并** - `TestCaseAgentOrchestrator` 已集成 `TestCaseAgentManager` 功能
- **✅ 双模式支持** - 支持传统模式和智能体管理器模式
- **✅ 性能监控** - 提供详细的性能指标和健康检查
- **✅ 配置管理** - 支持动态配置更新
- **✅ 工作流管理** - 完善的工作流跟踪和错误处理

### 新增功能
- **统一管理** - 集中管理所有测试用例相关智能体
- **性能监控** - 提供详细的性能指标和健康检查
- **配置管理** - 支持动态配置更新
- **错误恢复** - 完善的错误处理和重试机制
- **工作流跟踪** - 详细的工作流状态管理

## 🚀 使用方法

### 启用智能体管理器模式
```python
# 创建编排器实例
orchestrator = get_test_case_orchestrator(collector=collector)

# 初始化（启用智能体管理器模式）
await orchestrator.initialize()

# 使用工作流方法
workflow_id = await orchestrator.parse_document(request)
```

### 传统模式（兼容性）
```python
# 不调用 initialize() 方法，使用传统模式
orchestrator = get_test_case_orchestrator(collector=collector)

# 直接使用工作流方法（传统模式）
await orchestrator.parse_document(request)
```

### 系统管理功能
```python
# 获取系统状态
status = await orchestrator.get_system_status()

# 更新智能体配置（仅在智能体管理器模式下可用）
await orchestrator.update_agent_config(agent_type, config_updates)

# 获取智能体列表
agent_list = await orchestrator.get_agent_list()

# 健康检查
health = status.get("health_status", {})
```

## 📝 具体实施步骤

### 1. 更新 test_case_generator.py API

```python
# 在 process_text_requirement 函数中
async def process_text_requirement(session_id: str):
    try:
        # 获取编排器
        collector = StreamResponseCollector(platform=AgentPlatform.TEST_CASE)
        collector.set_callback(message_callback)

        orchestrator = get_test_case_orchestrator(collector=collector)
        await orchestrator.initialize()  # 新增：初始化智能体管理器模式

        # 其余代码保持不变...

    except Exception as e:
        logger.error(f"处理文本需求失败: {str(e)}")
    finally:
        # 新增：清理资源
        if 'orchestrator' in locals():
            await orchestrator.stop()
```

### 2. 添加系统监控端点

```python
# 在 app/api/v1/endpoints/test_case_generator.py 中添加

@router.get("/system/status")
async def get_system_status():
    """获取系统状态和性能指标"""
    try:
        orchestrator = get_test_case_orchestrator()
        await orchestrator.initialize()

        status = await orchestrator.get_system_status()
        await orchestrator.stop()

        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/health")
async def health_check():
    """健康检查端点"""
    try:
        orchestrator = get_test_case_orchestrator()
        await orchestrator.initialize()

        status = await orchestrator.get_system_status()
        health = status.get("health_status", {})
        await orchestrator.stop()

        return {
            "status": "success",
            "health": health
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/agents/{agent_type}/config")
async def update_agent_config(
    agent_type: str,
    config_updates: Dict[str, Any]
):
    """更新智能体配置"""
    try:
        orchestrator = get_test_case_orchestrator()
        await orchestrator.initialize()

        await orchestrator.update_agent_config(agent_type, config_updates)
        await orchestrator.stop()

        return {
            "status": "success",
            "message": f"智能体 {agent_type} 配置已更新"
        }
    except Exception as e:
        logger.error(f"更新智能体配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 更新前端集成

```typescript
// 在 frontend-mine-old/src/api/testCase.ts 中添加

// 系统监控相关API
export const systemMonitoringApi = {
  // 获取系统状态
  getSystemStatus(): Promise<{
    timestamp: string
    system_status: string
    agent_metrics: any
    health_status: any
    orchestrator_metrics: any
    active_sessions: string[]
  }> {
    return request.get('/test-case/system/status')
  },

  // 健康检查
  healthCheck(): Promise<{
    status: string
    health: any
  }> {
    return request.get('/test-case/system/health')
  },

  // 更新智能体配置
  updateAgentConfig(agentType: string, config: any): Promise<{
    status: string
    message: string
  }> {
    return request.post(`/test-case/system/agents/${agentType}/config`, config)
  },

  // 获取智能体列表
  getAgentList(): Promise<any[]> {
    return request.get('/test-case/system/agents')
  }
}
```

## 🧪 测试验证

### 1. 功能测试
```python
# 创建测试文件 tests/test_agent_manager_integration.py
import pytest
from app.services.test_case.enhanced_orchestrator_service import get_enhanced_test_case_orchestrator

@pytest.mark.asyncio
async def test_enhanced_orchestrator_initialization():
    """测试增强版编排器初始化"""
    orchestrator = get_enhanced_test_case_orchestrator()
    await orchestrator.initialize()
    
    # 验证智能体管理器已初始化
    assert orchestrator.agent_manager is not None
    
    # 验证智能体已注册
    agent_list = await orchestrator.get_agent_list()
    assert len(agent_list) > 0
    
    await orchestrator.stop()

@pytest.mark.asyncio
async def test_system_status():
    """测试系统状态获取"""
    orchestrator = get_enhanced_test_case_orchestrator()
    await orchestrator.initialize()
    
    status = await orchestrator.get_system_status()
    assert "agent_metrics" in status
    assert "health_status" in status
    
    await orchestrator.stop()
```

### 2. 性能测试
```python
@pytest.mark.asyncio
async def test_performance_monitoring():
    """测试性能监控功能"""
    orchestrator = get_enhanced_test_case_orchestrator()
    await orchestrator.initialize()
    
    # 获取初始指标
    initial_metrics = await orchestrator.agent_manager.get_performance_metrics()
    
    # 执行一些操作...
    
    # 获取更新后的指标
    updated_metrics = await orchestrator.agent_manager.get_performance_metrics()
    
    # 验证指标已更新
    assert updated_metrics["timestamp"] != initial_metrics["timestamp"]
    
    await orchestrator.stop()
```

## 📊 迁移检查清单

### 准备阶段
- [ ] 备份现有代码
- [ ] 创建测试环境
- [ ] 准备回滚方案

### 实施阶段
- [ ] 部署增强版编排器
- [ ] 更新API端点
- [ ] 添加监控端点
- [ ] 更新前端集成

### 验证阶段
- [ ] 功能测试通过
- [ ] 性能测试通过
- [ ] 监控功能正常
- [ ] 配置管理正常

### 上线阶段
- [ ] 生产环境部署
- [ ] 监控系统运行
- [ ] 收集用户反馈
- [ ] 性能优化

## 🔧 配置示例

### 智能体配置更新示例
```python
# 更新测试用例生成智能体配置
config_updates = {
    "ai_enhancement_enabled": True,
    "model_type": "deepseek",
    "max_retries": 5,
    "batch_size": 50
}

await orchestrator.update_agent_config(
    AgentTypes.TEST_CASE_GENERATOR.value,
    config_updates
)
```

### 监控告警配置
```python
# 在系统监控中添加告警逻辑
async def check_system_health():
    status = await orchestrator.get_system_status()
    
    if status["system_status"] != "healthy":
        # 发送告警
        await send_alert(f"系统状态异常: {status['system_status']}")
    
    # 检查性能指标
    for agent_type, metrics in status["agent_metrics"]["agents"].items():
        if metrics.get("success_rate", 100) < 80:
            await send_alert(f"智能体 {agent_type} 成功率过低: {metrics['success_rate']}%")
```

## 🎯 预期收益

### 1. 管理效率提升
- 统一的智能体管理界面
- 实时性能监控
- 动态配置调整

### 2. 系统稳定性改善
- 完善的健康检查
- 自动错误恢复
- 详细的错误日志

### 3. 运维便利性增强
- 可视化监控面板
- 自动化告警机制
- 便捷的配置管理

---

通过以上集成方案，可以将 `TestCaseAgentManager` 的优势充分发挥，同时保持系统的向后兼容性和稳定性。
