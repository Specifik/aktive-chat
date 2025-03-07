let isListening = false;
let recognition;
let inputLanguage = 'de';
let outputLanguage = 'en';
let originalText = '';
let translatedText = '';

const listenButton = document.getElementById('listen-button');
const inputLanguageSelect = document.getElementById('input-language');
const outputLanguageSelect = document.getElementById('output-language');
const clearButton = document.getElementById('clear-button');
const swapButton = document.getElementById('swap-button');
const originalTextElement = document.getElementById('original-text');
const translatedTextElement = document.getElementById('translated-text');
const fontSizeSlider = document.getElementById('font-size');
const fontSizeValue = document.getElementById('font-size-value');
const fontUpload = document.getElementById('font-upload');
const liveTextElement = document.getElementById('live-text');

inputLanguageSelect.addEventListener('change', (e) => inputLanguage = e.target.value);
outputLanguageSelect.addEventListener('change', (e) => outputLanguage = e.target.value);

fontSizeSlider.addEventListener('input', (e) => {
    fontSizeValue.textContent = e.target.value;
    liveTextElement.style.fontSize = `${e.target.value}px`;
});

clearButton.addEventListener('click', () => {
    originalText = '';
    translatedText = '';
    originalTextElement.textContent = 'Speak to see text here...';
    translatedTextElement.textContent = 'Translation will appear here...';
});

swapButton.addEventListener('click', () => {
    [inputLanguage, outputLanguage] = [outputLanguage, inputLanguage];
    [originalText, translatedText] = [translatedText, originalText];
    originalTextElement.textContent = originalText;
    translatedTextElement.textContent = translatedText;
});

if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        originalText += finalTranscript || interimTranscript;
        originalTextElement.textContent = originalText;

        // Translate text (simulated translation for now)
        translatedText = `${finalTranscript} (translated from ${inputLanguage} to ${outputLanguage})`;
        translatedTextElement.textContent = translatedText;
    }
}
