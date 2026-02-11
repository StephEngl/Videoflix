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
