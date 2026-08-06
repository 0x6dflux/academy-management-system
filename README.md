# Academy Management System

## Overview
Backend API for managing an educational institute, developed as the final project for Python Bootcamp. This system handles class reporting and teacher payroll calculations, featuring advanced architectural patterns like idempotent cascade soft-deletion, custom email-based authentication, and strict role-based access control.

## Tech Stack
- **Language:** Python 3.14
- **Framework:** Django 6.0 & Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** SimpleJWT
- **API Docs:** drf-yasg (Swagger)
- **Type Checking:** MyPy (strict mode)

## Key Architectural Decisions & Features

### 1. Advanced Soft-Deletion System
Implemented a bulletproof soft-deletion mechanism using Abstract Mixins (`SoftDeleteMixin`), bypassing common Django traps:
- **Base Manager Trap Resolution:** Explicitly set `base_manager_name = "all_objects"` to prevent `DoesNotExist` errors when accessing reverse relations of soft-deleted objects.
- **Idempotency Guards:** Soft-deleting an already deleted object (or its children) does not trigger unnecessary DB saves or overwrite the original `updated_by` audit trail.
- **Configurable Cascade:** Inner `SoftDeletionOptions` class allows models to opt-out of cascade deletion (e.g., `Report` model is immune to cascade deletion when a `Course` is deleted).

### 2. Custom User & Authentication Architecture
Replaced Django's default username-based auth with an email-based system, resolving complex Multiple Inheritance (MRO) conflicts:
- **Email as USERNAME_FIELD:** Removed `username`, using `email` for authentication.
- **Manager MRO Resolution:** Explicitly declared `objects` and `all_objects` in the `User` model to resolve the `AbstractUser` vs `SoftDeleteMixin` manager clash.
- **DRY Manager Logic:** Used `CreateUserWithEmailMixin` to inject email-based creation logic into both `UserSoftDeleteManager` and `UserAllObjectsManager` without code duplication.

### 3. Role-Based Access Control (RBAC)
Implemented granular permissions tailored to the PRD:
- `IsRoleAdmin`
- `IsEducationOfficerOrAdmin`
- `IsFinanceOfficerOrAdmin`
- `IsTeacherOrAdmin`
- `IsTeacherOrEducationOfficerOrAdmin`

### 4. CLI Management Command
Created `create_user` management command for seeding initial users (bypassing the lack of public sign-up), complete with input validation and role checks.

## Project Structure
- `account/`: User, TeacherProfile, Custom Managers, Permissions.
- `education/`: School, Semester, Course (AcademicClass), Session, Report.
- `finance/`: Wage calculations.
- `system/`: Base models (`BaseMixin`, `SoftDeleteMixin`), Custom Soft Delete Managers/Querysets, Validators.

## Getting Started

### Prerequisites
- Python 3.14+
- PostgreSQL

### Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd academy-management-system
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your PostgreSQL database and update `.env` or `settings.py` with your DB credentials.

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

### Usage
1. **Create the first Admin user via CLI:**
   ```bash
   python manage.py create_user -e admin@example.com -p securepassword -r ADM
   ```
2. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
3. **API Documentation:**
   Navigate to `http://127.0.0.1:8000/swagger/` to view the interactive Swagger UI.

4. **Authentication:**
   Obtain a JWT token via `POST /api/v1/token/` and use it as a `Bearer` token in subsequent requests.

## Roadmap
- [x] Phase 1: Base System, Roles, Auth, and User Management
- [ ] Phase 2: School, Term, and Class Management
- [ ] Phase 3: Session Reporting Cycle
- [ ] Phase 4: Payroll Calculation, Integration, and Defense

## License
This project is developed for educational purposes as part of Maktab Sharif Bootcamp 141.
