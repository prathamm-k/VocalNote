import React, { useRef, useEffect, useState } from 'react';
import './AudioPlayer.css';

interface AudioPlayerProps {
  audioUrl: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <section className="audio-player-section" id="audio-player">
      <div className="audio-player-container">
        {/* Rangoli Divider */}
        <div className="rangoli-divider">
          <span className="rangoli-dot"></span>
        </div>

        <div className="audio-player-header">
          <span className="audio-label devanagari-accent">आपका पॉडकास्ट</span>
          <h3 className="audio-title gold-text">Your Podcast is Ready</h3>
        </div>

        {/* Custom Audio Player Card */}
        <div className="audio-card">
          {/* Waveform decoration */}
          <div className="waveform-bg" aria-hidden="true">
            {Array.from({ length: 40 }).map((_, i) => (
              <div
                key={i}
                className={`waveform-bar ${isPlaying ? 'waveform-bar--active' : ''}`}
                style={{
                  height: `${20 + Math.sin(i * 0.5) * 15 + Math.random() * 10}%`,
                  animationDelay: `${i * 0.05}s`,
                }}
              ></div>
            ))}
          </div>

          <div className="player-controls">
            <button
              className="play-btn"
              onClick={togglePlay}
              aria-label={isPlaying ? 'Pause podcast' : 'Play podcast'}
              id="play-button"
            >
              {isPlaying ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" rx="1"/>
                  <rect x="14" y="4" width="4" height="16" rx="1"/>
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5V19L19 12L8 5Z"/>
                </svg>
              )}
            </button>

            <div className="player-track-area">
              <div className="player-time">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
              <div className="player-slider-container">
                <div className="player-slider-track">
                  <div
                    className="player-slider-fill"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <input
                  type="range"
                  className="player-slider-input"
                  min="0"
                  max={duration || 0}
                  step="0.1"
                  value={currentTime}
                  onChange={handleSeek}
                  aria-label="Seek podcast position"
                  id="seek-slider"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Download */}
        <a
          className="download-btn"
          href={audioUrl}
          download="podcast.wav"
          id="download-button"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 2V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M5 9L9 13L13 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 15H15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span>Download WAV</span>
        </a>

        <audio ref={audioRef} src={audioUrl} preload="metadata" />
      </div>
    </section>
  );
};

export default AudioPlayer;
