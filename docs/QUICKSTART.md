# Quick Start Guide for Aktive Chat

This guide will help you quickly set up and run the Aktive Chat speech translation application.

## Prerequisites

- Python 3.9+ installed
- A Google Cloud account with the Translation API enabled
- An ElevenLabs account with API access
- Optional: A DeepL API key for alternative translation

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/aktive-chat.git
cd aktive-chat
```

## Step 2: Run the Setup Script

The setup script will guide you through the installation process:

```bash
python setup.py
```

This script will:
- Create necessary directories
- Set up your environment variables in a `.env` file
- Install dependencies
- Initialize the database
- Create a superuser account

## Step 3: Start the Development Server

```bash
python manage.py runserver
```

## Step 4: Access the Application

- Admin interface: http://localhost:8000/admin/
- Main application: http://localhost:8000/

## Testing Individual Components

To make sure everything is working correctly, you can run the test scripts:

```bash
# Test Google Translate integration
python test_translate.py

# Test ElevenLabs text-to-speech
python test_tts.py

# Test Faster Whisper speech recognition
python test_whisper.py

# Test QR code generation
python test_qrcode.py
```

## Using the Translator

1. Log in to your account
2. Navigate to the Translator page
3. Select your target language
4. Click "Start Recording" and speak into your microphone
5. Your speech will be transcribed, translated, and spoken in the target language

## Sharing Subtitles

1. Create a new subtitle sharing session
2. Configure session settings (language options, expiration, etc.)
3. Share the generated QR code with your audience
4. Audience members can scan the QR code to view live translations on their devices

## Troubleshooting

If you encounter any issues:

1. **Database migrations**: Make sure all migrations are applied
   ```bash
   python manage.py migrate
   ```

2. **API keys**: Verify your API keys in the `.env` file

3. **WebSocket issues**: Check that Channels is properly installed and configured

4. **Faster Whisper installation**: If you have issues with Faster Whisper, you may need to install additional dependencies depending on your platform
   ```bash
   # For CUDA support (NVIDIA GPUs)
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   pip install faster-whisper
   ```

## Next Steps

- Customize subtitle appearance and positioning
- Add more languages 
- Implement custom voice creation
- Integrate with video platforms