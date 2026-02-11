# Videoflix Django Project

Videoflix is a comprehensive video streaming platform that provides seamless video upload, processing, and streaming capabilities. Built with Django and powered by FFmpeg, Videoflix offers an innovative solution for video content management with adaptive streaming technology. Key features include automatic HLS video conversion in multiple resolutions, secure user authentication with JWT tokens, thumbnail generation, and a robust REST API for modern web applications.

## ✨ Features

📹 **Video Upload & Processing** - Upload videos in various formats with automatic conversion  
🎬 **HLS Streaming** - Adaptive streaming with multiple resolutions (480p, 720p, 1080p)  
🖼️ **Thumbnail Generation** - Automatic thumbnail creation from video content  
🔐 **Authentication** - Secure user registration, email activation, and JWT token management  
🎭 **Video Categories** - Organize videos with category classification  
🛡️ **User Permissions** - Secure access control and user management  
📱 **REST API** - Comprehensive API for frontend integration  
🐳 **Docker Support** - Containerized deployment with Docker Compose

## 🛠️ Tech Stack

- **Python** - Core programming language
- **Django** - Web framework
- **Django REST Framework** - API development
- **FFmpeg** - Video processing and conversion
- **Redis** - Task queue management
- **Django-RQ** - Background job processing
- **PostgreSQL** - Production database
- **Docker** - Containerization and deployment
- **JWT** - Token-based authentication

## 🚀 Getting Started

Follow these steps to set up and run the project using Docker.

### ⚙️ Prerequisites

- Docker & Docker Compose
- Git

### 📦 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/videoflix.git
   cd videoflix
   ```

2. **Set up environment variables**
   Copy the .env.template to .env and configure your settings:
   ```bash
   cp .env.template .env
   ```
   Update the variables in your .env file!

3. **Build and start the containers**
   ```bash
   # For development
   docker-compose -f docker-compose.yml -f docker-compose.development-override.yml up --build

   # For production
   docker-compose up --build
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api/schema/swagger-ui/

### 🐳 Docker Commands
Development Environment:
   ```bash
   # Start development environment
   docker-compose -f docker-compose.yml -f docker-compose.development-override.yml up -d

   # View logs
   docker-compose logs -f web

   # Execute commands in container
   docker-compose exec web python manage.py shell

   # Stop containers
   docker-compose down
   ```

Production Environment:
```bash
# Start production environment
docker-compose up -d

# Monitor containers
docker-compose ps

# Restart services
docker-compose restart

# Update and rebuild
docker-compose up --build -d
```
Database Management:
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access database
docker-compose exec db psql -U videoflix_user -d videoflix_db
```

## 📚 API Documentation

This project includes automatically generated API documentation with Swagger UI and Redoc.

**The OpenAPI schema is available at:**
- `/api/schema/`

**Interactive Swagger UI can be accessed at:**
- `/api/schema/swagger-ui/`  
  Use this web interface to explore and test the API endpoints easily.

**Alternative documentation with Redoc is available at:**
- `/api/schema/redoc/`

These endpoints are integrated using drf-spectacular and configured in the Django URL patterns for convenient API exploration during development and testing.

## 📁 Project Structure

- [`core`](core) – Project configuration, global settings, and root URLs
- [`app_auth`](app_auth) – Handles user authentication, registration, email activation, and JWT token management
- [`app_video`](app_video) – Manages video upload, HLS conversion, thumbnail generation, and streaming
- [`media`](media) – Stores uploaded videos, processed HLS files, and thumbnails
- [`static`](static) – Static files for admin interface and API documentation

## 🔗 API Endpoints

### 🛡️ Authentication
- `POST /api/auth/register/` – Register new user account
- `GET /api/auth/activate/{uidb64}/{token}/` – Activate user account via email
- `POST /api/auth/login/` – User login and JWT token generation
- `POST /api/auth/token/refresh/` – Refresh JWT access token
- `POST /api/auth/logout/` – User logout and token cleanup
- `POST /api/auth/password-reset/` – Request password reset email
- `POST /api/auth/password-reset-confirm/{uidb64}/{token}/` – Confirm password reset

### 📹 Video Management
- `GET /api/videos/` – List all processed videos
- `GET /api/videos/{id}/playlist/{resolution}/` – Get HLS playlist for specific resolution
- `GET /api/videos/{id}/segment/{resolution}/{segment}/` – Get HLS video segment

## 🎯 How It Works

1. **Video Upload**: Users upload videos through the admin interface or API
2. **Background Processing**: Django-RQ handles video conversion tasks asynchronously
3. **HLS Conversion**: FFmpeg converts videos to multiple resolutions (480p, 720p, 1080p)
4. **Thumbnail Generation**: Automatic thumbnail creation from video frames
5. **Master Playlist**: Generation of HLS master playlist for adaptive streaming
6. **File Cleanup**: Automatic cleanup of video files when videos are deleted
7. **Streaming**: Users can stream videos through HLS-compatible players

## 🔒 Security Information

- **Secret Key**: Never share your Django SECRET_KEY. Use environment variables for production.
- **Debug Mode**: Set `DEBUG = False` in production environments.
- **Allowed Hosts**: Update `ALLOWED_HOSTS` in settings.py for your deployment domain.
- **Email Configuration**: Use secure SMTP settings and app passwords.
- **Database**: Use strong credentials and restrict database access.
- **HTTPS**: Always use HTTPS in production with proper SSL certificates.
- **Admin Panel**: Restrict admin access and use strong passwords.
- **Environment Files**: Ensure .env files are not committed to version control.
- **User Enumeration**: Registration endpoint prevents email enumeration attacks.
- **File Security**: Uploaded files are validated and stored securely.

## 🧪 Running Tests

Run the comprehensive test suite to ensure everything works correctly:

```bash
# Run tests in Docker container
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test app_video
docker-compose exec web python manage.py test app_auth

# Run with coverage analysis
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

## 🔧 Management Commands

The project includes custom management commands for maintenance:

```bash
# Clean up inactive users (implement as needed)
docker-compose exec web python manage.py cleanup_inactive_users

# Send test emails
docker-compose exec web python manage.py send_test_email
```

## 🎬 Video Processing Pipeline

1. **Upload**: Video uploaded to `media/videos/original/`
2. **Signal Trigger**: Post-save signal starts background processing
3. **HLS Conversion**: Multiple resolution conversions run in parallel
4. **Thumbnail Creation**: Thumbnail generated from video frame at 1 second
5. **Master Playlist**: Combined playlist created for all resolutions
6. **Status Update**: Video marked as processed and available for streaming

## 👥 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/videoflix.git`
3. Create a new branch: `git checkout -b feature/your-feature`
4. Make your changes and test thoroughly
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to your branch: `git push origin feature/your-feature`
7. Open a pull request

Please ensure your code follows Django best practices and includes appropriate tests.

## 🔧 Configuration

For more details about project configuration, see:
- [core/settings.py](core/settings.py) - Django settings and configurations
- [docker-compose.yml](docker-compose.yml) - Production Docker configuration
- [docker-compose.development-override.yml](docker-compose.development-override.yml) - Development overrides
- [requirements.txt](requirements.txt) - Python dependencies
- [backend.Dockerfile](backend.Dockerfile) - Docker image configuration

## 📊 Monitoring & Maintenance

**Container Health:**
```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Check logs
docker-compose logs -f web
docker-compose logs -f redis
docker-compose logs -f db
```

**Database Backup:**
```bash
# Create database backup
docker-compose exec db pg_dump -U videoflix_user videoflix_db > backup.sql

# Restore database backup
docker-compose exec -T db psql -U videoflix_user -d videoflix_db < backup.sql
```

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
