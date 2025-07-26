# OT Tracker Application - AI Coding Instructions

## Architecture Overview
This is a Flask-based overtime tracking and personal finance management application with SQLite database. The app uses a multi-user architecture with session-based authentication and optional Google OAuth integration.

## Core Components

### Database Schema
- **users**: Multi-tenant user management with Google OAuth support
- **ot_records**: Overtime tracking with complex calculation rules
- **income_expense**: Personal finance tracking with JSON item storage
- **holidays**: User-specific holiday management affecting OT calculations
- **work_settings**: Per-user configurable work schedules and OT rates

### Key Business Logic
- **OT Calculation Engine** (`calculate_ot` functions): Complex multi-tier system supporting normal OT, Saturday premium rates, weekday special rates, and night shift multipliers
- **Template Inheritance**: Uses `templates/base.html` for consistent Bootstrap 5 navigation across all pages
- **Multi-user Isolation**: All database queries filter by `session['user_id']`

## Development Patterns

### Template Structure
```
base.html - Bootstrap 5 navigation with dropdown menus
├── index.html - OT tracking (main page)
├── income_expense.html - Financial management
├── holidays.html - Holiday management
├── settings.html - User preferences
└── login.html/signup.html - Authentication
```

### Route Patterns
- All main routes require `@login_required` decorator
- Use `session['user_id']` for data isolation
- POST forms redirect to prevent refresh issues
- Export routes generate CSV downloads with UTF-8-BOM encoding

### Database Patterns
- **Schema Evolution**: Uses try/except blocks for ALTER TABLE statements to handle existing databases
- **Connection Management**: `get_db_connection()` returns `sqlite3.Row` factory for dict-like access
- **Multi-tenant Queries**: Always include `WHERE user_id = ?` for data isolation

## Critical Workflows

### OT Calculation Workflow
1. Parse datetime strings in `%Y-%m-%dT%H:%M` format
2. Query user's work_settings for custom schedules
3. Apply break deductions based on holiday status
4. Calculate using priority order: night OT > weekend OT > weekday special > normal OT

### Template Update Workflow
When adding pages:
1. Extend `base.html` 
2. Set appropriate `{% block title %}`
3. Wrap content in `{% block content %}`
4. Add navigation items to base.html if needed

### Database Migration Pattern
```python
try:
    conn.execute('ALTER TABLE table_name ADD COLUMN new_column TEXT DEFAULT "value"')
except sqlite3.OperationalError:
    pass  # Column exists already
```

## Integration Points

### Google OAuth (Optional)
- Controlled by `GOOGLE_OAUTH_AVAILABLE` flag based on requests library
- Creates users with `password_hash = 'google_oauth'`
- Stores profile info in session variables

### CSV Import/Export
- Uses pandas with `encoding='utf-8-sig'` for Excel compatibility
- Template downloads available at `/export-template` and `/export-ot-template`
- Supports both monthly and yearly exports

## Project-Specific Conventions

### Thai Localization
- All UI text in Thai language
- Date formats follow Thai conventions
- Flash messages use Thai text with appropriate tone

### Form Handling
- Bootstrap 5 form styling throughout
- Datetime inputs use HTML5 `datetime-local` type
- Select dropdowns trigger immediate form submission for filtering

### Error Handling
- Flash messages for user feedback: `flash('message', 'success'|'error')`
- Form validation happens server-side with redirect on error
- JavaScript confirmation dialogs for destructive actions

## Configuration Dependencies
- Requires `config.py` with `Config` class containing SECRET_KEY and DATABASE_FILE
- Optional Google OAuth requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Database initialization via `init_db()` creates tables and handles migrations

When modifying this codebase, maintain the multi-user isolation, preserve the OT calculation logic complexity, and ensure all new pages follow the base template pattern for consistent navigation.
