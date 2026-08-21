# Academy Management System

## Overview

Backend API for managing an educational institute, developed as the final project for Python Bootcamp 141. This system handles class reporting and teacher payroll calculations, featuring advanced architectural patterns such as idempotent cascade soft-deletion, custom email-based authentication, and strict role-based access control.

## Tech Stack

- **Language:** Python 3.14
- **Framework:** Django 6.0 & Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** SimpleJWT
- **API Docs:** drf-yasg (Swagger)
- **Type Checking:** MyPy (strict mode)

## Key Architectural Decisions & Features

### 1. Advanced Soft-Deletion System

Implemented a custom soft-deletion mechanism using `SoftDeleteMixin` and custom managers/querysets:

- Explicitly set `base_manager_name = "all_objects"` to handle reverse relations correctly.
- Soft deletion is idempotent and does not overwrite the original `updated_by` audit trail when an already-deleted object is deleted again.
- Cascade soft deletion is configurable through `SoftDeletionOptions`.
- `all_objects` provides access to soft-deleted records.

### 2. Custom User & Authentication Architecture

Replaced Django's default username-based authentication with an email-based system:

- **Email as `USERNAME_FIELD`**
- Custom user managers supporting soft deletion
- JWT authentication
- Custom management command for creating users
- No public user registration

### 3. Role-Based Access Control (RBAC)

Implemented role-based permissions tailored to the project requirements:

- `IsRoleAdmin`
- `IsEducationOfficerOrAdmin`
- `IsFinanceOfficerOrAdmin`
- `IsTeacherOrAdmin`
- `IsTeacherOrEducationOfficerOrAdmin`

### 4. CLI Management Command

Created the `create_user` management command for creating users with a specific role.

Example:

```bash
python manage.py create_user -e admin@example.com -p securepassword -r ADM
```

## Project Structure

- `account/`: User, TeacherProfile, custom managers and permissions.
- `education/`: School, Semester, Course, Session, TeacherCourse and related educational APIs.
- `finance/`: Wage-related models and operations.
- `system/`: Base models, soft-deletion managers/querysets, renderers and validators.

# Usage

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd academy-management-system
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and configure the required database/environment variables in `.env` or `settings.py`.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create the first Admin user

```bash
python manage.py create_user -e admin@example.com -p securepassword -r ADM
```

### 7. Run the development server

```bash
python manage.py runserver
```

### 8. Authentication

Obtain a JWT token via:

```text
POST /api/v1/token/
```

Use the returned access token for authenticated requests:

```text
Authorization: Bearer <access_token>
```

### 9. API Documentation

Navigate to:

```text
http://127.0.0.1:8000/swagger/
```

to access the interactive Swagger UI.

### 10. Run Tests

Run the complete test suite:

```bash
python manage.py test
```

Run tests with coverage:

```bash
coverage run manage.py test
coverage report
```

## **Phase 2 — Education Management**

Phase 2 focuses on managing the educational structure of the system.

### Implemented

- **School API**
  - Create, retrieve, update and list schools
  - Soft-deletion support

- **School Contact Person API**
  - Manage school contact persons
  - Soft-deletion support

- **Semester API**
  - Manage semesters associated with schools
  - Start/end dates
  - Summer semester flag

- **Course API**
  - Manage courses associated with semesters
  - Course level
  - Session length
  - Course start/end dates
  - Serial number generation
  - Filtering and search

- **Session API**
  - Manage course sessions
  - Session date and start/end time
  - Serial number generation

- **Teacher-Course API**
  - Assign teachers to courses
  - Store assignment start/end dates
  - Support multiple teachers for the same course over different periods

- **Teacher Schedule API**
  - Provide teachers with their assigned course schedule

### Tests

Phase 2 functionality is covered by automated tests, including:

- Endpoint permissions and supported methods
- Soft-deleted objects being excluded from the default manager
- Access to deleted objects through `all_objects`
- School and school contact person endpoints
- Semester endpoint
- Course endpoint
- Session endpoint
- Teacher-course endpoint
- Multiple teacher assignments for a single course
- Teacher schedule endpoint
- Course filtering and search

Coverage reports are updated as part of the development workflow.

## **Phase 3 — Session Reporting Cycle**

Phase 3 covers session reporting, moderation, and teacher-facing reporting analytics.

### Implemented

- **Report API**
  - Teachers submit reports for their assigned sessions
  - Validation prevents duplicate reports per session
  - Late submission detection with delay duration (48-hour rule)
  - Teachers can update rejected reports for resubmission
  - Serial-numbered report records with role-aware status visibility

- **Review & Audit API**
  - Education Officers and Admins approve or reject reports
  - Rejections require a non-blank reason
  - Report history logs each approval/rejection/comment action
  - Bulk approval endpoint for multiple pending reports

- **Teacher Dashboard API**
  - Teacher schedule endpoint for course/session assignment visibility
  - Teacher report statistics endpoint for submitted, pending, rejected, and approved counts
  - Configurable time-window query parameters

- **Reporting Filters and Permissions**
  - Role-based endpoints for Teacher, Education Officer, and Admin
  - Filtering and searching by school, course, teacher name, and session date
  - Education Officer queue returns only non-finalized reports

### Tests

Phase 3 is covered by automated tests, including:

- Report permission matrix and unsupported method constraints
- Teacher ownership, session ownership, and duplicate-report protection
- Delay calculations and late-submission behavior
- Report approval/rejection flow and idempotency guards
- Bulk approval validation and history patch rules
- Dashboard statistics and filtering behavior

## Development Status

- **Phase 1:** Completed
- **Phase 2:** Completed
- **Phase 3:** Completed
- **Phase 4:** Pending
