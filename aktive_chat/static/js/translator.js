// Basic audio recording functionality
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
    }
    
    async start() {
        try {
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];
            
            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            return false;
        }
    }
    
    stop() {
        return new Promise((resolve) => {
            if (!this.mediaRecorder || !this.isRecording) {
                resolve(null);
                return;
            }
            
            this.mediaRecorder.onstop = () => {
                // Create blob from chunks
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                
                // Cleanup
                this.stream.getTracks().forEach(track => track.stop());
                this.mediaRecorder = null;
                this.stream = null;
                this.isRecording = false;
                
                resolve(audioBlob);
            };
            
            this.mediaRecorder.stop();
        });
    }
}