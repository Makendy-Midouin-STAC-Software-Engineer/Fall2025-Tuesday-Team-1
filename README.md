# NYC Restaurant Inspections App

[![Django CI/CD](https://github.com/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1/actions/workflows/django.yml/badge.svg)](https://github.com/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1/actions/workflows/django.yml)

**Coverage Status:**
- Main: [![Coverage Status](https://coveralls.io/repos/github/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1/badge.svg?branch=main&cachebust=20251105)](https://coveralls.io/github/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1?branch=main)
- Develop: [![Coverage Status](https://coveralls.io/repos/github/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1/badge.svg?branch=develop&cachebust=20251105)](https://coveralls.io/github/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1?branch=develop)

A Django web application for searching and tracking NYC restaurant health inspections with a comprehensive follow/subscribe system.

## Features

- 🔍 **Restaurant Search**: Search through 289K+ NYC restaurant inspections
- ⭐ **Favorites System**: Save your favorite restaurants  
- 🔔 **Follow/Subscribe**: Get notifications for restaurant updates
- 📊 **Health Grades**: View inspection grades and violation details
- 📱 **Responsive Design**: Mobile-friendly interface
- 🚀 **Performance Optimized**: Fast search with pagination

## Live Demo

Visit the live application: [NYC Restaurant Inspections](https://nyc-restaurants-fresh.eba-nfmqf9hf.us-east-1.elasticbeanstalk.com)

## Technology Stack

- **Backend**: Django 5.2.6, Python 3.11
- **Database**: SQLite (109MB dataset)
- **Frontend**: HTML5, CSS3, JavaScript (AJAX)
- **Deployment**: AWS Elastic Beanstalk
- **CI/CD**: GitHub Actions
- **Code Quality**: Black, Flake8, Coverage.py

## Getting Started

### Prerequisites

- Python 3.11+
- pip
- git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Makendy-Midouin-STAC-Software-Engineer/Fall2025-Tuesday-Team-1.git
cd Fall2025-Tuesday-Team-1
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start development server:
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to see the application.

## Testing

Run the test suite:
```bash
python manage.py test
```

Run with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

## Code Quality

Format code with Black:
```bash
black .
```

Lint with Flake8:
```bash
flake8 .
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- **Code Quality**: Black formatting, Flake8 linting
- **Testing**: Django test suite with coverage reporting
- **Deployment**: Automatic deployment to AWS Elastic Beanstalk on main branch
- **Coverage**: Integration with Coveralls for coverage tracking

### For Contributors

The CI/CD pipeline will automatically run when you:
- Push commits to `main` or `develop` branches
- Open a Pull Request against `main` or `develop` branches

**Requirements for passing CI:**
- All code must pass Black formatting (`black --check .`)
- All code must pass Flake8 linting (`flake8 .`)
- Django system checks must pass (`python manage.py check`)
- All tests must pass (`python manage.py test`)

**Local testing before committing:**
```bash
# Run the full CI pipeline locally
black --check .          # Check formatting
flake8 .                 # Check linting
python manage.py check   # Django system checks
python manage.py test    # Run test suite
```

**AWS Deployment (Optional):**
Deployment to AWS Elastic Beanstalk only occurs on pushes to `main` branch. 
To enable deployment, repository maintainers need to set these secrets in GitHub:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

All pull requests must pass CI checks before merging.

## License

This project is part of the Fall 2025 Software Engineering course.
