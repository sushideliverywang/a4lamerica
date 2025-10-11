"""
模型代理文件 - 为 frontend app 提供必要的模型定义
这些模型直接连接到 nasmaha 数据库，不需要迁移
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import timedelta
from django.utils import timezone

# ==================== ACCOUNTS APP 模型代理 ====================

class User(AbstractUser):
    """用户模型代理"""
    # 只需要保留 groups 和 permissions 的自定义设置
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    class Meta:
        managed = False
        db_table = 'accounts_user'

class Customer(models.Model):
    """客户模型代理"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=10, null=True, blank=True, verbose_name="Phone Number")
    phone_verified = models.BooleanField(default=False, verbose_name="Phone Number Verified")
    credit_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Available credit balance(includes coupons and refunds)",
        verbose_name="Credit Balance"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    activation_token = models.UUIDField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'accounts_customer'
        ordering = ['-created_at']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    @property
    def is_verified(self):
        """通过 user.is_active 判断是否完成验证"""
        return self.user.is_active

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    def generate_activation_token(self):
        """生成激活令牌有效期24小时"""
        self.activation_token = uuid.uuid4()
        self.token_expiry = timezone.now() + timedelta(hours=24)
        self.save()
        return self.activation_token

# ==================== ORGANIZATION APP 模型代理 ====================

# 地址模型代理
class Address(models.Model):
    """地址模型代理"""
    street_number = models.CharField(max_length=20, verbose_name="Street Number")
    street_name = models.CharField(max_length=200, verbose_name="Street Name")
    unit_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Unit Number")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State")
    zip_code = models.CharField(max_length=20, verbose_name="ZIP Code")
    country = models.CharField(max_length=100, default="United States", verbose_name="Country")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitude")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'organization_address'
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        unique_together = [
            ['street_number', 'street_name', 'unit_number', 'city', 'state', 'zip_code', 'country']
        ]

    def __str__(self):
        address_parts = [
            f"{self.street_number} {self.street_name}",
            f"{self.unit_number}" if self.unit_number else None,
            f"{self.city}, {self.state} {self.zip_code}",
            self.country
        ]
        return ", ".join(filter(None, address_parts))

    def get_full_address(self):
        """获取完整地址字符串"""
        return str(self)

# 位置模型代理
class Location(models.Model):
    """位置模型代理"""
    LOCATION_TYPES = [
        ('STORE', 'Store'),
        ('WAREHOUSE', 'Warehouse'),
        ('STORAGE', 'Storage Facility'),
        ('SERVICE', 'Service Center'),
    ]

    TIMEZONE_CHOICES = [
        ('America/New_York', 'Eastern Time (ET)'),
        ('America/Chicago', 'Central Time (CT)'),
        ('America/Denver', 'Mountain Time (MT)'),
        ('America/Los_Angeles', 'Pacific Time (PT)'),
        ('America/Anchorage', 'Alaska Time (AKT)'),
        ('Pacific/Honolulu', 'Hawaii Time (HT)'),
    ]

    id = models.AutoField(primary_key=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, verbose_name="Company")
    name = models.CharField(max_length=200, verbose_name="Location Name")
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, verbose_name="Location Type")
    address = models.OneToOneField(Address, on_delete=models.CASCADE, verbose_name="Address")
    sales_tax_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0.0000, verbose_name="Sales Tax Rate")
    image = models.ImageField(upload_to='locations/', null=True, blank=True, verbose_name="Location Image")
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name="Deactivated At")
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',
        verbose_name="Location Timezone",
        help_text="Timezone for this specific location"
    )
    order_code = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        verbose_name="Order Code",
        help_text="3-character code used in order numbers. Must be set once and cannot be changed later."
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="URL Slug",
        help_text="URL-friendly identifier for this location"
    )

    class Meta:
        managed = False
        db_table = 'organization_location'
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        unique_together = [['company', 'name']]

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"

# 营业时间模型代理
class BusinessHours(models.Model):
    """营业时间模型代理"""
    DAYS_OF_WEEK = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='business_hours',
        verbose_name="Location"
    )
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name="Day of Week"
    )
    open_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Opening Time"
    )
    close_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Closing Time"
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name="Is Closed"
    )
    is_24_hours = models.BooleanField(
        default=False,
        verbose_name="Is 24 Hours"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'organization_businesshours'
        verbose_name = "Business Hours"
        verbose_name_plural = "Business Hours"
        unique_together = [['location', 'day_of_week']]
        ordering = ['day_of_week', 'open_time']
    
    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_of_week_display()}: Closed"
        elif self.is_24_hours:
            return f"{self.get_day_of_week_display()}: 24 Hours"
        else:
            return f"{self.get_day_of_week_display()}: {self.open_time} - {self.close_time}"
    
    @property
    def is_open_now(self):
        """检查当前时间是否在营业时间内"""
        from django.utils import timezone
        import pytz
        
        if self.is_closed:
            return False
        
        if self.is_24_hours:
            return True
        
        if not self.open_time or not self.close_time:
            return False
        
        # 获取店铺所在位置的当前时间
        location_tz = pytz.timezone(self.location.timezone)
        now = timezone.now()
        location_time = now.astimezone(location_tz)
        current_time = location_time.time()
        
        # 检查当前时间是否在营业时间内
        if self.open_time <= self.close_time:
            # 正常营业时间（同一天内）
            return self.open_time <= current_time <= self.close_time
        else:
            # 跨天营业时间（如23:00-07:00）
            return current_time >= self.open_time or current_time <= self.close_time
    
    def get_today_hours(self):
        """获取今日营业时间的显示文本"""
        if self.is_closed:
            return "Closed"
        elif self.is_24_hours:
            return "24 Hours"
        else:
            return f"{self.open_time.strftime('%I:%M %p')} - {self.close_time.strftime('%I:%M %p')}"

# 公司模型代理
class Company(models.Model):
    """公司模型代理"""
    TIMEZONE_CHOICES = [
        ('America/New_York', 'Eastern Time (ET)'),
        ('America/Chicago', 'Central Time (CT)'),
        ('America/Denver', 'Mountain Time (MT)'),
        ('America/Los_Angeles', 'Pacific Time (PT)'),
        ('America/Anchorage', 'Alaska Time (AKT)'),
        ('Pacific/Honolulu', 'Hawaii Time (HT)'),
    ]

    SUBSCRIPTION_PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('overdue', 'Overdue'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    ]

    id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=200, verbose_name="Company Name")
    ein = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Employer Identification Number")
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name="Deactivated At")
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',
        verbose_name="Company Timezone",
        help_text="Default timezone for the company"
    )

    subscription_plan = models.CharField(
        max_length=50,
        choices=SUBSCRIPTION_PLAN_CHOICES,
        default='basic',
        verbose_name="Subscription Plan"
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True, verbose_name="Subscription Start Date")
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Subscription End Date")
    payment_status = models.CharField(
        max_length=50,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        verbose_name="Payment Status"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='credit_card',
        verbose_name="Payment Method"
    )
    gateway_customer_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Payment Gateway Customer ID")
    gateway_subscription_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Payment Gateway Subscription ID")
    
    # 初始化状态字段
    bank_accounts_initialized = models.BooleanField(default=False, verbose_name="Bank Accounts Initialized")
    inventory_initialized = models.BooleanField(default=False, verbose_name="Inventory Initialized")
    liabilities_initialized = models.BooleanField(default=False, verbose_name="Liabilities Initialized")
    other_assets_initialized = models.BooleanField(default=False, verbose_name="Other Assets Initialized")

    final_validation_completed = models.BooleanField(default=False, verbose_name="Final Validation Completed")
    
    # 初始化时间记录
    initialization_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Initialization Started At")
    initialization_completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Initialization Completed At")
    initialized_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Initialized By", related_name="initialized_companies")

    class Meta:
        managed = False
        db_table = 'organization_company'
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.company_name

# 分类模型代理
class Category(models.Model):
    """分类模型代理"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True, verbose_name="Category Slug")
    parent_category = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='subcategories',
        verbose_name="Parent Category"
    )
    base_service_time = models.PositiveIntegerField(
        default=5,
        help_text="基础服务时间（分钟）",
        verbose_name="Base Service Time (minutes)"
    )

    class Meta:
        managed = False
        db_table = 'product_category'
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
    def get_effective_base_service_time(self):
        """获取有效的基础服务时间
        
        如果当前类别没有设置基础服务时间，则尝试从父类别获取
        如果都没有设置，返回默认值5分钟
        
        Returns:
            int: 基础服务时间（分钟）
        """
        if self.base_service_time and self.base_service_time > 0:
            return self.base_service_time
        
        # 尝试从父类别获取
        if self.parent_category:
            return self.parent_category.get_effective_base_service_time()
        
        # 返回默认值
        return 5

# 品牌模型代理
class Brand(models.Model):
    """品牌模型代理"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Brand Name")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    website = models.URLField(null=True, blank=True, verbose_name="Website")
    logo = models.ImageField(upload_to='brand_logos/', null=True, blank=True, verbose_name="Logo")

    class Meta:
        managed = False
        db_table = 'product_brand'
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def __str__(self):
        return self.name

# 产品型号模型代理
class ProductModel(models.Model):
    """产品型号模型代理"""
    id = models.AutoField(primary_key=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Brand")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category")
    model_number = models.CharField(max_length=100, unique=True, verbose_name="Model Number")
    description = models.TextField(blank=True, verbose_name="Description")
    msrp = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="MSRP"
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Discount Price"
    )
    link = models.URLField(max_length=500, null=True, blank=True, verbose_name="Product URL")
    gtin = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        verbose_name="GTIN (UPC/EAN)",
        help_text="Global Trade Item Number - UPC (12 digits) or EAN (13 digits)"
    )

    class Meta:
        managed = False
        db_table = 'product_productmodel'
        verbose_name = "Product Model"
        verbose_name_plural = "Product Models"

    def __str__(self):
        return f"{self.brand.name} - {self.model_number}"

# 商品状态模型代理
class ItemState(models.Model):
    """商品状态模型代理"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="State Name"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Description"
    )

    class Meta:
        managed = False
        db_table = 'inventory_itemstate'
        verbose_name = "Item State"
        verbose_name_plural = "Item States"
        ordering = ['name']

    def __str__(self):
        return self.name

# 库存商品模型代理
class InventoryItem(models.Model):
    """库存商品模型代理"""
    class Condition(models.TextChoices):
        BRAND_NEW = 'BRAND_NEW', 'Brand New - Factory Sealed'
        OPEN_BOX = 'OPEN_BOX', 'Open Box - Like New'
        SCRATCH_DENT = 'SCRATCH_DENT', 'Scratch & Dent - Minor Cosmetic Damage'
        USED_GOOD = 'USED_GOOD', 'Used - Good Condition'
        USED_FAIR = 'USED_FAIR', 'Used - Fair Condition'

    class WarrantyType(models.TextChoices):
        NONE = 'NONE', 'No Warranty'
        MANUFACTURER = 'MANUFACTURER', 'Manufacturer Warranty'
        STORE = 'STORE', 'Store Warranty'
        THIRD_PARTY = 'THIRD_PARTY', 'Third Party Warranty'
    
    class WarrantyPeriod(models.TextChoices):
        ZERO_DAYS = '0', '0 Days',
        SEVEN_DAYS = '7', '7 Days',
        THIRTY_DAYS = '30', '30 Days',
        NINETY_DAYS = '90', '90 Days',
        ONE_YEAR = '365', '365 Days',
        TWO_YEARS = '730', '730 Days',
        THREE_YEARS = '1095', '1095 Days',
        FOUR_YEARS = '1460', '1460 Days',
        FIVE_YEARS = '1825', '1825 Days'

    id = models.AutoField(primary_key=True)
    model_number = models.ForeignKey(ProductModel, on_delete=models.CASCADE, verbose_name="Model Number")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Company")
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.CASCADE, verbose_name="Location")
    load_number = models.ForeignKey('LoadManifest', on_delete=models.CASCADE, verbose_name="Load Number", null=True)
    control_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Control Number")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Serial Number")
    current_state = models.ForeignKey(ItemState, on_delete=models.CASCADE, verbose_name="Current State")
    created_by = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='inventory_items_created', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    item_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Item Value", help_text="Original purchase price allocated from supplier order")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total Cost", help_text="Total cost including shipping, platform fees and other expenses")
    published = models.BooleanField(default=False, verbose_name="Published", help_text="If checked, this item will be visible on the public website. Only one item per model needs to be published.")
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Retail Price", help_text="Retail price of the item")
    item_description = models.TextField(blank=True, null=True, verbose_name="Item Description", help_text="Unique description of this specific item, such as physical condition details, special features, etc.")
    warranty_period = models.CharField(
        max_length=4,
        choices=WarrantyPeriod.choices,
        default=WarrantyPeriod.ONE_YEAR,
        verbose_name="Warranty Period",
        help_text="Warranty period in days"
    )
    warranty_start_date = models.DateField(null=True, blank=True, verbose_name="Warranty Start Date", help_text="Start date of the warranty")
    warranty_end_date = models.DateField(null=True, blank=True, verbose_name="Warranty End Date", help_text="End date of the warranty")
    warranty_type = models.CharField(
        max_length=20,
        choices=WarrantyType.choices,
        default=WarrantyType.STORE,
        verbose_name="Warranty Type", 
        help_text="Warranty provider"
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.SCRATCH_DENT,
        verbose_name="Condition",
        help_text="Physical condition of the item"
    )
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name="Order", null=True, blank=True, related_name='inventory_items')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Unit Price")
    service_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Service Price")

    class Meta:
        managed = False
        db_table = 'inventory_inventoryitem'
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
        unique_together = [
            ['company', 'control_number'],  # 控制编号在公司内唯一
            ['company', 'serial_number'],   # 序列号在公司内唯一（如果有）
        ]
        indexes = [
            models.Index(fields=['company', 'control_number']),
            models.Index(fields=['company', 'serial_number']),
            models.Index(fields=['location']),
            models.Index(fields=['current_state']),
        ]

    def __str__(self):
        return f"{self.control_number} ({self.current_state.name})"

# 商品图片模型代理
class ItemImage(models.Model):
    """商品图片模型代理"""
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='items/',
        max_length=255
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True)

    class Meta:
        managed = False
        db_table = 'inventory_itemimage'
        ordering = ['display_order', 'created_at']
        verbose_name = 'Item Image'
        verbose_name_plural = 'Item Images'

    def __str__(self):
        return f'Image {self.id} for item {self.item.control_number}'

# 产品图片模型代理
class ProductImage(models.Model):
    """产品图片模型代理"""
    id = models.AutoField(primary_key=True)
    product_model = models.ForeignKey(
        ProductModel, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Product Model"
    )
    image = models.ImageField(
        upload_to='product_model_images/',
        max_length=500,
        verbose_name="Image"
    )
    hash = models.CharField(
        max_length=32, 
        null=True, 
        blank=True, 
        verbose_name="Image Hash"
    )

    class Meta:
        managed = False
        db_table = 'product_productimage'
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product_model}"

# 规格定义模型代理
class Spec(models.Model):
    """规格定义模型代理"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Specification Name")

    class Meta:
        managed = False
        db_table = 'product_spec'
        verbose_name = "Specification"
        verbose_name_plural = "Specifications"

    def __str__(self):
        return self.name

# 产品规格值模型代理
class ProductSpec(models.Model):
    """产品规格值模型代理"""
    id = models.AutoField(primary_key=True)
    product_model = models.ForeignKey(
        ProductModel, 
        on_delete=models.CASCADE,
        related_name='specs',
        verbose_name="Product Model"
    )
    spec = models.ForeignKey(
        Spec, 
        on_delete=models.CASCADE,
        verbose_name="Specification"
    )
    value = models.CharField(
        max_length=500, 
        null=True, 
        blank=True,
        verbose_name="Value"
    )

    class Meta:
        managed = False
        db_table = 'product_productspec'
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specifications"

    def __str__(self):
        return f"{self.product_model} - {self.spec}: {self.value}"


# 订单模型代理
class Order(models.Model):
    """订单模型代理"""
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('UPDATED', 'Updated'),
        ('SCHEDULED', 'Scheduled'),
        ('PICKED_UP', 'Picked Up'), #customer picked up from store
        ('SHIPPED', 'Shipped'), #store shipped to customer
        ('DELIVERED', 'Delivered'), #delivery team delivered to customer
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('NOT_PAID', 'Not Paid'),
        ('PAID', 'Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('REFUNDED', 'Refunded'),
    ]

    # 基础信息
    order_number = models.CharField(max_length=50, unique=True, verbose_name="Order Number")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Company")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Location")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Created By")

    # 订单状态
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='PENDING',
        verbose_name="Order Status"
    )
    
    # 支付信息
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='NOT_PAID',
        verbose_name="Payment Status"
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Tax Amount")
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Shipping Amount")
    other_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Other Fee Amount")
    
    # 新增字段：征税金额和免征税金额
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Taxable Amount")  # 征税金额
    non_taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Non-taxable Amount")  # 免征税金额
    
    # Shipping Information
    shipping_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Shipping Address")
    shipping_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Shipping Latitude")
    shipping_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Shipping Longitude")
    shipping_miles = models.IntegerField(default=0, null=True, blank=True, verbose_name="Shipping Miles")
    alternative_shipping_address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Alternative Shipping Address")
    receiver_name = models.CharField(max_length=255, verbose_name="Receiver Name")
    alternative_receiver_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Alternative Receiver Name")
    receiver_phone = models.CharField(max_length=255, verbose_name="Receiver Phone")
    alternative_receiver_phone = models.CharField(max_length=255, null=True, blank=True, verbose_name="Alternative Receiver Phone")
    receiver_email = models.EmailField(max_length=255, null=True, blank=True, verbose_name="Receiver Email")
    
   
    # 时间信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Paid At")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="Shipped At")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Delivered At")
    
    service_order = models.BooleanField(default=False, verbose_name="Service Order")
    related_order = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Related Order")
    # 备注信息
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        managed = False
        db_table = 'order_order'
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['company']),
            models.Index(fields=['customer']),
            models.Index(fields=['order_status']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"
    
    def calculate_paid_amount(self):
        """
        计算客户对订单的实际支付金额
        
        计算逻辑：
        1. 获取订单的所有DEPOSIT交易记录（实际存款）
        2. 获取订单的所有VIRTUAL_DEPOSIT交易记录（虚拟存款）
        3. 获取订单的所有WITHDRAWAL交易记录（实际取款）
        4. 获取订单的所有VIRTUAL_WITHDRAWAL交易记录（虚拟取款）
        5. 计算总支付金额=实际存款+虚拟存款+实际取款(负数)+虚拟取款(负数)
        
        Returns:
            Decimal: 实际支付金额
        """
        from decimal import Decimal
        
        # 获取实际存款记录
        deposits = TransactionRecord.objects.filter(
            order=self,
            transaction_type='DEPOSIT'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # 获取虚拟存款记录
        virtual_deposits = TransactionRecord.objects.filter(
            order=self,
            transaction_type='VIRTUAL_DEPOSIT'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # 获取订单的所有WITHDRAWAL交易记录（实际取款）
        withdrawals = TransactionRecord.objects.filter(
            order=self,
            transaction_type='WITHDRAWAL'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        # 获取订单的所有VIRTUAL_WITHDRAWAL交易记录（虚拟取款）
        virtual_withdrawals = TransactionRecord.objects.filter(
            order=self,
            transaction_type='VIRTUAL_WITHDRAWAL'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # 计算总支付金额
        total_paid = deposits + virtual_deposits + withdrawals + virtual_withdrawals
        return total_paid
    
    def calculate_order_balance(self):
        """计算订单余额
        
        计算逻辑：
        1. 获取订单的所有交易记录
        2. 按时间排序
        3. 计算余额
        
        Returns:
            Decimal: 订单余额
        """
        from decimal import Decimal
        
        transactions = TransactionRecord.objects.filter(
            order=self
        ).order_by('created_at')
        
        balance = sum(t.amount for t in transactions)
        return balance
    
    def calculate_pre_tax_total(self):
        """
        计算订单税前总额（未保存字段）。
        税前总额 = 所有item的unit_price + service_price之和 + shipping_amount + other_fee_amount
        Returns:
            Decimal: 税前总额
        """
        from decimal import Decimal
        
        # 注意：这里需要访问inventory_items，但在代理模型中可能没有这个关系
        # 暂时返回0，实际使用时需要根据具体情况调整
        items_total = Decimal('0.00')
        pre_tax_total = items_total + self.shipping_amount + self.other_fee_amount
        return pre_tax_total
    
    def get_virtual_transfers(self):
        """获取订单的虚拟转账记录
        
        Returns:
            QuerySet: 虚拟转账记录
        """
        return TransactionRecord.objects.filter(
            order=self,
            transaction_type__in=['VIRTUAL_DEPOSIT', 'VIRTUAL_WITHDRAWAL']
        ).order_by('created_at')
    
    def can_transfer_to_other_order(self, amount):
        """检查是否可以转账到其他订单
        
        Args:
            amount (Decimal): 转账金额
            
        Returns:
            bool: 是否可以转账
        """
        current_balance = self.calculate_order_balance()
        return current_balance >= amount

# 客户收藏模型代理
class CustomerFavorite(models.Model):
    """客户收藏模型代理"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Customer"
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="Inventory Item"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        managed = False
        db_table = 'customer_customerfavorite'
        verbose_name = "Customer Favorite"
        verbose_name_plural = "Customer Favorites"
        unique_together = ['customer', 'item']  # 确保一个客户不会重复收藏同一个商品
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['item', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer} likes {self.item}"

# 购物车模型代理
class ShoppingCart(models.Model):
    """购物车模型代理"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Customer"
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Inventory Item"
    )
    
    price_at_add = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price at Add"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        managed = False
        db_table = 'customer_shoppingcart'
        verbose_name = "Shopping Cart Item"
        verbose_name_plural = "Shopping Cart Items"
        unique_together = ['customer', 'item']  # 确保一个商品在购物车中只出现一次
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['item', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer}'s cart: {self.item}"

# 客户地址模型代理
class CustomerAddress(models.Model):
    """客户地址模型代理"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    street_address = models.CharField(max_length=255)
    apartment_suite = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)  # 使用两字母州代码
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=2, default='US')  # 使用两字母国家代码
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    formatted_address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'customer_address'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"

    def get_full_address(self):
        """获取完整地址字符串"""
        parts = [self.street_address]
        if self.apartment_suite:
            parts.append(self.apartment_suite)
        parts.extend([self.city, self.state, self.zip_code])
        return ', '.join(parts)

# 订单状态历史模型代理
class OrderStatusHistory(models.Model):
    """订单状态历史模型代理"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', verbose_name="Order")
    from_status = models.CharField(max_length=20, blank=True, null=True, verbose_name="From Status")
    to_status = models.CharField(max_length=20, verbose_name="To Status")
    changed_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, verbose_name="Changed By")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")

    class Meta:
        managed = False
        db_table = 'order_orderstatushistory'
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.from_status} to {self.to_status}"

# 交易记录模型代理
class TransactionRecord(models.Model):
    """交易记录模型代理"""
    TRANSACTION_TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),           # Customer deposits money
        ('WITHDRAWAL', 'Withdrawal'),     # Customer withdraws money
        ('CONSUMPTION', 'Consumption'),   # Customer uses money to purchase
        ('CANCELLATION', 'Cancellation'), # Order cancellation, money returned
        ('VIRTUAL_DEPOSIT', 'Virtual Deposit'), # Virtual deposit, no money moved,same customer use money to other order, amount is positive
        ('VIRTUAL_WITHDRAWAL', 'Virtual Withdrawal'), # Virtual withdrawal, money from other order same customer,  amount is negative
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CASH', 'Cash'),
        ('ZELLE', 'Zelle'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('SNAP_FINANCE', 'Snap Finance'),
        ('SNAP_CREDIT', 'Snap Credit'),
        ('ACIMA_FINANCE', 'Acima Finance'),
        ('AMERICAN_FIRST_FINANCE', 'American First Finance'),
        ('CHECK', 'Check'),
        ('OTHER', 'Other'),
    ]

    # Basic Information
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,  # Prevent transaction loss when customer is deleted
        verbose_name="Customer"
    )
    company = models.ForeignKey(
        'Company',
        on_delete=models.PROTECT,
        verbose_name="Company"
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT,
        verbose_name="Location"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name="Transaction Type"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Amount"
    )

    financial_confirmation = models.BooleanField(
        default=False,
        verbose_name="Financial Confirmation"
    )
    financial_confirmation_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Financial Confirmation At"
    )
    financial_confirmation_by = models.ForeignKey(
        'Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Financial Confirmation By",
        related_name='financial_confirmed_transactions'
    )

    # Related Information
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        verbose_name="Related Order"
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        verbose_name="Payment Method"
    )
    related_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Transaction"
    )

    # Time Information
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    created_by = models.ForeignKey('Staff', on_delete=models.CASCADE, verbose_name="Created By", related_name='created_transactions')
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Reference"
    )

    class Meta:
        managed = False
        db_table = 'order_transactionrecord'
        verbose_name = "Transaction Record"
        verbose_name_plural = "Transaction Records"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.id} - {self.get_transaction_type_display()} - {self.amount}"

# 保修政策模型代理
class LocationWarrantyPolicy(models.Model):
    """位置保修政策模型代理"""
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Location")
    title = models.CharField(max_length=200, verbose_name="Policy Title", help_text="Warranty policy title")
    summary = models.TextField(max_length=500, verbose_name="Policy Summary", help_text="Brief summary of the warranty policy")
    content_file = models.FileField(
        upload_to='warranty_policies/',
        verbose_name="Policy Content File",
        help_text="HTML file containing the detailed warranty policy content"
    )
    version = models.CharField(max_length=20, default='1.0', verbose_name="Policy Version")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    effective_date = models.DateField(verbose_name="Effective Date", help_text="Date when this policy becomes effective")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'organization_locationwarrantypolicy'
        verbose_name = "Location Warranty Policy"
        verbose_name_plural = "Location Warranty Policies"
        unique_together = ['location', 'version']  # 确保每个location的每个版本只能有一个保修政策

    def __str__(self):
        return f"Warranty Policy v{self.version} for {self.location.name}"
    
    def get_policy_summary(self, max_length=100):
        """获取保修政策的摘要"""
        if len(self.summary) <= max_length:
            return self.summary
        return self.summary[:max_length] + "..."
    
    def get_content_url(self):
        """获取保修政策文件的URL"""
        if self.content_file:
            return self.content_file.url
        return None
    
    def get_content_path(self):
        """获取保修政策文件的本地路径"""
        if self.content_file:
            return self.content_file.path
        return None
    
    @classmethod
    def get_active_policy_for_location(cls, location):
        """获取指定location的当前有效保修政策"""
        try:
            return cls.objects.filter(location=location, is_active=True).order_by('-effective_date').first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_policy_for_location(cls, location, version=None):
        """获取指定location的保修政策"""
        try:
            if version:
                return cls.objects.get(location=location, version=version)
            else:
                return cls.get_active_policy_for_location(location)
        except cls.DoesNotExist:
            return None

# 条款条件模型代理
class LocationTermsAndConditions(models.Model):
    """位置条款条件模型代理"""
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Location")
    title = models.CharField(max_length=200, verbose_name="Terms Title", help_text="Terms and conditions title")
    summary = models.TextField(max_length=500, verbose_name="Terms Summary", help_text="Brief summary of the terms and conditions")
    content_file = models.FileField(
        upload_to='terms_conditions/',
        verbose_name="Terms Content File",
        help_text="HTML file containing the detailed terms and conditions content"
    )
    version = models.CharField(max_length=20, default='1.0', verbose_name="Terms Version")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    effective_date = models.DateField(verbose_name="Effective Date", help_text="Date when these terms become effective")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'organization_locationtermsandconditions'
        verbose_name = "Location Terms and Conditions"
        verbose_name_plural = "Location Terms and Conditions"
        unique_together = ['location', 'version']  # 确保每个location的每个版本只能有一个条款

    def __str__(self):
        return f"Terms and Conditions v{self.version} for {self.location.name}"
    
    def get_terms_summary(self, max_length=100):
        """获取条款和条件的摘要"""
        if len(self.summary) <= max_length:
            return self.summary
        return self.summary[:max_length] + "..."
    
    def get_content_url(self):
        """获取条款和条件文件的URL"""
        if self.content_file:
            return self.content_file.url
        return None
    
    def get_content_path(self):
        """获取条款和条件文件的本地路径"""
        if self.content_file:
            return self.content_file.path
        return None
    
    @classmethod
    def get_active_terms_for_location(cls, location):
        """获取指定location的当前有效条款和条件"""
        try:
            return cls.objects.filter(location=location, is_active=True).order_by('-effective_date').first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_terms_for_location(cls, location, version=None):
        """获取指定location的条款和条件"""
        try:
            if version:
                return cls.objects.get(location=location, version=version)
            else:
                return cls.get_active_terms_for_location(location)
        except cls.DoesNotExist:
            return None

# 客户保修政策同意模型代理
class CustomerWarrantyPolicy(models.Model):
    """客户保修政策同意模型代理"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='warranty_agreements',
        verbose_name="Customer"
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.CASCADE,
        related_name='customer_warranty_agreements',
        verbose_name="Location"
    )
    warranty_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name="Warranty Version",
        help_text="Version of the warranty policy that the customer agreed to"
    )
    agreed_at = models.DateTimeField(auto_now_add=True, verbose_name="Agreed At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    
    class Meta:
        managed = False
        db_table = 'customer_customerwarrantypolicy'
        verbose_name = "Customer Warranty Policy Agreement"
        verbose_name_plural = "Customer Warranty Policy Agreements"
        unique_together = ['customer', 'location', 'warranty_version']  # 确保一个客户对同一个location的同一个版本只能有一条同意记录
        indexes = [
            models.Index(fields=['customer', 'agreed_at']),
            models.Index(fields=['location', 'agreed_at']),
        ]
        ordering = ['-agreed_at']

    def __str__(self):
        return f"{self.customer} agreed to {self.location} warranty policy on {self.agreed_at.strftime('%Y-%m-%d')}"
    
    @classmethod
    def has_agreed(cls, customer, location, warranty_version=None):
        """检查客户是否已经同意了指定location的保修条款"""
        if warranty_version:
            return cls.objects.filter(
                customer=customer, 
                location=location, 
                warranty_version=warranty_version
            ).exists()
        else:
            # 如果没有指定版本，检查是否有任何版本的同意记录
            return cls.objects.filter(customer=customer, location=location).exists()
    
    @classmethod
    def get_agreement_date(cls, customer, location):
        """获取客户同意指定location保修条款的日期"""
        try:
            agreement = cls.objects.get(customer=customer, location=location)
            return agreement.agreed_at
        except cls.DoesNotExist:
            return None

# 客户条款同意模型代理
class CustomerTermsAgreement(models.Model):
    """客户条款同意模型代理"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='terms_agreements',
        verbose_name="Customer"
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.CASCADE,
        related_name='customer_terms_agreements',
        verbose_name="Location"
    )
    terms_version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name="Terms Version",
        help_text="Version of the terms and conditions that the customer agreed to"
    )
    agreed_at = models.DateTimeField(auto_now_add=True, verbose_name="Agreed At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    
    class Meta:
        managed = False
        db_table = 'customer_customertermsagreement'
        verbose_name = "Customer Terms Agreement"
        verbose_name_plural = "Customer Terms Agreements"
        unique_together = ['customer', 'location', 'terms_version']  # 确保一个客户对同一个location的同一个版本只能有一条同意记录
        indexes = [
            models.Index(fields=['customer', 'agreed_at']),
            models.Index(fields=['location', 'agreed_at']),
        ]
        ordering = ['-agreed_at']

    def __str__(self):
        return f"{self.customer} agreed to {self.location} terms and conditions on {self.agreed_at.strftime('%Y-%m-%d')}"
    
    @classmethod
    def has_agreed(cls, customer, location, terms_version=None):
        """检查客户是否已经同意了指定location的条款和条件"""
        if terms_version:
            return cls.objects.filter(
                customer=customer, 
                location=location, 
                terms_version=terms_version
            ).exists()
        else:
            # 如果没有指定版本，检查是否有任何版本的同意记录
            return cls.objects.filter(customer=customer, location=location).exists()
    
    @classmethod
    def get_agreement_date(cls, customer, location):
        """获取客户同意指定location条款和条件的日期"""
        try:
            agreement = cls.objects.get(customer=customer, location=location)
            return agreement.agreed_at
        except cls.DoesNotExist:
            return None

# 状态转换模型代理
class StateTransition(models.Model):
    """状态转换模型代理"""
    id = models.AutoField(primary_key=True)
    from_state = models.ForeignKey(
        ItemState, 
        on_delete=models.CASCADE,
        related_name='transitions_from',
        verbose_name="From State"
    )
    to_state = models.ForeignKey(
        ItemState, 
        on_delete=models.CASCADE,
        related_name='transitions_to',
        verbose_name="To State"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Description"
    )

    class Meta:
        managed = False
        db_table = 'inventory_statetransition'
        verbose_name = "State Transition"
        verbose_name_plural = "State Transitions"
        unique_together = ['from_state', 'to_state']
        ordering = ['from_state', 'to_state']

    def __str__(self):
        return f"{self.from_state} -> {self.to_state}"

# 库存状态历史模型代理
class InventoryStateHistory(models.Model):
    """库存状态历史模型代理"""
    id = models.AutoField(primary_key=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='state_history', verbose_name="Inventory Item")
    state_transition = models.ForeignKey(StateTransition, on_delete=models.CASCADE, verbose_name="State Transition")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    changed_by = models.ForeignKey('Staff', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Changed By")
    notes = models.TextField(blank=True, verbose_name="Change Notes")

    class Meta:
        managed = False
        db_table = 'inventory_inventorystatehistory'
        verbose_name = "Inventory State History"
        verbose_name_plural = "Inventory State Histories"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['inventory_item', 'changed_at']),
            models.Index(fields=['state_transition']),
            models.Index(fields=['changed_by']),
        ]

    def __str__(self):
        return f"{self.inventory_item}: {self.state_transition} at {self.changed_at}"

# 装载清单模型代理
class LoadManifest(models.Model):
    """装载清单模型代理 - 管理批次发货信息和成本"""
    class Status(models.IntegerChoices):
        TEMPORARY = 1, 'Temporary'    # 仅在临时表
        CONVERTING = 2, 'Converting'  # 两表共存
        INVENTORY = 3, 'Inventory'    # 仅在正式库存
    
    id = models.AutoField(primary_key=True)
    load_number = models.CharField(
        max_length=100, 
        verbose_name="Load Number", 
        help_text="Load number must be unique within a company"
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.TEMPORARY,
        verbose_name="Status"
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        verbose_name="Company", 
        help_text="Company that purchased this load"
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Location", help_text="Location where this load is stored")
    load_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Load Cost", help_text="Total cost of the goods")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Shipping Fee", help_text="Cost of shipping")
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Other Fee", help_text="Additional fees or charges")
    purchase_date = models.DateField(verbose_name="Purchase Date", help_text="Date when the load was purchased")
    arrived_date = models.DateField(null=True, blank=True, verbose_name="Arrived Date", help_text="Date when the load arrived")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='load_manifests_created', verbose_name="Created By")

    class Meta:
        managed = False
        db_table = 'inventory_loadmanifest'
        verbose_name = "Load Manifest"
        verbose_name_plural = "Load Manifests"
        ordering = ['-purchase_date', '-created_at']
        unique_together = ['company', 'load_number']
        indexes = [
            models.Index(fields=['load_number']),
            models.Index(fields=['company']),
            models.Index(fields=['location']),
            models.Index(fields=['purchase_date']),
            models.Index(fields=['arrived_date']),
        ]

    def __str__(self):
        return f"{self.load_number} ({self.purchase_date})"

    @property
    def load_value(self):
        """Calculate items value without shipping and other fees"""
        """load_cost is the amount paid to the vendor,including shipping and other fees"""
        """shipping_fee and other_fee are the costs of shipping and other fees"""
        return self.load_cost - self.shipping_fee - self.other_fees

# 库存位置历史模型代理
class InventoryLocationHistory(models.Model):
    """位置转移历史记录模型代理 - 记录每个产品的位置变更历史"""
    id = models.AutoField(primary_key=True)
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='location_history', verbose_name="Inventory Item")
    from_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='transfers_from', verbose_name="From Location")
    to_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='transfers_to', verbose_name="To Location")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    changed_by = models.ForeignKey('Staff', on_delete=models.CASCADE, verbose_name="Changed By")
    notes = models.TextField(blank=True, verbose_name="Transfer Notes")

    class Meta:
        managed = False
        db_table = 'inventory_inventorylocationhistory'
        verbose_name = "Inventory Location History"
        verbose_name_plural = "Inventory Location Histories"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['inventory_item', 'changed_at']),
            models.Index(fields=['from_location']),
            models.Index(fields=['to_location']),
            models.Index(fields=['changed_by']),
        ]

    def __str__(self):
        return f"{self.inventory_item}: {self.from_location} -> {self.to_location} at {self.changed_at}"

# 临时库存项目模型代理
class TemporaryInventoryItem(models.Model):
    """临时库存表模型代理 - 用于临时存储库存项目,在导入manifest时使用,数据清理后会转移到正式库存"""
    id = models.AutoField(primary_key=True)
    model_number = models.CharField(max_length=255, verbose_name="Model Number", help_text="Product model number that needs to be matched with ProductModel")
    load_number = models.ForeignKey(LoadManifest, on_delete=models.CASCADE, verbose_name="Load Number", null=True)
    control_number = models.CharField(max_length=100, verbose_name="Control Number")
    serial_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Serial Number")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    msrp = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="MSRP")
    link = models.URLField(null=True, blank=True, verbose_name="Link")
    temporary_brand = models.CharField(max_length=255, null=True, blank=True, verbose_name="Temporary Brand")
    temporary_category = models.CharField(max_length=255, null=True, blank=True, verbose_name="Temporary Category")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Company")
    raw_data = models.JSONField(null=True, blank=True, verbose_name="Raw Data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='temp_items_created', verbose_name="Created By")
    matched_product = models.ForeignKey(ProductModel, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Matched Model Number")
    item_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Item Value", help_text="Original purchase price allocated from supplier order")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total Cost", help_text="Total cost including shipping, platform fees and other expenses")
    safecode = models.CharField(max_length=100, null=True, blank=True, verbose_name="Safe Code")

    class Meta:
        managed = False
        db_table = 'inventory_temporaryinventoryitem'
        verbose_name = "Temporary Inventory Item"
        verbose_name_plural = "Temporary Inventory Items"
        unique_together = [
            ['company', 'control_number'],
            ['company', 'serial_number'],
        ]
        indexes = [
            models.Index(fields=['model_number']),
            models.Index(fields=['company', 'control_number']),
            models.Index(fields=['company', 'serial_number']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.model_number} - {self.control_number}"

class Staff(models.Model):
    """员工模型代理"""
    # 基础关联
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="User Account")
    company_id = models.IntegerField(verbose_name="Company ID")  # 使用 ID 而不是外键
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    avatar = models.CharField(max_length=100, null=True, blank=True)  # 默认头像
    # 注册相关字段
    registration_token = models.UUIDField(
        default=uuid.uuid4, 
        null=True, 
        blank=True, 
        unique=True, 
        verbose_name="Registration Token"
    )
    token_expiry = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Token Expiry"
    )
    roles = models.ManyToManyField(  # 新增
        'Role',
        through='StaffRole',
        related_name='staff_members'
    )
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name="Deactivated At")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        managed = False
        db_table = 'accounts_staff'
        verbose_name = "Staff"
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"

    def is_owner(self):
        """检查该员工是否是 owner"""
        return self.staffrole_set.filter(
            role__role_name='OWNER',
            is_active=True
        ).exists()
    
    def has_financial_role(self):
        """检查该员工是否具有财务相关角色"""
        return self.staffrole_set.filter(
            role__role_name__in=['FINANCE', 'ACCOUNTANT'],
            is_active=True
        ).exists()
    
    def get_ordered_roles(self):
        """
        获取该员工的角色列表，按照 ROLE_CHOICES 定义顺序排序
        """
        from django.db.models import Case, When, Value, IntegerField

        role_order_case = Case(
            *[When(role__role_name=choice[0], then=Value(i))
              for i, choice in enumerate(Role.ROLE_CHOICES)],
            output_field=IntegerField()
        )

        return self.roles.annotate(
            role_order=role_order_case
        ).order_by('role_order')
    
    def generate_registration_token(self):
        """生成注册令牌和过期时间"""
        from datetime import timedelta
        
        self.registration_token = uuid.uuid4()
        self.token_expiry = timezone.now() + timedelta(days=2)  # 2天有效期
        self.user.is_active = False  # 未完成注册的用户设为非激活
        self.user.save()
        self.save()
        return self.registration_token

    def is_token_valid(self):
        """检查令牌是否有效"""
        if not self.registration_token or not self.token_expiry:
            return False
        return timezone.now() <= self.token_expiry

    @property
    def staff_status(self):
        """获取员工状态"""
        if self.is_active:
            return 'ACTIVE'
        elif self.is_token_valid():
            return 'PENDING'
        elif self.registration_token:
            return 'EXPIRED'
        elif self.deactivated_at:
            return 'INACTIVE'
        return 'UNKNOWN'
    
    def deactivate(self):
        """停用员工账户"""
        now = timezone.now()
        self.is_active = False
        self.deactivated_at = now
        self.user.is_active = False
        self.user.save()
        self.save()

class Role(models.Model):
    """角色模型代理"""
    ROLE_CHOICES = [
        # 管理层角色
        ('OWNER', 'Business Owner'),
        ('MANAGER', 'Store Manager'),

        # 销售相关角色
        ('SALES', 'Sales Representative'),

        # 库存相关角色
        ('INVENTORY', 'Inventory Staff'),
        ('WAREHOUSE', 'Warehouse Staff'),
        
        # 技术服务角色
        ('TECHNICIAN', 'Technician'),
        ('DELIVERY', 'Delivery Staff'),
        ('INSTALLER', 'Installation Staff'),
        
        # 财务角色
        ('FINANCE', 'Finance Staff'),
        ('ACCOUNTANT', 'Accountant'),
    ]
    
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(
        max_length=50, 
        choices=ROLE_CHOICES,  # 添加 choices
        unique=True
    )
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        managed = False
        db_table = 'accounts_role'
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['role_name']

    def __str__(self):
        return f"{self.get_role_name_display() or self.role_name}"

    @classmethod
    def get_ordered_roles(cls):
        """
        获取按照 ROLE_CHOICES 定义顺序排序的角色列表
        """
        from django.db.models import Case, When, Value, IntegerField
        
        role_order_case = Case(
            *[When(role_name=choice[0], then=Value(i))
              for i, choice in enumerate(cls.ROLE_CHOICES)],
            output_field=IntegerField()
        )
        
        return cls.objects.annotate(
            role_order=role_order_case
        ).order_by('role_order')

class StaffRole(models.Model):
    """员工角色关联表代理"""
    id = models.AutoField(primary_key=True)
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    is_active = models.BooleanField(default=False, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        managed = False
        db_table = 'accounts_staffrole'
        verbose_name = "Staff Role"
        verbose_name_plural = "Staff Roles"
        unique_together = ['staff', 'role', 'start_date']
        indexes = [
            models.Index(fields=['staff', 'is_active']),
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return f"{self.staff} - {self.role}"

    def save(self, *args, **kwargs):
        # 如果设置了结束日期，自动将 is_active 设为 False
        if self.end_date and self.end_date <= timezone.now().date():
            self.is_active = False
        super().save(*args, **kwargs)

