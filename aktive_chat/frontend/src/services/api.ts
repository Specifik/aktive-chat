import axios from 'axios';

// Create an axios instance with CSRF support
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Add request interceptor to handle CSRF token
api.interceptors.request.use(
  (config) => {
    // Get CSRF token from cookies
    const csrfToken = getCookie('csrftoken');
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Helper to get cookies
function getCookie(name: string): string | null {
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
  }
  return null;
}

// API endpoints
export const getLanguages = () => api.get('/languages/');

export const translateText = (text: string, language: string) => 
  api.post('/translate/', { text, language });

export const generateSpeech = (text: string, voiceId: string) => 
  api.post('/text-to-speech/', { text, voiceId });

export const getTranslationHistory = (page = 1, pageSize = 10, language?: string) => {
  let url = `/history/?page=${page}&page_size=${pageSize}`;
  if (language) {
    url += `&language=${language}`;
  }
  return api.get(url);
};

export const deleteTranslationHistory = (historyId: number) => 
  api.delete(`/history/${historyId}/`);

export const startTranscriptionSession = () => 
  api.post('/transcription/session/');

export const stopTranscriptionSession = (sessionId: string) => 
  api.delete('/transcription/session/', { data: { sessionId } });

export const processAudioChunk = (sessionId: string, audio: Blob) => {
  const formData = new FormData();
  formData.append('sessionId', sessionId);
  formData.append('audio', audio);
  
  return api.post('/transcription/process/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export default api;