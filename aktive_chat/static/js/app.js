// Global variables
let isListening = false;
let recognition;
let inputLanguage = 'de';
let outputLanguage = 'en';
let originalText = '';
let translatedText = '';

// Main control buttons
const listenButton = document.getElementById('listen-button');
const testAudioButton = document.getElementById('test-audio-button');
const outputLanguageSelect = document.getElementById('output-language');
const originalTextElement = document.getElementById('original-text');
const translatedTextElement = document.getElementById('translated-text');
const fontSizeSlider = document.getElementById('font-size');
const fontSizeValue = document.getElementById('font-size-value');
const fontUpload = document.getElementById('font-upload');
const liveTextElement = document.getElementById('live-text');

// Audio device selectors
const microphoneSelect = document.getElementById('microphone-select');
const speakerSelect = document.getElementById('speaker-select');
const headphonesSelect = document.getElementById('headphones-select');

// Volume controls
const micVolumeSlider = document.getElementById('mic-volume');
const micVolumeValue = document.getElementById('mic-volume-value');
const speakerVolumeSlider = document.getElementById('speaker-volume');
const speakerVolumeValue = document.getElementById('speaker-volume-value');

// Font family selector
const fontFamilySelect = document.getElementById('font-family');

// Audio test elements
const audioTestModal = document.querySelector('.audio-test-modal');
const micMeterFill = document.getElementById('audio-meter-microphone');
const playTestSoundButton = document.getElementById('play-test-sound');
const closeAudioTestButton = document.getElementById('close-audio-test');

// Audio test functionality
let audioContext;
let analyser;
let microphone;
let testAudioStream;
let testAudioInterval;

// Language buttons
const languageButtons = document.querySelectorAll('.language-button');

// Language name mapping
const languageNames = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'de': 'German'
};

// Language button functionality
languageButtons.forEach(button => {
    button.addEventListener('click', () => {
        languageButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        inputLanguage = button.dataset.lang;
        const languageName = languageNames[inputLanguage] || inputLanguage;
        document.getElementById('original-label').textContent = `Original (${languageName})`;
    });
});

// Recording button functionality
listenButton.addEventListener('click', () => {
    if (!isListening) {
        listenButton.classList.add('recording');
        listenButton.innerHTML = '<i class="fas fa-microphone"></i>Recording...';
        isListening = true;
        startRecording();
    } else {
        listenButton.classList.remove('recording');
        listenButton.innerHTML = '<i class="fas fa-microphone"></i>Start Listening';
        isListening = false;
        stopRecording();
    }
});

// Audio test modal functionality
testAudioButton.addEventListener('click', () => {
    audioTestModal.style.display = 'flex';
    startAudioTest();
});

closeAudioTestButton.addEventListener('click', () => {
    audioTestModal.style.display = 'none';
    stopAudioTest();
});

// Output language selection
outputLanguageSelect.addEventListener('change', (e) => {
    outputLanguage = e.target.value;
    const languageName = languageNames[outputLanguage] || outputLanguage;
    document.getElementById('translated-label').textContent = `Translated (${languageName})`;
});

// Handle volume sliders
micVolumeSlider.addEventListener('input', (e) => {
    const value = e.target.value;
    micVolumeValue.textContent = `${value}%`;
    micVolumeSlider.style.setProperty('--volume-percent', `${value}%`);
    
    // If we have an active audio context, adjust the gain
    if (window.micGainNode) {
        // Convert percentage to gain value (0-2 range, where 1 is normal)
        const gainValue = value / 50; // 50% = gain of 1
        window.micGainNode.gain.value = gainValue;
    }
});

speakerVolumeSlider.addEventListener('input', (e) => {
    const value = e.target.value;
    speakerVolumeValue.textContent = `${value}%`;
    speakerVolumeSlider.style.setProperty('--volume-percent', `${value}%`);
    
    // If we have an active audio context, adjust the gain
    if (window.speakerGainNode) {
        // Convert percentage to gain value (0-2 range, where 1 is normal)
        const gainValue = value / 50; // 50% = gain of 1
        window.speakerGainNode.gain.value = gainValue;
    }
});

// Start audio test
async function startAudioTest() {
    try {
        // Initialize audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        
        // Create gain nodes for volume control
        window.micGainNode = audioContext.createGain();
        window.speakerGainNode = audioContext.createGain();
        
        // Set initial gain values based on sliders
        window.micGainNode.gain.value = micVolumeSlider.value / 50;
        window.speakerGainNode.gain.value = speakerVolumeSlider.value / 50;
        
        // Get microphone stream
        const selectedMicId = microphoneSelect.value;
        const constraints = {
            audio: selectedMicId ? { deviceId: { exact: selectedMicId } } : true
        };
        
        testAudioStream = await navigator.mediaDevices.getUserMedia(constraints);
        microphone = audioContext.createMediaStreamSource(testAudioStream);
        
        // Connect through gain node
        microphone.connect(window.micGainNode);
        window.micGainNode.connect(analyser);
        
        // Start monitoring microphone level
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        testAudioInterval = setInterval(() => {
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate volume level (0-100)
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;
            const volume = Math.min(100, average * 2); // Scale up for better visibility
            
            // Update microphone meter
            micMeterFill.style.width = `${volume}%`;
            
            // Change color based on volume
            if (volume < 30) {
                micMeterFill.style.backgroundColor = '#EF4444'; // Low (red)
            } else if (volume < 70) {
                micMeterFill.style.backgroundColor = '#F59E0B'; // Medium (yellow)
            } else {
                micMeterFill.style.backgroundColor = '#10B981'; // High (green)
            }
        }, 100);
    } catch (error) {
        console.error('Error starting audio test:', error);
    }
}

// Stop audio test
function stopAudioTest() {
    if (testAudioInterval) {
        clearInterval(testAudioInterval);
        testAudioInterval = null;
    }
    
    if (testAudioStream) {
        testAudioStream.getTracks().forEach(track => track.stop());
        testAudioStream = null;
    }
    
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
    }
}

// Play test sound
playTestSoundButton.addEventListener('click', () => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const gainNode = audioContext.createGain();
    
    // Use the speaker volume setting
    gainNode.gain.value = speakerVolumeSlider.value / 100;
    
    // Create a short melody
    const notes = [
        { frequency: 523.25, duration: 0.2 }, // C5
        { frequency: 659.25, duration: 0.2 }, // E5
        { frequency: 783.99, duration: 0.4 }  // G5
    ];
    
    let startTime = audioContext.currentTime;
    
    notes.forEach(note => {
        const oscillator = audioContext.createOscillator();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(note.frequency, startTime);
        
        // Create individual gain node for envelope
        const noteGain = audioContext.createGain();
        noteGain.gain.setValueAtTime(0, startTime);
        noteGain.gain.linearRampToValueAtTime(0.5, startTime + 0.01);
        noteGain.gain.linearRampToValueAtTime(0, startTime + note.duration);
        
        oscillator.connect(noteGain);
        noteGain.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.start(startTime);
        oscillator.stop(startTime + note.duration);
        
        startTime += note.duration;
    });
});

// Audio device handling
async function initializeAudioDevices() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Stop the stream immediately after getting permission
        
        const devices = await navigator.mediaDevices.enumerateDevices();
        const microphones = devices.filter(device => device.kind === 'audioinput');
        const speakers = devices.filter(device => device.kind === 'audiooutput');
        
        // Clear and populate device selectors
        microphoneSelect.innerHTML = microphones
            .map(device => `<option value="${device.deviceId}">${device.label || 'Microphone ' + (microphones.indexOf(device) + 1)}</option>`)
            .join('');
            
        const speakerOptions = speakers
            .map(device => `<option value="${device.deviceId}">${device.label || 'Speaker ' + (speakers.indexOf(device) + 1)}</option>`)
            .join('');
            
        speakerSelect.innerHTML = speakerOptions;
        headphonesSelect.innerHTML = speakerOptions;
        
        // Add change event listeners
        microphoneSelect.addEventListener('change', async () => {
            if (testAudioStream) {
                testAudioStream.getTracks().forEach(track => track.stop());
            }
            if (audioContext && audioContext.state === 'running') {
                await startAudioTest(); // Restart audio test with new device
            }
        });
        
        speakerSelect.addEventListener('change', () => {
            if (audioContext && audioContext.state === 'running') {
                // Update audio output device
                if (typeof HTMLMediaElement.prototype.setSinkId !== 'undefined') {
                    const deviceId = speakerSelect.value;
                    audioContext.destination.setSinkId(deviceId).catch(console.error);
                }
            }
        });
        
        headphonesSelect.addEventListener('change', () => {
            if (audioContext && audioContext.state === 'running') {
                // Update audio output device
                if (typeof HTMLMediaElement.prototype.setSinkId !== 'undefined') {
                    const deviceId = headphonesSelect.value;
                    audioContext.destination.setSinkId(deviceId).catch(console.error);
                }
            }
        });
        
    } catch (error) {
        console.error('Error initializing audio devices:', error);
    }
}

// Initialize audio devices on page load
initializeAudioDevices();

// Update devices when they change
navigator.mediaDevices.addEventListener('devicechange', initializeAudioDevices);

// Handle device selection
microphoneSelect.addEventListener('change', async (e) => {
    if (recognition) {
        recognition.stop();
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
        setupRecognition();
    }
});

// Function to set up recognition with selected device
function setupRecognition() {
    if (recognition) {
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
        };
    }
}

// Update font size when slider changes
fontSizeSlider.addEventListener('input', (e) => {
    const fontSize = e.target.value;
    fontSizeValue.textContent = fontSize;
    document.documentElement.style.setProperty('--preview-font-size', `${fontSize}px`);
    document.getElementById('live-text').style.fontSize = `${fontSize}px`;
});

// Update font family when selection changes
fontFamilySelect.addEventListener('change', (e) => {
    const fontFamily = e.target.value;
    document.documentElement.style.setProperty('--preview-font-family', fontFamily);
    document.getElementById('live-text').style.fontFamily = fontFamily;
});

// Handle custom font upload
fontUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const fontName = 'CustomFont';
            const fontFace = new FontFace(fontName, e.target.result);
            
            fontFace.load().then(function(loadedFace) {
                document.fonts.add(loadedFace);
                liveTextElement.style.fontFamily = fontName;
                
                // Add custom font to dropdown
                const option = document.createElement('option');
                option.value = fontName;
                option.textContent = file.name.split('.')[0] + ' (Custom)';
                option.selected = true;
                fontFamilySelect.appendChild(option);
                
                // Show success message
                const successMessage = document.getElementById('success-message');
                successMessage.textContent = `Custom font "${file.name}" loaded successfully!`;
                successMessage.style.display = 'block';
                setTimeout(() => {
                    successMessage.style.display = 'none';
                }, 3000);
            }).catch(function(error) {
                // Show error message
                const errorMessage = document.getElementById('error-message');
                errorMessage.textContent = `Error loading font: ${error.message}`;
                errorMessage.style.display = 'block';
                setTimeout(() => {
                    errorMessage.style.display = 'none';
                }, 3000);
            });
        };
        reader.readAsArrayBuffer(file);
    }
});

// Recording functions
function startRecording() {
    // Initialize speech recognition if not already done
    if (!recognition) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = true;
        recognition.interimResults = true;
        setupRecognition();
    }
    recognition.start();
}

function stopRecording() {
    if (recognition) {
        recognition.stop();
    }
}
