# A4L America Website

Coming soon page for A4L America with subscription feature.

## Features

- User registration with name, email and phone
- Email verification
- $50 discount coupon generation
- Mobile responsive design
- Form validation

## Tech Stack

- Django 5.1.4
- Python 3.11
- MySQL
- Tailwind CSS

## Setup

1. Clone the repository
bash
git clone https://github.com/yourusername/a4lamerica.git
cd a4lamerica

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create .env file with following variables:
```env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_from_email
```

5. Run migrations
```bash
python manage.py migrate
```

6. Run the development server
```bash
python manage.py runserver
```

## Project Structure


a4lamerica/
├── accounts/ # Main app directory
│ ├── static/ # Static files (images, css)
│ ├── templates/ # HTML templates
│ ├── forms.py # Form definitions
│ ├── models.py # Database models
│ ├── urls.py # URL configurations
│ └── views.py # View functions
├── a4lamerica/ # Project settings directory
│ ├── settings.py # Project settings
│ ├── urls.py # Main URL configuration
│ └── wsgi.py # WSGI configuration
├── .env # Environment variables
├── .gitignore # Git ignore file
├── manage.py # Django management script
└── requirements.txt # Project dependencies


## License

[MIT](https://choosealicense.com/licenses/mit/)
