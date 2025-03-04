import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Button, Form, Card, Alert, Spinner } from 'react-bootstrap';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import * as api from '../services/api';

const Translator: React.FC = () => {
  // State variables
  const [languages, setLanguages] = useState<string[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('French');
  const [voiceId, setVoiceId] = useState<string>('');
  const [originalText, setOriginalText] = useState<string[]>([]);
  const [partialText, setPartialText] = useState<string>('');
  const [translatedText, setTranslatedText] = useState<string[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('Ready');
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const originalTextEndRef = useRef<HTMLDivElement>(null);
  const translatedTextEndRef = useRef<HTMLDivElement>(null);
  
  // Custom hook for audio recording
  const { isRecording, audioBlob, startRecording, stopRecording } = useAudioRecorder();
  
  // Fetch available languages
  useEffect(() => {
    api.getLanguages()
      .then(response => {
        setLanguages(response.data);
      })
      .catch(err => {
        setError('Failed to load languages. Please refresh the page.');
        console.error('Error fetching languages:', err);
      });
  }, []);
  
  // Auto-scroll to bottom when text updates
  useEffect(() => {
    if (originalTextEndRef.current) {
      originalTextEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    if (translatedTextEndRef.current) {
      translatedTextEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [originalText, translatedText]);
  
  // Process audio blob when available during recording
  useEffect(() => {
    if (isRecording && audioBlob && sessionId) {
      processAudioChunk(audioBlob);
    }
  }, [isRecording, audioBlob, sessionId]);
  
  // Start recording and transcription
  const handleStartRecording = async () => {
    try {
      setStatus('Starting...');
      setError(null);
      
      // Start transcription session
      const response = await api.startTranscriptionSession();
      setSessionId(response.data.sessionId);
      
      // Start recording
      await startRecording();
      
      setStatus('Recording...');
    } catch (err) {
      setStatus('Error');
      setError('Failed to start recording. Please check your microphone permissions.');
      console.error('Error starting recording:', err);
    }
  };
  
  // Stop recording and transcription
  const handleStopRecording = async () => {
    try {
      setStatus('Stopping...');
      
      // Stop recording
      await stopRecording();
      
      // Stop transcription session
      if (sessionId) {
        await api.stopTranscriptionSession(sessionId);
        setSessionId(null);
      }
      
      setStatus('Ready');
    } catch (err) {
      setStatus('Error');
      setError('Failed to stop recording.');
      console.error('Error stopping recording:', err);
    }
  };
  
// Process audio chunk
const processAudioChunk = async (blob: Blob) => {
    if (!sessionId) return;
    
    try {
      await api.processAudioChunk(sessionId, blob);
    } catch (err) {
      console.error('Error processing audio chunk:', err);
    }
  };
  
  // Handle transcription data
  const handleTranscription = (text: string, isFinal: boolean) => {
    if (isFinal) {
      // Add to final transcripts
      setOriginalText(prev => [...prev, text]);
      setPartialText('');
      
      // Translate final transcript
      handleTranslate(text);
    } else {
      // Update partial transcript
      setPartialText(text);
    }
  };
  
  // Translate text
  const handleTranslate = async (text: string) => {
    try {
      setStatus('Translating...');
      
      const response = await api.translateText(text, selectedLanguage);
      const translation = response.data.translation;
      
      // Add to translated text
      setTranslatedText(prev => [...prev, translation]);
      
      // Generate speech for translation
      handleGenerateSpeech(translation);
    } catch (err) {
      setStatus('Error');
      setError('Translation failed. Please try again.');
      console.error('Error translating:', err);
    }
  };
  
  // Generate speech
  const handleGenerateSpeech = async (text: string) => {
    try {
      setStatus('Generating speech...');
      
      const response = await api.generateSpeech(text, voiceId);
      const audioUrl = response.data.audioUrl;
      
      // Set audio URL
      setAudioUrl(audioUrl);
      
      // Play audio
      const audio = new Audio(audioUrl);
      audio.play();
      
      setStatus('Ready');
    } catch (err) {
      setStatus('Error');
      setError('Speech generation failed. Please try again.');
      console.error('Error generating speech:', err);
    }
  };
  
  // Clear all text
  const handleClearText = () => {
    setOriginalText([]);
    setTranslatedText([]);
    setPartialText('');
    setAudioUrl(null);
  };
  
  return (
    <Container>
      <h2 className="my-4">Real-Time Speech Translator</h2>
      
      {error && (
        <Alert variant="danger" onClose={() => setError(null)} dismissible>
          {error}
        </Alert>
      )}
      
      <Row className="mb-4">
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label>Target Language</Form.Label>
            <Form.Select 
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              disabled={isRecording}
            >
              {languages.map((language) => (
                <option key={language} value={language}>{language}</option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group className="mb-3">
            <Form.Label>Voice ID (Optional)</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter ElevenLabs Voice ID"
              value={voiceId}
              onChange={(e) => setVoiceId(e.target.value)}
              disabled={isRecording}
            />
          </Form.Group>
        </Col>
      </Row>
      
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          {!isRecording ? (
            <Button 
              variant="primary"
              onClick={handleStartRecording}
              disabled={status === 'Starting...'}
            >
              {status === 'Starting...' ? (
                <>
                  <Spinner animation="border" size="sm" /> Starting...
                </>
              ) : (
                'Start Recording'
              )}
            </Button>
          ) : (
            <Button 
              variant="danger"
              onClick={handleStopRecording}
              disabled={status === 'Stopping...'}
            >
              {status === 'Stopping...' ? (
                <>
                  <Spinner animation="border" size="sm" /> Stopping...
                </>
              ) : (
                'Stop Recording'
              )}
            </Button>
          )}
          <Button 
            variant="outline-secondary"
            className="ms-2"
            onClick={handleClearText}
            disabled={isRecording}
          >
            Clear
          </Button>
        </div>
        <div className="text-muted">
          Status: {status}
          {isRecording && (
            <span className="ms-2">
              <span 
                className="bg-danger d-inline-block rounded-circle" 
                style={{ width: '10px', height: '10px', animation: 'pulse 1.5s infinite' }}
              ></span>
            </span>
          )}
        </div>
      </div>
      
      <Row>
        <Col md={6} className="mb-4">
          <Card>
            <Card.Header>Original Speech</Card.Header>
            <Card.Body>
              <div 
                className="transcript-box border rounded p-3" 
                style={{ height: '300px', overflowY: 'auto' }}
              >
                {originalText.map((text, index) => (
                  <div key={index} className="mb-2 pb-2 border-bottom">
                    {text}
                  </div>
                ))}
                {partialText && (
                  <div className="text-muted fst-italic">{partialText}</div>
                )}
                <div ref={originalTextEndRef}></div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} className="mb-4">
          <Card>
            <Card.Header>Translated Text</Card.Header>
            <Card.Body>
              <div 
                className="transcript-box border rounded p-3" 
                style={{ height: '300px', overflowY: 'auto' }}
              >
                {translatedText.map((text, index) => (
                  <div key={index} className="mb-2 pb-2 border-bottom">
                    {text}
                  </div>
                ))}
                <div ref={translatedTextEndRef}></div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {audioUrl && (
        <Row>
          <Col>
            <Card>
              <Card.Header>Audio Playback</Card.Header>
              <Card.Body>
                <audio controls src={audioUrl} className="w-100"></audio>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default Translator;