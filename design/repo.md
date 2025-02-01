# Repo

## Repo Format

The following is a general outline for the repo format.

```
# **EXAMPLE**
my_flask_app/
├── app/
│   ├── __init__.py
│   ├── extensions.py        # Flask extensions initialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py 
│   ├── core/               # Core business logic
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── product_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── auth/              # Auth blueprint **EXAMPLE**
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── api.py         # Auth API routes
│   │   └── forms.py
│   ├── products/          # Products blueprint **EXAMPLE**
│   │   ├── __init__.py
│   │   ├── routes.py      # Web routes
│   │   ├── api.py         # API routes
│   │   └── forms.py
├── static/
├── templates/
│   ├── auth/
│   └── products/
├── tests/                 # Unit tests **EXAMPLE** Might change this part
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_products.py
├── config.py
├── requirements.txt
└── run.py
```