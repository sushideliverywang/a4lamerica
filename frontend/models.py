"""
Frontend app 模型文件
导入所有代理模型，使Django能够识别它们
"""

# 导入所有代理模型
from .models_proxy import (
    # Accounts models
    User,
    Customer,
    Staff,
    Role,
    StaffRole,
    
    # Organization models
    Address,
    Company,
    Location,
    BusinessHours,
    LocationWarrantyPolicy,
    LocationTermsAndConditions,
    
    # Product models
    Brand,
    Category,
    ProductModel,
    ProductImage,
    Spec,
    ProductSpec,
    
    # Order models
    Order,
    OrderStatusHistory,
    TransactionRecord,
    
    # Inventory models
    ItemState,
    StateTransition,
    InventoryItem,
    InventoryStateHistory,
    LoadManifest,
    InventoryLocationHistory,
    TemporaryInventoryItem,
    ItemImage,
    
    # Customer models
    CustomerFavorite,
    CustomerAddress,
    ShoppingCart,
    CustomerWarrantyPolicy,
    CustomerTermsAgreement,
)

# 确保所有模型都被Django识别
__all__ = [
    # Accounts
    'User',
    'Customer', 
    'Staff',
    'Role',
    'StaffRole',
    
    # Organization
    'Address',
    'Company',
    'Location',
    'BusinessHours',
    'LocationWarrantyPolicy',
    'LocationTermsAndConditions',
    
    # Product
    'Brand',
    'Category',
    'ProductModel',
    'ProductImage',
    'Spec',
    'ProductSpec',
    
    # Order
    'Order',
    'OrderStatusHistory',
    'TransactionRecord',
    
    # Inventory
    'ItemState',
    'StateTransition',
    'InventoryItem',
    'InventoryStateHistory',
    'LoadManifest',
    'InventoryLocationHistory',
    'TemporaryInventoryItem',
    'ItemImage',
    
    # Customer
    'CustomerFavorite',
    'CustomerAddress',
    'ShoppingCart',
    'CustomerWarrantyPolicy',
    'CustomerTermsAgreement',
]