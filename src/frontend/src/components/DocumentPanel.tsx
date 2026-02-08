/**
 * Document management panel with tabs for compliance and internal documents.
 */
import { useState, useEffect, useCallback } from 'react';
import { listDocuments, uploadDocument, deleteDocument } from '../api/client';
import type { DocType } from '../api/client';

interface DocumentPanelProps {
  selectedCompliance: string[];
  setSelectedCompliance: (docs: string[]) => void;
  selectedInternal: string[];
  setSelectedInternal: (docs: string[]) => void;
}

export function DocumentPanel({
  selectedCompliance,
  setSelectedCompliance,
  selectedInternal,
  setSelectedInternal,
}: DocumentPanelProps) {
  const [activeTab, setActiveTab] = useState<'compliance' | 'internal'>('compliance');
  const [complianceDocs, setComplianceDocs] = useState<string[]>([]);
  const [internalDocs, setInternalDocs] = useState<string[]>([]);
  const [uploadType, setUploadType] = useState<DocType>('regulation');
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch document lists
  const refreshDocs = useCallback(async () => {
    try {
      const [compliance, internal] = await Promise.all([
        listDocuments('regulation'),
        listDocuments('company_doc'),
      ]);
      setComplianceDocs(compliance);
      setInternalDocs(internal);
    } catch (e) {
      console.error('Failed to fetch documents:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocs();
  }, [refreshDocs]);

  // Handle file upload
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('Uploading...');

    try {
      const result = await uploadDocument(file, uploadType);
      setUploadStatus(result.message);
      await refreshDocs();
    } catch (error) {
      setUploadStatus(`Error: ${error instanceof Error ? error.message : 'Upload failed'}`);
    } finally {
      setIsUploading(false);
      e.target.value = ''; // Reset file input
    }
  };

  // Handle document deletion
  const handleDelete = async (docId: string, type: DocType) => {
    try {
      await deleteDocument(docId, type);
      await refreshDocs();
      // Remove from selection if deleted
      if (type === 'regulation') {
        setSelectedCompliance(selectedCompliance.filter(id => id !== docId));
      } else {
        setSelectedInternal(selectedInternal.filter(id => id !== docId));
      }
      setUploadStatus(`Deleted '${docId}'`);
    } catch (error) {
      setUploadStatus(`Error: ${error instanceof Error ? error.message : 'Delete failed'}`);
    }
  };

  // Toggle document selection
  const toggleSelection = (docId: string, type: DocType) => {
    if (type === 'regulation') {
      if (selectedCompliance.includes(docId)) {
        setSelectedCompliance(selectedCompliance.filter(id => id !== docId));
      } else {
        setSelectedCompliance([...selectedCompliance, docId]);
      }
    } else {
      if (selectedInternal.includes(docId)) {
        setSelectedInternal(selectedInternal.filter(id => id !== docId));
      } else {
        setSelectedInternal([...selectedInternal, docId]);
      }
    }
  };

  const currentDocs = activeTab === 'compliance' ? complianceDocs : internalDocs;
  const currentSelected = activeTab === 'compliance' ? selectedCompliance : selectedInternal;
  const currentType: DocType = activeTab === 'compliance' ? 'regulation' : 'company_doc';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h2 style={{ margin: 0, fontSize: '11px', color: '#2dd4bf', textTransform: 'uppercase' }}>
          [ DOCUMENTS ]
        </h2>
        <button
          onClick={() => { setIsLoading(true); refreshDocs(); }}
          disabled={isLoading}
          style={{
            background: '#134e4a',
            border: '2px solid #14b8a6',
            padding: '0.3rem 0.5rem',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            color: '#ffffff',
            fontSize: '10px',
            borderRadius: '4px',
          }}
        >
          ↻
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.75rem' }}>
        <button
          onClick={() => setActiveTab('compliance')}
          style={{
            padding: '0.5rem 0.75rem',
            background: activeTab === 'compliance' ? '#14b8a6' : '#134e4a',
            color: '#ffffff',
            border: '2px solid',
            borderColor: activeTab === 'compliance' ? '#14b8a6' : '#0d9488',
            cursor: 'pointer',
            fontSize: '8px',
            borderRadius: '4px',
          }}
        >
          REGS ({complianceDocs.length})
        </button>
        <button
          onClick={() => setActiveTab('internal')}
          style={{
            padding: '0.5rem 0.75rem',
            background: activeTab === 'internal' ? '#14b8a6' : '#134e4a',
            color: '#ffffff',
            border: '2px solid',
            borderColor: activeTab === 'internal' ? '#14b8a6' : '#0d9488',
            cursor: 'pointer',
            fontSize: '8px',
            borderRadius: '4px',
          }}
        >
          DOCS ({internalDocs.length})
        </button>
      </div>

      {/* Document List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '0.5rem',
        marginBottom: '0.75rem',
        minHeight: '150px',
        background: '#0a0a0f',
        borderRadius: '8px',
      }}>
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', gap: '0.5rem' }}>
            <div className="spinner" />
            <span style={{ fontSize: '8px', color: '#5eead4' }}>LOADING...</span>
          </div>
        ) : currentDocs.length === 0 ? (
          <p style={{ color: '#5eead4', textAlign: 'center', fontSize: '8px' }}>NO DOCS YET</p>
        ) : (
          currentDocs.map(docId => (
            <div
              key={docId}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.4rem',
                borderBottom: '1px solid #134e4a',
              }}
            >
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#ffffff' }}>
                <input
                  type="checkbox"
                  checked={currentSelected.includes(docId)}
                  onChange={() => toggleSelection(docId, currentType)}
                  style={{ accentColor: '#14b8a6' }}
                />
                <span style={{ fontSize: '8px' }}>{docId}</span>
              </label>
              <button
                onClick={() => handleDelete(docId, currentType)}
                style={{
                  background: '#0d9488',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.2rem 0.4rem',
                  cursor: 'pointer',
                  fontSize: '7px',
                  borderRadius: '4px',
                }}
              >
                DEL
              </button>
            </div>
          ))
        )}
      </div>

      {/* Upload Section */}
      <div style={{
        background: '#134e4a',
        padding: '0.75rem',
        borderRadius: '8px',
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '9px', color: '#5eead4' }}>
          + UPLOAD
        </h3>

        <div style={{ marginBottom: '0.5rem', fontSize: '8px' }}>
          <label style={{ marginRight: '0.75rem', color: '#ffffff' }}>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'regulation'}
              onChange={() => setUploadType('regulation')}
              style={{ accentColor: '#14b8a6' }}
            />
            {' '}REG
          </label>
          <label style={{ color: '#ffffff' }}>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'company_doc'}
              onChange={() => setUploadType('company_doc')}
              style={{ accentColor: '#14b8a6' }}
            />
            {' '}DOC
          </label>
        </div>

        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.pptx"
          onChange={handleUpload}
          disabled={isUploading}
          style={{ marginBottom: '0.5rem', fontSize: '8px', color: '#ffffff' }}
        />

        {uploadStatus && (
          <p style={{
            margin: 0,
            fontSize: '8px',
            color: uploadStatus.startsWith('Error') ? '#f87171' : '#5eead4',
          }}>
            {uploadStatus.toUpperCase()}
          </p>
        )}
      </div>
    </div>
  );
}
