import React, { useState, useRef } from 'react';
import axios from 'axios';
import './PolicyUploadSection.css';

interface PolicyUploadSectionProps {
  policy: any;
  onPolicyUpload: (data: any) => void;
}

const PolicyUploadSection: React.FC<PolicyUploadSectionProps> = ({
  policy,
  onPolicyUpload,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      uploadFile(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      alert('Please upload a PDF file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/upload-policy', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(percentCompleted);
        },
      });

      const now = new Date();
      setLastUpdated(
        `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`
      );
      onPolicyUpload(response.data);
      setIsUploading(false);
      setUploadProgress(0);
    } catch (error) {
      console.error('Upload failed:', error);
      setIsUploading(false);
      alert('Policy upload failed');
    }
  };

  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="policy-upload-section">
      <div className="policy-header gradient-primary">
        <h2>MarginGuard</h2>
        <p>Competitive Analysis Engine</p>
      </div>

      <div className="policy-content">
        <label className="section-label">Company Policy Document</label>

        {!policy ? (
          <div
            className={`drag-drop-zone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <p>Drag PDF here or click to browse</p>
            <div className="button-group">
              <button
                className="btn-secondary"
                onClick={() => fileInputRef.current?.click()}
              >
                Choose File
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileInputChange}
                hidden
              />
            </div>
          </div>
        ) : null}

        {isUploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p>Uploading... {uploadProgress}%</p>
          </div>
        )}

        {policy && (
          <div className="policy-loaded">
            <p className="status-message">
              Policy Loaded: {policy.sections_uploaded || 0} sections
            </p>
            {lastUpdated && <p className="timestamp">Last updated: {lastUpdated}</p>}

            <div className="policy-sections">
              {policy.sections?.map((section: any, index: number) => (
                <div key={index} className="policy-card">
                  <div
                    className="policy-card-header"
                    onClick={() => toggleSection(index)}
                  >
                    <span className="caret">
                      {expandedSections.has(index) ? '▼' : '▶'}
                    </span>
                    <h4>{section.title}</h4>
                  </div>
                  {expandedSections.has(index) && (
                    <div className="policy-card-content">
                      <p>{section.content}</p>
                      <button
                        className="btn-copy"
                        onClick={() => copyToClipboard(section.content)}
                      >
                        Copy
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button
              className="btn-primary"
              onClick={() => fileInputRef.current?.click()}
            >
              Upload New Policy
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PolicyUploadSection;
