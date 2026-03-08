# Jiak99 Planner - Deployment Guide

## Prerequisites

- Python 3.11 or higher
- Git
- Windows/Linux/Mac OS

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Jiak99_App01
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# Create database and tables
python manage.py migrate

# Generate tour time slots (10am-8pm, 1.5h tours)
python manage.py generate_tour_slots
```

### 4. Create Admin Account

```bash
python manage.py createsuperuser
```

Follow the prompts to create your manager account:
- Username: (your choice)
- Email: (optional)
- Password: (secure password)

### 5. Run the Application

```bash
python manage.py runserver
```

Access the application at: **http://localhost:8000**

### 6. Initial Setup

1. Log in at http://localhost:8000/admin/ with your superuser credentials
2. Add Guides: Admin → Guides → Add guide
3. Add Restaurant Staff: Admin → Kitchen and serving staff → Add
4. Start scheduling: Navigate to Schedule Management

## Default URLs

- **Main Dashboard:** http://localhost:8000/main/
- **Schedule Management:** http://localhost:8000/schedule/
- **Tour Guide Scheduler:** http://localhost:8000/schedule/guide/
- **Restaurant Staff Scheduler:** http://localhost:8000/schedule/restaurant/
- **Admin Panel:** http://localhost:8000/admin/

## Quick Start Data Setup

### Add Tour Guides:
1. Go to Admin → Authentication and Authorization → Users → Add user
2. Create user account
3. In the user edit page, scroll to "Guide Profile" section
4. Select guide type (Full-time, Part-time Morning, Part-time Afternoon)
5. Save

### Add Restaurant Staff:
1. Go to Admin → Kitchen and serving staff → Kitchen and serving staff → Add
2. Select existing user or create new one
3. Choose staff type (Kitchen or Serving)
4. Save

### Create Schedule:
1. Go to http://localhost:8000/schedule/
2. Click "Open Schedule Manager" for Tour Guides or Restaurant Staff
3. Select a date
4. Click "Auto-Assign" to generate optimized schedules
5. Review and adjust as needed
6. Click "Publish" to make schedule visible to staff

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
python manage.py runserver 8001
```

### Database Errors
```bash
# Reset database (WARNING: deletes all data)
rm db.sqlite3
python manage.py migrate
python manage.py generate_tour_slots
python manage.py createsuperuser
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

## Notes

- This is a manager-only tool. A separate app will be built for guides and staff.
- The database (db.sqlite3) contains all schedule data. Back it up regularly.
- For multi-manager deployment, consider using a centralized server (see README.md)

## Support

For issues or questions, contact your system administrator.
