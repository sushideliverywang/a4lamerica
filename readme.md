# A4L America - Professional Appliance Sales & Services Platform

A full-featured e-commerce platform specializing in appliance sales, delivery, installation, and recycling services. Built on Django with comprehensive SEO optimization and multi-location support.

## 🚀 Live Website

**Website**: [https://a4lamerica.com](https://a4lamerica.com)

## 🌟 Key Features

### E-commerce Platform
- **Product Catalog**: Comprehensive inventory management with categories, brands, and product models
- **Shopping Cart & Checkout**: Full order processing with payment tracking
- **Customer Accounts**: User registration, favorites, order history, and address management
- **Multi-location Support**: Service across multiple Georgia locations (Doraville, Chamblee, Norcross, etc.)

### Service Offerings
- **Appliance Delivery**: Professional delivery service with distance-based pricing
- **Installation Services**: Refrigerator, washer, dryer, dishwasher, stove, microwave, wall oven installation
- **Haul Away & Recycling**: Eco-friendly disposal and recycling services
- **Same-day Service**: Subject to availability across all service areas

### SEO & Marketing Features
- **Advanced SEO Configuration**: City-specific and service-specific SEO optimization
- **XML Sitemaps**: Auto-generated sitemaps for products, categories, and services
- **Structured Data**: Rich snippets for products and services
- **Local SEO**: Geo-targeted content for multiple Georgia cities
- **Mobile Responsive**: Optimized for all devices with Tailwind CSS

### Business Management
- **Staff Role Management**: Owner, manager, sales, inventory, technician, and finance roles
- **Inventory Tracking**: Real-time inventory with state transitions and location tracking
- **Order Management**: Complete order lifecycle from pending to delivered
- **Financial Tracking**: Transaction records, payment methods, and customer credit balances
- **Warranty & Terms**: Location-specific warranty policies and terms management

## 🛠 Tech Stack

- **Backend**: Django 5.1.4, Python 3.11
- **Database**: MySQL with proxy models connecting to shared `nasmaha` database
- **Frontend**: Tailwind CSS, responsive design
- **SEO**: Django Sitemaps, structured data, meta optimization
- **Integrations**: Google Maps API, geolocation services
- **Media**: Shared media storage with external SSD mounting

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11+
- MySQL 5.7+
- Access to shared `nasmaha` database

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/a4lamerica.git
cd a4lamerica
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create `.env` file with the following variables:
```env
# Database Configuration (connects to shared nasmaha database)
DATABASE_NAME=nasmaha_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306

# Django Configuration
SECRET_KEY=your_secret_key
DEBUG=False  # Set to True for development
COMPANY_ID=58  # A4L America company ID

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_from_email

# Google Services
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_MAPS_CLIENT_API_KEY=your_client_api_key
RECAPTCHA_SITE_KEY=your_recaptcha_site_key
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key
RECAPTCHA_SCORE_THRESHOLD=0.5

# Additional Configuration
ITEM_HASH_SECRET_KEY=your_hash_secret_key
EXTRA_ALLOWED_HOSTS=your_external_ip  # For production
```

5. **No Database Migrations Required**
This project uses proxy models connecting to an existing database. No migrations needed.

6. **Collect Static Files** (Production)
```bash
python manage.py collectstatic
```

7. **Run Development Server**
```bash
python manage.py runserver
```

## 📁 Project Architecture

```
a4lamerica/
├── a4lamerica/          # Django project settings
│   ├── settings.py      # Environment-aware configuration
│   ├── urls.py          # Main URL routing
│   └── wsgi.py          # WSGI configuration
├── accounts/            # User authentication (proxy models)
│   ├── models.py        # Imports from frontend.models_proxy
│   ├── views.py         # Authentication views
│   └── urls.py          # Auth URL patterns
├── frontend/            # Main e-commerce application
│   ├── models_proxy.py  # All database models (proxy to nasmaha DB)
│   ├── views.py         # Business logic and SEO views
│   ├── urls.py          # Frontend URL patterns
│   ├── sitemaps.py      # XML sitemap generation
│   ├── utils.py         # SEO utilities and helpers
│   ├── config/          # SEO and business configuration
│   │   └── seo_keywords.py  # City and service SEO config
│   ├── templates/       # HTML templates
│   ├── static/          # CSS, JS, images
│   └── templatetags/    # Custom template tags
├── docs/                # Documentation and business files
├── logs/                # Application logs
├── media/              # Uploaded files (external mount)
├── staticfiles/        # Collected static files
└── scripts/            # Utility scripts
```

## 🎯 SEO Features

### Local SEO Optimization
- **Multi-city targeting**: Doraville, Chamblee, Norcross, Duluth, Tucker, Brookhaven, Lilburn, Sandy Springs, Dunwoody, Peachtree Corners
- **Service-specific pages**: Each service type optimized for local search
- **Structured data markup**: Product, service, and local business schemas

### Technical SEO
- **XML Sitemaps**: Auto-generated for all content types
- **Meta optimization**: Dynamic title tags and descriptions
- **Mobile-first design**: Responsive across all devices
- **Page speed optimization**: Optimized assets and caching

### Content Strategy
- **Long-tail keywords**: City + service combinations
- **Service descriptions**: Detailed pricing and feature information
- **Local content**: City-specific information and service areas

## 🌍 Service Areas

**Primary Location**: Doraville, GA
**Service Coverage**:
- Doraville, Chamblee, Norcross, Duluth
- Tucker, Brookhaven, Lilburn
- Sandy Springs, Dunwoody, Peachtree Corners
- Greater Atlanta Metro Area

## 🔧 Development & Production

### Development Environment
- Debug mode enabled
- Local network access (192.168.1.*)
- File-based logging
- Relaxed security settings

### Production Environment
- SSL/HTTPS enforcement
- Secure cookie settings
- Apache integration
- External media storage
- Comprehensive logging

## 📊 Business Model

- **B2C E-commerce**: Direct sales to consumers
- **Service Integration**: Sales + installation in one platform
- **Multi-location**: Expandable to additional service areas
- **Shared Resources**: Leverages existing nasmaha infrastructure

## 🤝 Contributing

This is a production e-commerce platform. Contact the development team for contribution guidelines.

## 📄 License

Proprietary - A4L America, LLC