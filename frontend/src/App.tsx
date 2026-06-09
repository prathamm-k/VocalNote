import { useState, type ChangeEvent } from 'react';
import axios from 'axios';
import Header from './components/Header';
import HeroUpload from './components/HeroUpload';
import StatusBar from './components/StatusBar';
import AudioPlayer from './components/AudioPlayer';
import FeatureCards from './components/FeatureCards';
import Footer from './components/Footer';
import './App.css';

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError('');
    } else {
      setError('Please upload a valid PDF file.');
      setFile(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('No file selected.');
      return;
    }

    setIsProcessing(true);
    setStatus('Processing PDF...');
    setError('');
    setAudioUrl('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:9000/generate-podcast', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
      });

      // Check if the response is actually an error JSON (not audio)
      const contentType = response.headers['content-type'];
      if (typeof contentType === 'string' && contentType.includes('application/json')) {
        const text = await response.data.text();
        const json = JSON.parse(text);
        setError(json.detail || json.error || 'Unknown error from server.');
      } else {
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'audio/wav' }));
        setAudioUrl(url);
        setStatus('Podcast generated successfully!');
      }
    } catch (err: any) {
      if (err.response) {
        // Server returned an error status code
        try {
          const text = await err.response.data.text();
          const json = JSON.parse(text);
          setError(json.detail || 'Server error. Please try again.');
        } catch {
          setError(`Server error (${err.response.status}). Please try again.`);
        }
      } else if (err.request) {
        setError('Cannot reach the backend server. Is it running on port 9000?');
      } else {
        setError('Error generating podcast. Please try again.');
      }
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="vaak-app">
      <Header />

      <main className="vaak-main">
        <HeroUpload
          file={file}
          isProcessing={isProcessing}
          onFileChange={handleFileChange}
          onSubmit={handleSubmit}
        />

        <StatusBar
          status={status}
          error={error}
          isProcessing={isProcessing}
        />

        {audioUrl && <AudioPlayer audioUrl={audioUrl} />}

        <FeatureCards />
      </main>

      <Footer />
    </div>
  );
};

export default App;