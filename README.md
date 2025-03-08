# Aktive Chat - Real-time Speech Translation Platform

Aktive Chat is a web application for real-time speech translation with customizable subtitles, built on Django. The application allows users to speak in one language and have their speech translated into another language in real-time, with both text and voice output options.

## 🌟 Features

- **Real-time Speech Recognition**: Captures speech input and converts it to text using Faster Whisper
- **Machine Translation**: Translates text between multiple languages using Google Translate or DeepL
- **Voice Synthesis**: Converts translations to speech using ElevenLabs voices
- **Live Subtitles**: Displays translations as customizable subtitles
- **Subtitle Sharing**: Generate QR codes for others to view translations on their devices
- **Font Customization**: Change subtitle appearance to fit your needs
- **Multiple Language Support**: Works with many languages for both input and output
- **User Account System**: Manage settings, history, and preferences
- **Usage Tracking**: Track your API usage for each service

## 🏗️ Architecture

The system uses a multi-service architecture:

1. **Django Web Application**: Core server handling authentication, API endpoints, database, and view rendering
2. **WebSockets**: Real-time communication using Django Channels
3. **Faster Whisper**: High-performance speech-to-text conversion
4. **Google Translate/DeepL**: Text translation between languages
5. **ElevenLabs API**: High-quality voice generation for the translated text

## 🔧 Prerequisites

- Python 3.9+
- Django 5.0+
- PostgreSQL (recommended for production)
- CUDA-compatible GPU (optional but recommended for Faster Whisper)
- API keys for:
  - Google Cloud (Translation API)
  - ElevenLabs
  - DeepL (optional alternative to Google Translate)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aktive-chat.git
   cd aktive-chat
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Faster Whisper:
   ```bash
   pip install faster-whisper
   ```

5. Create a `.env` file with your API keys:
   ```
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # Google Cloud Translation
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
   # or
   GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}
   
   # ElevenLabs
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   
   # DeepL (optional)
   DEEPL_API_KEY=your_deepl_api_key
   DEEPL_FREE_API=true  # or false if using Pro account
   
   # Database (for production)
   # DATABASE_URL=postgres://user:password@localhost:5432/aktive_chat
   ```

6. Initialize the database:
   ```bash
   python manage.py migrate
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

## 📱 Usage

### Speech Translation

1. Log in to your account
2. Go to the Translator page
3. Select your target language
4. Click "Start Recording" and speak
5. Your speech will be transcribed, translated, and optionally spoken in the target language
6. Translations will also appear as subtitles

### Subtitle Sharing

1. Create a new shared session
2. Configure session settings (language options, password protection, etc.)
3. Share the provided URL or QR code with your audience
4. Audience members can scan the QR code to view subtitles on their devices
5. If enabled, viewers can select their preferred language and customize subtitle appearance

## 🔄 API Service Integration

### Faster Whisper

The application uses Faster Whisper for high-performance speech recognition:

```python
from faster_whisper import WhisperModel

# Initialize model (optimized for your hardware)
model_size = "small"  # Options: tiny, base, small, medium, large
model = WhisperModel(model_size, device="cuda", compute_type="float16")

# Perform transcription
segments, info = model.transcribe("audio.wav", beam_size=5, vad_filter=True)

# Process results
for segment in segments:
    print(segment.text)
```

### Google Translate

Text translation is handled by Google Cloud Translation API:

```python
from google.cloud import translate_v2 as translate

client = translate.Client()
result = client.translate("Hello world", target_language="es")
translated_text = result["translatedText"]
```

### ElevenLabs

Voice synthesis is done using ElevenLabs API:

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="your_api_key")
audio = client.generate(
    text="Hello world",
    voice="voice_id_here",  # Optional
    model="eleven_multilingual_v2"
)
```

## 📐 Project Structure

```
aktive_chat/                 # Main project directory
│
├── accounts/                # User accounts app
├── api/                     # API services
│   ├── services/            # Third-party service integrations
│   │   ├── faster_whisper_service.py
│   │   ├── google_translate_service.py
│   │   └── elevenlabs_service.py
│   └── consumers.py         # WebSocket consumers
│
├── core/                    # Core application functionality
│   ├── models.py            # Database models
│   ├── views.py             # View controllers
│   └── utils/               # Utility functions
│       └── qr_code.py       # QR code generation
│
├── static/                  # Static files
│   ├── css/
│   └── js/
│
├── templates/               # HTML templates
│   ├── account/             # Account management templates
│   └── core/                # Core app templates
│       └── subtitle_viewer.html  # Subtitle viewer page
│
└── aktive_chat/             # Project settings
    ├── asgi.py              # ASGI config for WebSockets
    ├── settings.py          # Project settings
    └── urls.py              # URL routing
```

## 🧪 Testing

Run tests with:

```bash
python manage.py test
```

## 🛣️ Roadmap

- [ ] Add speech language auto-detection
- [ ] Support for custom ElevenLabs voice creation
- [ ] Mobile app for better on-the-go use
- [ ] Offline mode with downloaded models
- [ ] Multi-speaker differentiation
- [ ] Improved subtitle formatting options
- [ ] Video subtitling capabilities

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **[Speech2Speech Translation](https://github.com/ALucek/speech2speech-translation)** - Original inspiration and implementation by ALucek
- **[Faster Whisper](https://github.com/SYSTRAN/faster-whisper)** - High-performance implementation of OpenAI's Whisper model
- **[ElevenLabs](https://elevenlabs.io/)** - State-of-the-art voice synthesis
- **[Django](https://www.djangoproject.com/)** - The web framework used
- **[Django Channels](https://channels.readthedocs.io/)** - WebSocket support for Django

## 📞 Support

If you encounter any issues or have questions, please file an issue on the GitHub repository or contact us at:

- Email: [your-email@example.com](mailto:your-email@example.com)
- Twitter: [@yourusername](https://twitter.com/yourusername)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##
