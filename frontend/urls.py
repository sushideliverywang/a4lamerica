from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('cookie-policy/', views.CookiePolicyView.as_view(), name='cookie_policy'),
    path('category/<slug:category_slug>/', views.CategoryView.as_view(), name='category'),
    path('item/<str:item_hash>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('customer/dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('customer/profile/', views.CustomerProfileView.as_view(), name='customer_profile'),
    path('item/<str:item_hash>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('customer/favorites/', views.CustomerFavoriteView.as_view(), name='customer_favorites'),
    path('customer/favorites/toggle/<str:item_hash>/', views.toggle_favorite, name='toggle_favorite'),
    
    # 搜索相关URL
    path('search/', views.SearchResultsView.as_view(), name='search_results'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    
    # 购物车相关URL
    path('cart/', views.ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/add/<str:item_hash>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/calculate-distances/', views.calculate_distances, name='calculate_distances'),
    path('api/addresses/', views.get_addresses, name='get_addresses'),
    path('api/geocode-address/', views.geocode_address, name='geocode_address'),
    path('show-map/', views.ShowMapView.as_view(), name='show_map'),
    path('api/orders/create/', views.create_order, name='create_order'),
    path('customer/order/<str:order_number>/', views.CustomerOrderDetailView.as_view(), name='customer_order_detail'),
    
    # 保修政策相关URL
    path('<slug:location_slug>/warranty/', views.WarrantyPolicyView.as_view(), name='warranty_policy'),
    path('<slug:location_slug>/warranty/agree/', views.WarrantyAgreementView.as_view(), name='warranty_agreement'),
    path('<slug:location_slug>/warranty/agree/submit/', views.agree_warranty_policy, name='agree_warranty_policy'),
    
    # 条款和条件相关URL
    path('<slug:location_slug>/terms/', views.TermsAndConditionsView.as_view(), name='terms_conditions'),
    path('<slug:location_slug>/terms/agree/', views.TermsAgreementView.as_view(), name='terms_agreement'),
    path('<slug:location_slug>/terms/agree/submit/', views.agree_terms_conditions, name='agree_terms_conditions'),
    
    # 网站地图URL（必须在通配符路由之前）
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('sitemap-<str:section>.xml', views.sitemap_view, name='sitemap_section'),
    
    # SEO页面URL
    path('services/', views.SEOServiceListView.as_view(), name='seo_service_list'),
    path('services/<str:city_key>/', views.SEOServiceListView.as_view(), name='seo_service_list'),

    # 动态产品SEO页面URL
    path('products/<str:seo_page_key>/', views.DynamicProductSEOView.as_view(), name='product_seo_page'),

    # 图片缩放服务URL
    path('resize/<int:width>x<int:height>/<path:image_path>', views.ImageResizeView.as_view(), name='image_resize'),

    # 商店页面URL（注意：这个URL需要放在最后，避免与其他URL冲突）
    # 排除已知的系统路径，避免冲突
    path('<slug:location_slug>/', views.StoreView.as_view(), name='store'),
]
