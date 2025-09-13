"""
Accounts app 模型文件已清空
所有账户相关模型已迁移到 frontend/models_proxy.py 中
这些模型作为代理模型连接到 nasmaha 数据库
"""

# 所有账户相关模型现在都在 frontend/models_proxy.py 中定义
# 包括：User, Customer, Staff, Role, StaffRole
from frontend.models_proxy import (
    # Accounts models
    User,
    Customer,
    Staff,
    Role,
    StaffRole,
)

__all__ = [
    'User',
    'Customer',
    'Staff',
    'Role',
    'StaffRole'
]