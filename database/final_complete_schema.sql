-- =====================================================
-- 企业级测试用例生成平台 - 最终完整版数据库结构
-- 版本: Final Complete
-- 设计原则: 简洁、高效、功能完整
-- 包含: 核心表 + 需求管理 + 智能体日志 + 视图
-- =====================================================

-- 删除并重建数据库
DROP DATABASE IF EXISTS test_case_automation;
CREATE DATABASE test_case_automation 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE test_case_automation;

-- =====================================================
-- 1. 项目表
-- =====================================================
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY COMMENT '项目ID',
    name VARCHAR(255) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    status ENUM('active', 'archived') DEFAULT 'active' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- =====================================================
-- 2. 测试用例分类表
-- =====================================================
CREATE TABLE categories (
    id VARCHAR(36) PRIMARY KEY COMMENT '分类ID',
    name VARCHAR(255) NOT NULL COMMENT '分类名称',
    description TEXT COMMENT '分类描述',
    parent_id VARCHAR(36) COMMENT '父分类ID',
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_name (name),
    INDEX idx_parent_id (parent_id),
    INDEX idx_project_id (project_id),
    INDEX idx_sort_order (sort_order),
    
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例分类表';

-- =====================================================
-- 3. 需求表
-- =====================================================
CREATE TABLE requirements (
    id VARCHAR(36) PRIMARY KEY COMMENT '需求ID',
    requirement_id VARCHAR(100) NOT NULL COMMENT '需求编号',
    title VARCHAR(500) NOT NULL COMMENT '需求标题',
    description TEXT COMMENT '需求描述',
    
    -- 分类信息
    requirement_type ENUM(
        'functional', 'non_functional', 'business', 'technical', 
        'interface', 'performance', 'security', 'usability'
    ) NOT NULL COMMENT '需求类型',
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium' COMMENT '优先级',
    status ENUM('draft', 'approved', 'rejected', 'deprecated') DEFAULT 'draft' COMMENT '状态',
    
    -- 关联信息
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    document_id VARCHAR(36) COMMENT '源文档ID',
    session_id VARCHAR(36) COMMENT '会话ID',
    
    -- 源信息
    source_file_path VARCHAR(500) COMMENT '源文件路径',
    source_section VARCHAR(200) COMMENT '源文档章节',
    
    -- AI相关信息
    ai_generated BOOLEAN DEFAULT TRUE COMMENT '是否AI生成',
    ai_confidence FLOAT COMMENT 'AI置信度',
    ai_model_info JSON COMMENT 'AI模型信息',
    
    -- 元数据
    extra_metadata JSON COMMENT '扩展元数据',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_requirement_id (requirement_id),
    INDEX idx_title (title(100)),
    INDEX idx_requirement_type (requirement_type),
    INDEX idx_priority (priority),
    INDEX idx_status (status),
    INDEX idx_project_id (project_id),
    INDEX idx_document_id (document_id),
    INDEX idx_session_id (session_id),
    INDEX idx_ai_generated (ai_generated),
    INDEX idx_created_at (created_at),
    INDEX idx_composite (project_id, status, requirement_type, priority),
    
    -- 外键约束
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求表';

-- =====================================================
-- 4. 测试用例主表
-- =====================================================
CREATE TABLE test_cases (
    id VARCHAR(36) PRIMARY KEY COMMENT '测试用例ID',
    title VARCHAR(500) NOT NULL COMMENT '标题',
    description TEXT COMMENT '描述',
    preconditions TEXT COMMENT '前置条件',
    test_steps JSON COMMENT '测试步骤',
    expected_results TEXT COMMENT '预期结果',
    
    -- 分类信息
    test_type ENUM('functional', 'performance', 'security', 'compatibility', 'usability', 'interface', 'database') NOT NULL COMMENT '测试类型',
    test_level ENUM('unit', 'integration', 'system', 'acceptance') NOT NULL COMMENT '测试级别',
    priority ENUM('P0', 'P1', 'P2', 'P3', 'P4') DEFAULT 'P2' COMMENT '优先级',
    status ENUM('draft', 'approved', 'deprecated') DEFAULT 'draft' COMMENT '状态',
    
    -- 关联信息
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    category_id VARCHAR(36) COMMENT '分类ID',
    session_id VARCHAR(36) COMMENT '生成会话ID',
    
    -- 输入源信息
    input_source ENUM('image', 'document', 'api_spec', 'database_schema', 'video', 'manual') COMMENT '输入源',
    source_file_path VARCHAR(500) COMMENT '源文件路径',
    
    -- AI生成信息
    ai_generated BOOLEAN DEFAULT FALSE COMMENT '是否AI生成',
    ai_confidence FLOAT COMMENT 'AI置信度',
    ai_model_info JSON COMMENT 'AI模型信息',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_title (title(100)),
    INDEX idx_test_type (test_type),
    INDEX idx_test_level (test_level),
    INDEX idx_priority (priority),
    INDEX idx_status (status),
    INDEX idx_project_id (project_id),
    INDEX idx_category_id (category_id),
    INDEX idx_session_id (session_id),
    INDEX idx_input_source (input_source),
    INDEX idx_ai_generated (ai_generated),
    INDEX idx_created_at (created_at),
    INDEX idx_composite (project_id, status, test_type, priority),
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例主表';

-- =====================================================
-- 5. 测试用例需求关联表
-- =====================================================
CREATE TABLE test_case_requirements (
    id VARCHAR(36) PRIMARY KEY COMMENT 'ID',
    test_case_id VARCHAR(36) NOT NULL COMMENT '测试用例ID',
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    
    -- 覆盖信息
    coverage_type VARCHAR(50) DEFAULT 'full' COMMENT '覆盖类型: full/partial',
    coverage_description TEXT COMMENT '覆盖描述',
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 唯一约束
    UNIQUE KEY uk_test_case_requirement (test_case_id, requirement_id),
    
    -- 索引
    INDEX idx_test_case_id (test_case_id),
    INDEX idx_requirement_id (requirement_id),
    INDEX idx_coverage_type (coverage_type),
    INDEX idx_created_at (created_at),
    
    -- 外键约束
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例需求关联表';

-- =====================================================
-- 6. 标签表
-- =====================================================
CREATE TABLE tags (
    id VARCHAR(36) PRIMARY KEY COMMENT '标签ID',
    name VARCHAR(100) NOT NULL COMMENT '标签名称',
    color VARCHAR(20) DEFAULT '#1890ff' COMMENT '标签颜色',
    project_id VARCHAR(36) COMMENT '项目ID',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_project_tag (project_id, name),
    INDEX idx_name (name),
    INDEX idx_project_id (project_id),
    INDEX idx_usage_count (usage_count),
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- =====================================================
-- 7. 测试用例标签关联表
-- =====================================================
CREATE TABLE test_case_tags (
    id VARCHAR(36) PRIMARY KEY COMMENT 'ID',
    test_case_id VARCHAR(36) NOT NULL COMMENT '测试用例ID',
    tag_id VARCHAR(36) NOT NULL COMMENT '标签ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_case_tag (test_case_id, tag_id),
    INDEX idx_test_case_id (test_case_id),
    INDEX idx_tag_id (tag_id),
    
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例标签关联表';

-- =====================================================
-- 8. 文件上传表
-- =====================================================
CREATE TABLE file_uploads (
    id VARCHAR(36) PRIMARY KEY COMMENT '文件ID',
    original_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    stored_name VARCHAR(255) NOT NULL COMMENT '存储文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size BIGINT NOT NULL COMMENT '文件大小',
    file_type VARCHAR(100) NOT NULL COMMENT '文件类型',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    upload_source ENUM('document', 'image', 'api_spec', 'database_schema', 'video') NOT NULL COMMENT '上传源',
    session_id VARCHAR(36) COMMENT '会话ID',
    project_id VARCHAR(36) COMMENT '项目ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_original_name (original_name),
    INDEX idx_file_type (file_type),
    INDEX idx_upload_source (upload_source),
    INDEX idx_session_id (session_id),
    INDEX idx_project_id (project_id),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件上传表';

-- =====================================================
-- 9. 处理会话表
-- =====================================================
CREATE TABLE processing_sessions (
    id VARCHAR(36) PRIMARY KEY COMMENT '会话ID',
    session_type ENUM('document_parse', 'image_analysis', 'api_spec_parse', 'database_schema_parse', 'video_analysis', 'manual_input') NOT NULL COMMENT '会话类型',
    status ENUM('created', 'processing', 'completed', 'failed') DEFAULT 'created' COMMENT '状态',
    progress DECIMAL(5,2) DEFAULT 0.00 COMMENT '进度',
    project_id VARCHAR(36) COMMENT '项目ID',
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    config_data JSON COMMENT '配置数据',
    agent_type VARCHAR(50) COMMENT '智能体类型',
    processing_time FLOAT COMMENT '处理时间(秒)',
    error_message TEXT COMMENT '错误信息',
    generated_count INT DEFAULT 0 COMMENT '生成数量',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 智能体日志相关字段
    agent_logs_summary JSON COMMENT '智能体日志摘要',
    key_metrics JSON COMMENT '关键指标数据',
    processing_stages JSON COMMENT '处理阶段信息',

    INDEX idx_session_type (session_type),
    INDEX idx_status (status),
    INDEX idx_project_id (project_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处理会话表';

-- =====================================================
-- 10. 智能体消息日志表
-- =====================================================
CREATE TABLE agent_message_logs (
    id VARCHAR(36) PRIMARY KEY COMMENT '日志ID',
    session_id VARCHAR(36) NOT NULL COMMENT '会话ID',
    message_id VARCHAR(100) NOT NULL COMMENT '消息ID',
    agent_type VARCHAR(50) NOT NULL COMMENT '智能体类型',
    agent_name VARCHAR(100) NOT NULL COMMENT '智能体名称',
    message_type ENUM('progress', 'info', 'success', 'warning', 'error', 'metrics', 'completion') NOT NULL COMMENT '消息类型',
    content TEXT NOT NULL COMMENT '消息内容',
    region VARCHAR(50) DEFAULT 'process' COMMENT '消息区域',
    source VARCHAR(100) COMMENT '消息来源',
    is_final BOOLEAN DEFAULT FALSE COMMENT '是否为最终消息',
    result_data JSON COMMENT '结果数据',
    error_info JSON COMMENT '错误信息',
    metrics_data JSON COMMENT '指标数据',
    processing_stage VARCHAR(100) COMMENT '处理阶段',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_session_id (session_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_message_type (message_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_processing_stage (processing_stage),
    INDEX idx_session_agent (session_id, agent_type),

    FOREIGN KEY (session_id) REFERENCES processing_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能体消息日志表';

-- =====================================================
-- 11. 思维导图表
-- =====================================================
CREATE TABLE mind_maps (
    id VARCHAR(36) PRIMARY KEY COMMENT '思维导图ID',
    name VARCHAR(255) NOT NULL COMMENT '名称',
    session_id VARCHAR(36) NOT NULL COMMENT '会话ID',
    project_id VARCHAR(36) COMMENT '项目ID',
    mind_map_data JSON NOT NULL COMMENT '思维导图数据',
    layout_config JSON COMMENT '布局配置',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_name (name),
    INDEX idx_session_id (session_id),
    INDEX idx_project_id (project_id),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='思维导图表';

-- =====================================================
-- 12. 导出记录表
-- =====================================================
CREATE TABLE export_records (
    id VARCHAR(36) PRIMARY KEY COMMENT '导出ID',
    export_type ENUM('excel', 'word', 'pdf') NOT NULL COMMENT '导出类型',
    test_case_ids JSON COMMENT '测试用例ID列表',
    session_id VARCHAR(36) COMMENT '会话ID',
    project_id VARCHAR(36) COMMENT '项目ID',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size BIGINT COMMENT '文件大小',
    export_config JSON COMMENT '导出配置',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_export_type (export_type),
    INDEX idx_session_id (session_id),
    INDEX idx_project_id (project_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='导出记录表';

-- =====================================================
-- 13. 系统配置表
-- =====================================================
CREATE TABLE system_configs (
    id VARCHAR(36) PRIMARY KEY COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string' COMMENT '配置类型',
    description TEXT COMMENT '配置描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- =====================================================
-- 14. 插入默认数据
-- =====================================================

-- 插入默认项目
INSERT INTO projects (id, name, description) VALUES
('default-project-001', '默认项目', '系统默认测试用例项目');

-- 插入默认分类
INSERT INTO categories (id, name, description, parent_id, project_id) VALUES
('cat-functional-001', '功能测试', '功能测试用例分类', NULL, 'default-project-001'),
('cat-performance-001', '性能测试', '性能测试用例分类', NULL, 'default-project-001'),
('cat-security-001', '安全测试', '安全测试用例分类', NULL, 'default-project-001'),
('cat-compatibility-001', '兼容性测试', '兼容性测试用例分类', NULL, 'default-project-001'),
('cat-usability-001', '可用性测试', '可用性测试用例分类', NULL, 'default-project-001'),
('cat-interface-001', '接口测试', '接口测试用例分类', NULL, 'default-project-001'),
('cat-database-001', '数据库测试', '数据库测试用例分类', NULL, 'default-project-001');

-- 插入系统配置
INSERT INTO system_configs (id, config_key, config_value, config_type, description) VALUES
('cfg-001', 'max_file_size', '100', 'number', '最大文件上传大小(MB)'),
('cfg-002', 'supported_image_formats', '["jpg", "jpeg", "png", "gif", "bmp", "webp"]', 'json', '支持的图片格式'),
('cfg-003', 'supported_document_formats', '["pdf", "docx", "doc", "txt", "md"]', 'json', '支持的文档格式'),
('cfg-004', 'supported_api_formats', '["json", "yaml", "yml"]', 'json', '支持的API规范格式'),
('cfg-005', 'supported_video_formats', '["mp4", "avi", "mov", "wmv", "flv", "webm"]', 'json', '支持的视频格式'),
('cfg-006', 'ai_model_deepseek', '{"model": "deepseek-chat", "api_key": "", "base_url": ""}', 'json', 'DeepSeek模型配置'),
('cfg-007', 'ai_model_qwenvl', '{"model": "qwen-vl", "api_key": "", "base_url": ""}', 'json', 'QwenVL模型配置'),
('cfg-008', 'session_timeout', '3600', 'number', '会话超时时间(秒)'),
('cfg-009', 'enable_mindmap', 'true', 'boolean', '是否启用思维导图功能'),
('cfg-010', 'max_test_cases_per_session', '100', 'number', '单次会话最大生成测试用例数');

-- =====================================================
-- 15. 创建视图
-- =====================================================

-- 测试用例统计视图
CREATE VIEW v_test_case_stats AS
SELECT
    tc.project_id,
    p.name as project_name,
    tc.test_type,
    tc.test_level,
    tc.priority,
    tc.status,
    tc.input_source,
    COUNT(*) as total_count,
    COUNT(CASE WHEN tc.ai_generated = TRUE THEN 1 END) as ai_generated_count,
    AVG(tc.ai_confidence) as avg_confidence
FROM test_cases tc
LEFT JOIN projects p ON tc.project_id = p.id
GROUP BY tc.project_id, p.name, tc.test_type, tc.test_level, tc.priority, tc.status, tc.input_source;

-- 项目概览视图
CREATE VIEW v_project_overview AS
SELECT
    p.id,
    p.name,
    p.status,
    COUNT(DISTINCT tc.id) as total_test_cases,
    COUNT(DISTINCT CASE WHEN tc.status = 'approved' THEN tc.id END) as approved_cases,
    COUNT(DISTINCT c.id) as category_count,
    COUNT(DISTINCT t.id) as tag_count,
    COUNT(DISTINCT r.id) as requirement_count,
    MAX(tc.updated_at) as last_activity,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN test_cases tc ON p.id = tc.project_id
LEFT JOIN categories c ON p.id = c.project_id
LEFT JOIN tags t ON p.id = t.project_id
LEFT JOIN requirements r ON p.id = r.project_id
GROUP BY p.id, p.name, p.status, p.created_at, p.updated_at;

-- 会话统计视图
CREATE VIEW v_session_stats AS
SELECT
    ps.project_id,
    p.name as project_name,
    ps.session_type,
    ps.agent_type,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN ps.status = 'completed' THEN 1 END) as completed_sessions,
    COUNT(CASE WHEN ps.status = 'failed' THEN 1 END) as failed_sessions,
    AVG(ps.processing_time) as avg_processing_time,
    SUM(ps.generated_count) as total_generated_cases
FROM processing_sessions ps
LEFT JOIN projects p ON ps.project_id = p.id
GROUP BY ps.project_id, p.name, ps.session_type, ps.agent_type;

-- 需求覆盖统计视图
CREATE VIEW v_requirement_coverage_stats AS
SELECT
    p.id as project_id,
    p.name as project_name,
    COUNT(DISTINCT r.id) as total_requirements,
    COUNT(DISTINCT tcr.requirement_id) as covered_requirements,
    COUNT(DISTINCT tcr.test_case_id) as covering_test_cases,
    ROUND(
        COUNT(DISTINCT tcr.requirement_id) * 100.0 / NULLIF(COUNT(DISTINCT r.id), 0), 2
    ) as coverage_percentage,
    r.requirement_type,
    r.priority as requirement_priority
FROM projects p
LEFT JOIN requirements r ON p.id = r.project_id
LEFT JOIN test_case_requirements tcr ON r.id = tcr.requirement_id
GROUP BY p.id, p.name, r.requirement_type, r.priority;

-- 智能体会话摘要视图
CREATE VIEW v_session_agent_summary AS
SELECT
    s.id as session_id,
    s.session_type,
    s.status,
    s.progress,
    s.agent_type as primary_agent_type,
    COUNT(DISTINCT l.agent_type) as agents_count,
    COUNT(l.id) as total_messages,
    SUM(CASE WHEN l.message_type = 'error' THEN 1 ELSE 0 END) as error_count,
    SUM(CASE WHEN l.message_type = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN l.message_type = 'completion' THEN 1 ELSE 0 END) as completion_count,
    MIN(l.timestamp) as first_message_time,
    MAX(l.timestamp) as last_message_time,
    s.created_at,
    s.completed_at
FROM processing_sessions s
LEFT JOIN agent_message_logs l ON s.id = l.session_id
GROUP BY s.id, s.session_type, s.status, s.progress, s.agent_type, s.created_at, s.completed_at;

COMMIT;
