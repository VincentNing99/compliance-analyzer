/**
 * Document management panel with tabs for compliance and internal documents.
 * Medieval Parchment Theme
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
    setUploadStatus('Inscribing scroll...');

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
      setUploadStatus(`Scroll '${docId}' has been burned`);
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      {/* Header with refresh */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h2 style={{
          margin: 0,
          fontFamily: "'Cinzel', serif",
          fontSize: '1.1rem',
          color: '#ffd700',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          textShadow: '0 0 8px rgba(255,215,0,0.3), 1px 1px 2px rgba(0,0,0,0.8)',
        }}>
          <span style={{ fontSize: '1.2rem' }}>&#128220;</span> Archives of the Realm
        </h2>
        <button
          onClick={() => { setIsLoading(true); refreshDocs(); }}
          disabled={isLoading}
          style={{
            background: 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)',
            border: '2px solid #4a3828',
            padding: '0.4rem 0.7rem',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            color: '#c9a227',
            fontSize: '1rem',
            borderRadius: '4px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
          }}
        >
          &#8635;
        </button>
      </div>

      {/* Tabs - Dark wax seal style */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button
          onClick={() => setActiveTab('compliance')}
          style={{
            padding: '0.7rem 1.2rem',
            background: activeTab === 'compliance'
              ? 'linear-gradient(180deg, #722f37 0%, #4a1c24 100%)'
              : 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)',
            color: activeTab === 'compliance' ? '#ffd700' : '#a89070',
            border: activeTab === 'compliance' ? '2px solid #8b0000' : '2px solid #4a3828',
            cursor: 'pointer',
            fontFamily: "'Cinzel', serif",
            fontSize: '0.85rem',
            fontWeight: 600,
            borderRadius: '4px',
            boxShadow: activeTab === 'compliance'
              ? '0 0 12px rgba(139,0,0,0.5), inset 0 1px 0 rgba(255,215,0,0.2)'
              : '0 2px 6px rgba(0,0,0,0.4)',
            textShadow: activeTab === 'compliance' ? '0 0 6px rgba(255,215,0,0.4)' : 'none',
          }}
        >
          &#9670; Decrees ({complianceDocs.length})
        </button>
        <button
          onClick={() => setActiveTab('internal')}
          style={{
            padding: '0.7rem 1.2rem',
            background: activeTab === 'internal'
              ? 'linear-gradient(180deg, #722f37 0%, #4a1c24 100%)'
              : 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)',
            color: activeTab === 'internal' ? '#ffd700' : '#a89070',
            border: activeTab === 'internal' ? '2px solid #8b0000' : '2px solid #4a3828',
            cursor: 'pointer',
            fontFamily: "'Cinzel', serif",
            fontSize: '0.85rem',
            fontWeight: 600,
            borderRadius: '4px',
            boxShadow: activeTab === 'internal'
              ? '0 0 12px rgba(139,0,0,0.5), inset 0 1px 0 rgba(255,215,0,0.2)'
              : '0 2px 6px rgba(0,0,0,0.4)',
            textShadow: activeTab === 'internal' ? '0 0 6px rgba(255,215,0,0.4)' : 'none',
          }}
        >
          &#9670; Scrolls ({internalDocs.length})
        </button>
      </div>

      {/* Document List - Dark ancient tome style */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '0.75rem',
        marginBottom: '1rem',
        minHeight: '180px',
        background: 'linear-gradient(180deg, #0d0a08 0%, #1a1410 50%, #0d0a08 100%)',
        border: '2px solid #4a3828',
        borderRadius: '4px',
        boxShadow: 'inset 0 2px 12px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3)',
      }}>
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', gap: '0.75rem' }}>
            <div className="spinner" />
            <span style={{ fontStyle: 'italic', color: '#a89070', fontFamily: "'Cinzel', serif" }}>Consulting the archives...</span>
          </div>
        ) : currentDocs.length === 0 ? (
          <p style={{ color: '#a89070', textAlign: 'center', fontStyle: 'italic', fontFamily: "'Cinzel', serif" }}>
            The archive stands empty...
          </p>
        ) : (
          currentDocs.map(docId => (
            <div
              key={docId}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                padding: '0.7rem 0.6rem',
                borderBottom: '1px solid #3a2818',
                background: currentSelected.includes(docId) ? 'rgba(201,162,39,0.1)' : 'transparent',
                gap: '1rem',
              }}
            >
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem', cursor: 'pointer', color: '#d4c4a8', flex: 1 }}>
                <input
                  type="checkbox"
                  checked={currentSelected.includes(docId)}
                  onChange={() => toggleSelection(docId, currentType)}
                  style={{ accentColor: '#c9a227', width: '16px', height: '16px', flexShrink: 0, marginTop: '2px' }}
                />
                <span style={{ fontSize: '0.95rem', color: currentSelected.includes(docId) ? '#ffd700' : '#d4c4a8', fontWeight: currentSelected.includes(docId) ? 600 : 400, wordBreak: 'break-word' }}>{docId}</span>
              </label>
              <button
                onClick={() => handleDelete(docId, currentType)}
                title="Delete"
                className="candle-btn"
                style={{
                  background: 'linear-gradient(180deg, #5c1010 0%, #3a0808 100%)',
                  color: '#ff6b4a',
                  border: '1px solid #2a0000',
                  padding: '0.4rem 0.6rem',
                  cursor: 'pointer',
                  borderRadius: '3px',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{ fontSize: '1.1rem' }}>&#128367;</span>
              </button>
            </div>
          ))
        )}
      </div>

      {/* Upload Section - Dark Scribe's Desk style */}
      <div style={{
        background: 'linear-gradient(180deg, #1a1410 0%, #0d0a08 100%)',
        padding: '1rem',
        borderRadius: '6px',
        border: '2px solid #4a3828',
        boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.4)',
      }}>
        <h3 style={{
          marginTop: 0,
          marginBottom: '0.75rem',
          fontFamily: "'Cinzel', serif",
          fontSize: '1rem',
          color: '#ffd700',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          textShadow: '0 0 8px rgba(255,215,0,0.3)',
        }}>
          <span style={{ fontSize: '1.1rem' }}>&#129718;</span> Inscribe New Document
        </h3>

        <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
          <label style={{ marginRight: '1rem', color: '#d4c4a8', cursor: 'pointer', fontFamily: "'Cinzel', serif" }}>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'regulation'}
              onChange={() => setUploadType('regulation')}
              style={{ accentColor: '#c9a227', marginRight: '0.4rem' }}
            />
            Decree
          </label>
          <label style={{ color: '#d4c4a8', cursor: 'pointer', fontFamily: "'Cinzel', serif" }}>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'company_doc'}
              onChange={() => setUploadType('company_doc')}
              style={{ accentColor: '#c9a227', marginRight: '0.4rem' }}
            />
            Scroll
          </label>
        </div>

        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.pptx"
          onChange={handleUpload}
          disabled={isUploading}
          style={{
            marginBottom: '0.5rem',
            color: '#d4c4a8',
            fontSize: '0.9rem',
          }}
        />

        {uploadStatus && (
          <p style={{
            margin: '0.5rem 0 0 0',
            fontSize: '0.85rem',
            fontStyle: 'italic',
            fontFamily: "'Cinzel', serif",
            color: uploadStatus.startsWith('Error') ? '#ff6b4a' : '#c9a227',
            textShadow: '0 1px 2px rgba(0,0,0,0.5)',
          }}>
            {uploadStatus}
          </p>
        )}
      </div>
    </div>
  );
}
