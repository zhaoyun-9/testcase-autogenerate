"""
枚举工具函数
提供枚举值验证和转换的通用功能
"""
from typing import Type, Union, List, Optional
from enum import Enum
from fastapi import HTTPException


def validate_enum_value(value: str, enum_class: Type[Enum], field_name: str = "值") -> Enum:
    """
    验证并转换枚举值，支持多种格式
    
    Args:
        value: 要验证的值
        enum_class: 枚举类
        field_name: 字段名称，用于错误信息
        
    Returns:
        验证后的枚举实例
        
    Raises:
        HTTPException: 当值无效时
    """
    if not value:
        raise HTTPException(
            status_code=400,
            detail=f"无效的{field_name}: 值不能为空"
        )
    
    # 尝试多种匹配方式
    try:
        # 1. 直接匹配枚举值
        return enum_class(value)
    except ValueError:
        pass
    
    try:
        # 2. 尝试大写匹配
        return enum_class(value.upper())
    except ValueError:
        pass
    
    try:
        # 3. 尝试小写匹配
        return enum_class(value.lower())
    except ValueError:
        pass
    
    # 4. 尝试通过枚举名匹配
    value_upper = value.upper()
    for enum_member in enum_class:
        if enum_member.name == value_upper:
            return enum_member
    
    # 5. 尝试通过枚举名小写匹配
    value_lower = value.lower()
    for enum_member in enum_class:
        if enum_member.name.lower() == value_lower:
            return enum_member
    
    # 所有方式都失败，抛出异常
    valid_values = [member.value for member in enum_class]
    valid_names = [member.name.lower() for member in enum_class]
    
    raise HTTPException(
        status_code=400,
        detail=f"无效的{field_name}: {value}. 可选值: {valid_values} 或 {valid_names}"
    )


def validate_enum_list(values: Optional[List[str]], enum_class: Type[Enum], field_name: str = "值") -> Optional[List[Enum]]:
    """
    验证枚举值列表
    
    Args:
        values: 要验证的值列表
        enum_class: 枚举类
        field_name: 字段名称，用于错误信息
        
    Returns:
        验证后的枚举实例列表，如果输入为None则返回None
    """
    if not values:
        return None
    
    validated_enums = []
    for value in values:
        validated_enum = validate_enum_value(value, enum_class, field_name)
        validated_enums.append(validated_enum)
    
    return validated_enums


def enum_to_dict(enum_class: Type[Enum]) -> dict:
    """
    将枚举类转换为字典，包含名称和值的映射
    
    Args:
        enum_class: 枚举类
        
    Returns:
        包含枚举信息的字典
    """
    return {
        "values": [member.value for member in enum_class],
        "names": [member.name for member in enum_class],
        "mapping": {member.name: member.value for member in enum_class}
    }


def get_enum_choices(enum_class: Type[Enum]) -> List[dict]:
    """
    获取枚举选择列表，适用于前端下拉框
    
    Args:
        enum_class: 枚举类
        
    Returns:
        包含label和value的字典列表
    """
    return [
        {
            "label": member.name.replace("_", " ").title(),
            "value": member.value,
            "name": member.name
        }
        for member in enum_class
    ]


def normalize_enum_value(value: Union[str, Enum], enum_class: Type[Enum]) -> str:
    """
    标准化枚举值，确保返回正确的枚举值字符串
    
    Args:
        value: 枚举值或字符串
        enum_class: 枚举类
        
    Returns:
        标准化后的枚举值字符串
    """
    if isinstance(value, enum_class):
        return value.value
    elif isinstance(value, str):
        validated_enum = validate_enum_value(value, enum_class)
        return validated_enum.value
    else:
        raise ValueError(f"无法处理的值类型: {type(value)}")
