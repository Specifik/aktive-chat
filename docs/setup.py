#!/usr/bin/env python
"""
Setup script for the Aktive Chat project.
This script helps set up the development environment and create necessary files.
"""

import os
import sys
import uuid
import getpass
import subprocess
from pathlib import Path

def create_env_file():
    """Create the .env file with the necessary environment variables"""
    env_file = Path('.env')
    
    if env_file.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ").lower() == 'y'
        if not overwrite:
            print("Skipping .env file creation.")
            return
    
    # Generate a secret key
    SECRET_KEY = str(uuid.uuid4())
    
    # Get API keys
    print("\n== API Keys ==")
    print("Please enter your API keys (press Enter to skip):")
    
    google_credentials_path = input("Path to Google Cloud credentials file (or press Enter to skip): ")
    elevenlabs_api_key = input("ElevenLabs API Key: ")
    deepl_api_key = input("DeepL API Key (optional): ")
    
    # Create the .env content
    env_content = f"""# Django Settings
SECRET_KEY={SECRET_KEY}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
# Uncomment the line below to use PostgreSQL
# DATABASE_URL=postgres://user:password@localhost:5432/aktive_chat

# API Keys
"""

    if google_credentials_path:
        if os.path.exists(google_credentials_path):
            env_content += f"GOOGLE_APPLICATION_CREDENTIALS={google_credentials_path}\n"
        else:
            print(f"Warning: The file {google_credentials_path} doesn't exist. Skipping Google credentials setting.")
    
    if elevenlabs_api_key:
        env_content += f"ELEVENLABS_API_KEY={elevenlabs_api_key}\n"
    
    if deepl_api_key:
        env_content += f"DEEPL_API_KEY={deepl_api_key}\n"
        env_content += "DEEPL_FREE_API=true\n"
    
    # Add Whisper settings
    env_content += """
# Whisper Settings
WHISPER_MODEL_SIZE=small  # Options: tiny, base, small, medium, large

# Site Settings
SITE_DOMAIN=localhost:8000
"""

    # Write the file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f".env file created at {env_file.absolute()}")

def create_directories():
    """Create necessary directories"""
    directories = [
        'media',
        'media/translation_audio',
        'static/css',
        'static/js',
        'static/images',
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_test_audio():
    """Create a simple text file instructing user to add a test audio file"""
    test_audio_path = Path('test_audio.txt')
    content = """
This is a placeholder for a test audio file.

For testing the speech recognition functionality, please add an audio file named 'test_audio.mp3' 
or 'test_audio.wav' in this directory.

You can record a simple phrase like:
"Hello, this is a test of the speech recognition system."

Use a common audio format such as MP3 or WAV.
"""
    
    with open(test_audio_path, 'w') as f:
        f.write(content)
    
    print(f"Created test audio instructions at {test_audio_path}")

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("\nInstalling dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully!")
        
        # Special handling for Faster Whisper
        try:
            print("\nInstalling Faster Whisper...")
            subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
            print("Faster Whisper installed successfully!")
        except subprocess.CalledProcessError:
            print("Error installing Faster Whisper. You might need to install it manually.")
            print("pip install faster-whisper")
    
    except subprocess.CalledProcessError:
        print("Error installing dependencies. Please run:")
        print("pip install -r requirements.txt")

def initialize_database():
    """Initialize the database"""
    try:
        print("\nInitializing database...")
        subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("Database initialized successfully!")
    
    except subprocess.CalledProcessError:
        print("Error initializing database. Please run:")
        print("python manage.py makemigrations")
        print("python manage.py migrate")

def create_superuser():
    """Create a superuser"""
    print("\n== Create Superuser ==")
    create = input("Do you want to create a superuser now? (y/n): ").lower() == 'y'
    
    if create:
        try:
            subprocess.run([sys.executable, "manage.py", "createsuperuser"], check=False)
        except Exception as e:
            print(f"Error creating superuser: {e}")
            print("You can create one later with:")
            print("python manage.py createsuperuser")

def main():
    """Main setup function"""
    print("=" * 50)
    print("Aktive Chat - Setup Script")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Create test audio instructions
    create_test_audio()
    
    # Install dependencies
    install_dependencies()
    
    # Initialize database
    initialize_database()
    
    # Create superuser
    create_superuser()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run the development server:")
    print("   python manage.py runserver")
    print("2. Access the admin interface at http://localhost:8000/admin/")
    print("3. Visit the application at http://localhost:8000/")
    print("\nTo test individual components:")
    print("- Google Translate: python test_translate.py")
    print("- ElevenLabs TTS: python test_tts.py")
    print("- Faster Whisper: python test_whisper.py")
    print("- QR Code Generation: python test_qrcode.py")
    print("\nEnjoy building your speech translation app!")

if __name__ == "__main__":
    main()