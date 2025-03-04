import { useState, useRef, useEffect, useCallback } from 'react';

interface AudioRecorderOptions {
  mimeType?: string;
  audioBitsPerSecond?: number;
  sampleRate?: number;
  channelCount?: number;
}

export function useAudioRecorder(options: AudioRecorderOptions = {}) {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Default options
  const recorderOptions = {
    mimeType: options.mimeType || 'audio/webm',
    audioBitsPerSecond: options.audioBitsPerSecond || 128000,
    sampleRate: options.sampleRate || 44100,
    channelCount: options.channelCount || 1
  };
  
  // Clean up function
  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (mediaRecorderRef.current) {
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      mediaRecorderRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    chunksRef.current = [];
  }, []);
  
  // Start recording
  const startRecording = useCallback(async () => {
    try {
      cleanup();
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: recorderOptions.sampleRate,
          channelCount: recorderOptions.channelCount
        }
      });
      
      streamRef.current = stream;
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: recorderOptions.mimeType,
        audioBitsPerSecond: recorderOptions.audioBitsPerSecond
      });
      
      mediaRecorderRef.current = mediaRecorder;
      
      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          // Create a new blob for the current chunk
          const currentChunk = new Blob([event.data], { type: recorderOptions.mimeType });
          setAudioBlob(currentChunk);
        }
      };
      
      // Start recording
      mediaRecorder.start(1000); // Capture data every second
      
      setIsRecording(true);
      setError(null);
      
      return Promise.resolve();
    } catch (err) {
      cleanup();
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      return Promise.reject(error);
    }
  }, [cleanup, recorderOptions]);
  
  // Stop recording
  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current || !isRecording) {
      return Promise.resolve();
    }
    
    return new Promise<void>((resolve) => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.onstop = () => {
          // Create a final blob with all chunks
          const completeBlob = new Blob(chunksRef.current, { type: recorderOptions.mimeType });
          setAudioBlob(completeBlob);
          
          cleanup();
          setIsRecording(false);
          resolve();
        };
        
        mediaRecorderRef.current.stop();
      } else {
        cleanup();
        setIsRecording(false);
        resolve();
      }
    });
  }, [isRecording, cleanup, recorderOptions]);
  
  // Clean up on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);
  
  return {
    isRecording,
    audioBlob,
    error,
    startRecording,
    stopRecording
  };
}