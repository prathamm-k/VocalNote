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
      <div className="hero-split">
        {/* Left: Text content */}
        <div className="hero-text">
          <p className="hero-kicker devanagari-accent">पॉडकास्ट जनरेटर</p>
          <h2 className="hero-title">
            Your PDF,<br />
            <span className="hero-title-accent">spoken aloud</span>
          </h2>
          <p className="hero-subtitle">
            Local AI turns documents into natural two-speaker podcast
            conversations. No cloud. No API keys.
          </p>
        </div>

        {/* Right: Upload zone */}
        <div className="hero-upload-col">
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
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <path d="M20 4L20 28" stroke="var(--terracotta)" strokeWidth="1.5" strokeLinecap="round"/>
                      <path d="M13 11L20 4L27 11" stroke="var(--terracotta)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M6 24V33C6 34.7 7.3 36 9 36H31C32.7 36 34 34.7 34 33V24" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                  </div>
                  <p className="upload-label">Drop your PDF here</p>
                  <p className="upload-sublabel">or</p>
                  <button
                    type="button"
                    className="upload-browse-btn"
                    onClick={handleBrowseClick}
                    disabled={isProcessing}
                    id="browse-button"
                  >
                    Browse files
                  </button>
                  <p className="upload-hint">PDF only · Up to 100K characters</p>
                </>
              ) : (
                <div className="upload-file-info">
                  <div className="file-icon" aria-hidden="true">
                    <svg width="32" height="40" viewBox="0 0 32 40" fill="none">
                      <path d="M2 4C2 1.8 3.8 0 6 0H20L30 10V36C30 38.2 28.2 40 26 40H6C3.8 40 2 38.2 2 36V4Z" fill="var(--surface-2)" stroke="var(--border-warm)" strokeWidth="1"/>
                      <path d="M20 0L30 10H24C21.8 10 20 8.2 20 6V0Z" fill="var(--surface-1)"/>
                      <text x="16" y="28" textAnchor="middle" fill="var(--terracotta)" fontSize="9" fontWeight="700" fontFamily="var(--font-display)">PDF</text>
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
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <path d="M9 2C9 2 11 5 11 9C11 13 9 16 9 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <path d="M5 4.5C5 4.5 7 6.5 7 9C7 11.5 5 13.5 5 13.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <path d="M13 4.5C13 4.5 15 6.5 15 9C15 11.5 13 13.5 13 13.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </span>
                <span>Generate podcast</span>
              </>
            )}
          </button>
        </div>
      </div>
    </section>
  );
};

export default HeroUpload;
