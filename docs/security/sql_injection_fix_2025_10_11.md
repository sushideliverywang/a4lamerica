# SQL注入攻击防护修复 (a4lamerica)

**日期**: 2025-10-11
**严重性**: 高
**状态**: ✅ 已修复

## 背景

本修复与nasmaha项目同步，两个项目使用相同的哈希算法和密钥访问同一数据库。

## 问题描述

与nasmaha相同，a4lamerica也遭受SQL注入扫描攻击。攻击者通过商品URL哈希参数尝试注入恶意代码。

### 攻击示例
```
/item/07-1; waitfor delay '0:0:15' --...
/item/-1 OR 2+979-979-1=0+0+0+1...
```

## 修复内容

### 1. 添加输入验证 (`frontend/utils.py`)

```python
def is_valid_hash(encoded_id):
    """验证哈希字符串是否有效（只包含十六进制字符）"""
    if not encoded_id or not isinstance(encoded_id, str):
        return False

    # SHA256生成的哈希长度应该是64位十六进制字符
    if len(encoded_id) != 64:
        return False

    # 只允许十六进制字符（0-9, a-f, A-F）
    return bool(re.match(r'^[0-9a-fA-F]{64}$', encoded_id))
```

### 2. 添加缓存键清理

```python
def sanitize_hash_for_cache_key(encoded_id):
    """清理哈希字符串用于缓存键"""
    return ''.join(c.lower() for c in encoded_id if c in '0123456789abcdefABCDEF')[:64]
```

### 3. 更新decode_item_id函数

```python
def decode_item_id(item_hash):
    """解码商品哈希"""
    # 安全检查：验证输入格式
    if not is_valid_hash(item_hash):
        logger.warning(f"Invalid hash format detected: {item_hash[:100]}")
        return None
    # ...继续处理
```

## 安全测试结果

```
✅ 有效哈希: True
✅ SQL注入攻击: False (已拦截)
✅ 特殊字符: False (已拦截)
✅ 实际解码: 正常工作
```

## 与nasmaha的同步

- ✅ 使用相同的安全检查逻辑
- ✅ 使用相同的密钥 (ITEM_HASH_SECRET_KEY)
- ✅ 生成相同的哈希值
- ✅ 两个域名访问同一商品

## 部署步骤

### 1. 备份代码
```bash
cd /var/www/a4lamerica
git branch backup-security-fix-$(date +%Y%m%d)
```

### 2. 部署更新
```bash
git pull origin main
```

### 3. 重启服务
```bash
sudo systemctl restart a4lamerica
```

### 4. 验证功能
```bash
# 测试正常访问
curl -I https://a4lamerica.com/item/[有效哈希]/

# 检查日志
tail -f /var/log/a4lamerica/app.log
```

## 监控

使用与nasmaha相同的监控脚本，或创建a4lamerica专用版本。

## 注意事项

1. **密钥一致性**: 确保a4lamerica和nasmaha使用完全相同的`ITEM_HASH_SECRET_KEY`
2. **URL兼容**: 两个域名生成的哈希必须完全一致
3. **日志审计**: 定期检查攻击日志

## 验证两个项目的哈希一致性

```python
# 在nasmaha中
from frontend.utils import encode_item_id
nasmaha_hash = encode_item_id(1368)

# 在a4lamerica中
from frontend.utils import get_item_hash
from frontend.models_proxy import InventoryItem
item = InventoryItem.objects.get(id=1368)
a4l_hash = get_item_hash(item)

# 应该完全相同
assert nasmaha_hash == a4l_hash
```

## 影响范围

- **受影响的URL**: 所有 `/item/{hash}/` 路径
- **向后兼容**: ✅ 完全兼容
- **用户体验**: 无影响

---

**维护人员**: Claude
**关联文档**: nasmaha/docs/security/sql_injection_fix_2025_10_11.md
