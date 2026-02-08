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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h2 style={{ margin: 0 }}>Documents</h2>
        <button
          onClick={() => { setIsLoading(true); refreshDocs(); }}
          disabled={isLoading}
          style={{
            background: '#f3f4f6',
            border: 'none',
            borderRadius: '0.5rem',
            padding: '0.5rem 0.75rem',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontSize: '1rem',
          }}
        >
          ↻
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button
          onClick={() => setActiveTab('compliance')}
          style={{
            padding: '0.5rem 1rem',
            background: activeTab === 'compliance' ? '#4f46e5' : '#e5e7eb',
            color: activeTab === 'compliance' ? 'white' : 'black',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
          }}
        >
          Compliance ({complianceDocs.length})
        </button>
        <button
          onClick={() => setActiveTab('internal')}
          style={{
            padding: '0.5rem 1rem',
            background: activeTab === 'internal' ? '#4f46e5' : '#e5e7eb',
            color: activeTab === 'internal' ? 'white' : 'black',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer',
          }}
        >
          Internal ({internalDocs.length})
        </button>
      </div>

      {/* Document List */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        padding: '0.5rem',
        marginBottom: '1rem',
        minHeight: '200px',
      }}>
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <div className="spinner" />
          </div>
        ) : currentDocs.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center' }}>No documents yet</p>
        ) : (
          currentDocs.map(docId => (
            <div
              key={docId}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.5rem',
                borderBottom: '1px solid #f0f0f0',
              }}
            >
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={currentSelected.includes(docId)}
                  onChange={() => toggleSelection(docId, currentType)}
                />
                <span>{docId}</span>
              </label>
              <button
                onClick={() => handleDelete(docId, currentType)}
                style={{
                  background: '#fee2e2',
                  color: '#dc2626',
                  border: 'none',
                  borderRadius: '0.25rem',
                  padding: '0.25rem 0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                }}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>

      {/* Upload Section */}
      <div style={{
        background: '#f8fafc',
        borderRadius: '0.5rem',
        padding: '1rem',
        border: '2px dashed #cbd5e1',
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Upload Document</h3>

        <div style={{ marginBottom: '0.5rem' }}>
          <label style={{ marginRight: '1rem' }}>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'regulation'}
              onChange={() => setUploadType('regulation')}
            />
            {' '}Compliance
          </label>
          <label>
            <input
              type="radio"
              name="uploadType"
              checked={uploadType === 'company_doc'}
              onChange={() => setUploadType('company_doc')}
            />
            {' '}Internal
          </label>
        </div>

        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt,.pptx"
          onChange={handleUpload}
          disabled={isUploading}
          style={{ marginBottom: '0.5rem' }}
        />

        {uploadStatus && (
          <p style={{
            margin: 0,
            fontSize: '0.875rem',
            color: uploadStatus.startsWith('Error') ? '#dc2626' : '#059669',
          }}>
            {uploadStatus}
          </p>
        )}
      </div>
    </div>
  );
}
