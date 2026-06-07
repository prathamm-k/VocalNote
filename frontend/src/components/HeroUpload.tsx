import React, { useRef, useState, type ChangeEvent, type DragEvent } from 'react';
import './HeroUpload.css';

interface HeroUploadProps {
  file: File | null;
  isProcessing: boolean;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: () => void;
}

const HeroUpload: React.FC<HeroUploadProps> = ({ file, isProcessing, onFileChange, onSubmit }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      // Create a synthetic event-like call
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(droppedFile);
      if (fileInputRef.current) {
        fileInputRef.current.files = dataTransfer.files;
        const syntheticEvent = { target: fileInputRef.current } as unknown as ChangeEvent<HTMLInputElement>;
        onFileChange(syntheticEvent);
      }
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <section className="hero-section" id="hero-upload">
      {/* Background decorations */}
      <div className="hero-mandala hero-mandala--left" aria-hidden="true"></div>
      <div className="hero-mandala hero-mandala--right" aria-hidden="true"></div>

      <div className="hero-content">
        <div className="hero-text">
          <p className="hero-kicker devanagari-accent">पॉडकास्ट जनरेटर</p>
          <h2 className="hero-title">
            Transform your <span className="gold-text">documents</span> into
            <br/>
            <span className="hero-title-accent">engaging podcasts</span>
          </h2>
          <p className="hero-subtitle">
            Upload a PDF and let AI craft a two-speaker podcast conversation, 
            complete with natural dialogue, anecdotes, and storytelling — all 
            running locally on your machine.
          </p>
        </div>

        {/* Upload Zone */}
        <div
          className={`upload-zone ${isDragOver ? 'upload-zone--drag' : ''} ${file ? 'upload-zone--ready' : ''} ${isProcessing ? 'upload-zone--processing' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          id="upload-dropzone"
        >
          <div className="upload-zone-inner">
            {!file ? (
              <>
                <div className="upload-icon" aria-hidden="true">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <path d="M24 4L24 32" stroke="var(--saffron)" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M16 12L24 4L32 12" stroke="var(--saffron)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M8 28V38C8 40.2 9.8 42 12 42H36C38.2 42 40 40.2 40 38V28" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                <p className="upload-label">
                  Drag & drop your PDF here
                </p>
                <p className="upload-sublabel">or</p>
                <button
                  type="button"
                  className="upload-browse-btn"
                  onClick={handleBrowseClick}
                  disabled={isProcessing}
                  id="browse-button"
                >
                  Browse Files
                </button>
                <p className="upload-hint">PDF files only • Max 100,000 characters extracted</p>
              </>
            ) : (
              <div className="upload-file-info">
                <div className="file-icon" aria-hidden="true">
                  <svg width="40" height="48" viewBox="0 0 40 48" fill="none">
                    <path d="M4 4C4 1.8 5.8 0 8 0H26L36 10V44C36 46.2 34.2 48 32 48H8C5.8 48 4 46.2 4 44V4Z" fill="var(--surface-2)" stroke="var(--border-gold)" strokeWidth="1"/>
                    <path d="M26 0L36 10H30C27.8 10 26 8.2 26 6V0Z" fill="var(--surface-1)"/>
                    <text x="20" y="32" textAnchor="middle" fill="var(--pomegranate)" fontSize="10" fontWeight="700" fontFamily="var(--font-display)">PDF</text>
                  </svg>
                </div>
                <div className="file-details">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">{formatFileSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  className="file-change-btn"
                  onClick={handleBrowseClick}
                  disabled={isProcessing}
                  aria-label="Change file"
                >
                  Change
                </button>
              </div>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={onFileChange}
            disabled={isProcessing}
            className="upload-input-hidden"
            id="file-input"
            aria-label="Upload PDF file"
          />
        </div>

        {/* Generate Button */}
        <button
          className={`generate-btn ${isProcessing ? 'generate-btn--loading' : ''}`}
          onClick={onSubmit}
          disabled={isProcessing || !file}
          id="generate-button"
        >
          {isProcessing ? (
            <>
              <span className="mandala-spinner" aria-hidden="true"></span>
              <span>Crafting your podcast…</span>
            </>
          ) : (
            <>
              <span className="btn-icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2C10 2 12 5 12 10C12 15 10 18 10 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M6 5C6 5 8 7 8 10C8 13 6 15 6 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M14 5C14 5 16 7 16 10C16 13 14 15 14 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M2 8C2 8 4 9 4 10C4 11 2 12 2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M18 8C18 8 20 9 20 10C20 11 18 12 18 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </span>
              <span>Generate Podcast</span>
            </>
          )}
        </button>
      </div>
    </section>
  );
};

export default HeroUpload;
