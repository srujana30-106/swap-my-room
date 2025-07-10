# Hostel Room Swap Platform

A Flask-based web application for college students to swap hostel rooms with real-time notifications using SocketIO.

## Features

- **User Registration & Authentication** with college ID validation
- **Room Preference Posting** - Post available and needed rooms
- **Real-time Notifications** - Live updates when new preferences are posted
- **Room Request System** - Send and manage swap requests
- **Email Integration** - Password reset functionality
- **Floor-based Filtering** - Filter rooms by floor numbers
- **WhatsApp Integration** - Direct contact through WhatsApp links

##  Project Structure

```
swap-my-room/
├── app.py              # Main Flask application
├── models.py           # Database models (User, RoomPreference)
├── config.py           # Application configuration
├── database.py         # Database initialization script
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html      # Base template with SocketIO
│   ├── dashboard.html # Main dashboard
│   ├── login.html     # Login page
│   ├── register.html  # Registration page
│   └── ...
└── static/            # CSS and static files
```

##  Setup Instructions

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Security
SECRET_KEY=your-super-secret-key-here

# PostgreSQL Database
DATABASE_URL=postgresql://username:password@host:port/database_name

# Email Configuration (Gmail)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 2. Database Configuration

For **local development**, you have options:

**Option A: Local PostgreSQL**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/swap_room_db
```

**Option B: Railway PostgreSQL**
```bash
# Get this from your Railway project dashboard
DATABASE_URL=postgresql://username:password@containers-us-west-xxx.railway.app:6543/railway
```

### 3. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd swap-my-room

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python database.py
```

### 4. Running the Application

```bash
# Start the Flask-SocketIO server
python app.py
```

The application will be available at `http://localhost:5000`

##  Real-time Features

The application uses **Flask-SocketIO** for real-time features:

- **Live Connection Status** - Users see when they're connected
- **Instant Notifications** - New room preferences appear immediately
- **Broadcast Updates** - All connected users receive updates

### SocketIO Events:

- `connect` - User connects to the server
- `disconnect` - User disconnects
- `new_preference` - Emitted when posting new room preference
- `preference_update` - Broadcasted to all users for live updates

## Database Models

### User Model
```python
- id (Primary Key)
- college_id (Unique, 8 characters)
- password (Hashed)
- email (Unique)

```

### RoomPreference Model
```python
- id (Primary Key)
- user_id (Foreign Key to User)
- available (Current room number)
- needed (Desired room number)
- selected (Boolean - if accepted)
- accepted_by (Foreign Key to User)
- created_at (Timestamp)
```

##  Configuration

### Email Setup (Gmail)
1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Generate an "App Password"
4. Use the app password in `MAIL_PASSWORD`

### Database Setup
The application now uses a modular structure:
- **models.py** - Contains all database models
- **database.py** - Creates tables without dropping existing ones
- Supports PostgreSQL only (no SQLite fallback)

##  Deployment

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Railway will automatically detect and deploy the Flask app

### Environment Variables for Production:
```bash
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://...  # Railway provides this
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-app-password
```

##  Security Features

- **Input Validation** - College ID format validation (8 alphanumeric)
- **Duplicate Prevention** - Prevents duplicate registrations
- **Session Management** - Secure user sessions
- **Password Reset** - Secure token-based password reset
- **CSRF Protection** - Built-in Flask protection

##  Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python -c "from app import app; from models import db; 
with app.app_context(): db.create_all(); print('Database connected!')"
```

### SocketIO Connection Issues
- Check if port 5000 is available
- Ensure firewall allows WebSocket connections
- Check browser console for SocketIO errors

### Common Issues
1. **"No such table" error** - Run `python database.py`
2. **SocketIO not connecting** - Check CORS settings
3. **Email not sending** - Verify Gmail app password

##  License

This project is licensed under the MIT License.

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note:** This application is designed for college hostel room swapping. Make sure to comply with your institution's housing policies.

---
