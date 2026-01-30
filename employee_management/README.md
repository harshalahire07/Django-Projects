# Employee Management System (Django)

## Overview

The Employee Management System is a web-based CRUD (Create, Read, Update, Delete) application developed using the Django framework.  
The project is designed to manage employee records efficiently while following standard Django architecture and best practices.

This project was developed as part of an internship onboarding task to gain hands-on experience with Django fundamentals, database modeling, and structured web application development.

---

## Key Features

- Create, view, update, and delete employee records
- Relational database design using Django ORM
- Department and role management through foreign key relationships
- Clean and responsive user interface built with Bootstrap 5
- CSRF-protected forms and structured request handling
- Confirmation prompts to prevent accidental deletions

---

## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** HTML5, Bootstrap 5
- **Database:** SQLite (Django default)
- **Version Control:** Git & GitHub

---

## Database Schema

The application uses a relational data model consisting of:

- **Department**
  - name

- **Role**
  - name

- **Employee**
  - first_name
  - last_name
  - email
  - phone
  - address
  - department (ForeignKey → Department)
  - role (ForeignKey → Role)

This structure ensures data normalization and consistency using Django ORM relationships.

---

## Application Workflow

1. Users interact with the UI to perform CRUD operations.
2. Requests are routed through Django URL configurations.
3. Views handle business logic and database interactions.
4. Responses are rendered using Django templates.
5. Feedback is provided through alerts and confirmations.

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- Git

### Installation Steps

# Clone the repository

git clone https://github.com/harshalahire07/Employee_Management_System_Django.git

# Navigate to the project directory

cd Employee_Management_System_Django

# Create and activate virtual environment

python -m venv venv
venv\Scripts\activate # Windows

# Install dependencies

pip install django

# Apply migrations

python manage.py migrate

# Run the development server

python manage.py runserver

---

## Development Notes

- SQLite is used as the database for development simplicity and ease of setup.
- The project follows Django’s recommended MVT (Model–View–Template) architecture.
- AI tools were used selectively for debugging and validation assistance, while all core logic, structure, and implementation were completed manually to ensure strong conceptual understanding.

---

## Future Enhancements

- User authentication and role-based access control
- Pagination and search functionality for employee records
- Refactoring forms using Django ModelForms for improved validation
- Soft delete implementation instead of permanent record removal
- REST API development using Django REST Framework
- Production deployment using Gunicorn and Nginx

---

## Author

**Harshal Ahire**

---
