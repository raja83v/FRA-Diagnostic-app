/**
 * Import Data page with Soft & Elegant Light Theme.
 * Full drag-and-drop upload with transformer selector and import history.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import {
  getTransformers,
  uploadFRAFile,
  getImportHistory,
} from '../api';
import type {
  Transformer,
  UploadResponse,
  ImportHistoryRecord,
} from '../types';
import { GlassCard, Button, LoadingOverlay } from '../components/ui';

const WINDING_CONFIGS = [
  'HV-LV',
  'HV-TV',
  'LV-TV',
  'HV-GND',
  'LV-GND',
  'TV-GND',
  'HV-Open',
  'LV-Open',
  'Other',
];

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

export default function ImportPage() {
  // Form state
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [selectedTransformerId, setSelectedTransformerId] = useState('');
  const [windingConfig, setWindingConfig] = useState('HV-LV');
  const [measurementDate, setMeasurementDate] = useState('');
  const [temperature, setTemperature] = useState('');
  const [notes, setNotes] = useState('');

  // File & upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState('');

  // Import history
  const [importHistory, setImportHistory] = useState<ImportHistoryRecord[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load transformers and import history
  useEffect(() => {
    Promise.all([
      getTransformers().then(setTransformers),
      loadHistory(),
    ]).finally(() => setInitialLoading(false));
  }, []);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const history = await getImportHistory();
      setImportHistory(history);
    } catch (e) {
      console.error('Failed to load import history', e);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Drag & Drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus('idle');
      setUploadResult(null);
      setUploadError('');
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus('idle');
      setUploadResult(null);
      setUploadError('');
    }
  };

  // Upload
  const handleUpload = async () => {
    if (!selectedFile || !selectedTransformerId) return;

    setUploadStatus('uploading');
    setUploadError('');
    setUploadResult(null);

    try {
      const result = await uploadFRAFile({
        file: selectedFile,
        transformer_id: selectedTransformerId,
        winding_config: windingConfig,
        measurement_date: measurementDate || undefined,
        temperature_celsius: temperature ? parseFloat(temperature) : undefined,
        notes: notes || undefined,
      });
      setUploadStatus('success');
      setUploadResult(result);
      loadHistory();
    } catch (err: unknown) {
      setUploadStatus('error');
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setUploadError(
        axiosErr.response?.data?.detail || axiosErr.message || 'Upload failed'
      );
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setUploadResult(null);
    setUploadError('');
    setNotes('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={16} className="text-(--status-success)" />;
      case 'failed':
        return <XCircle size={16} className="text-(--status-critical)" />;
      case 'partial':
        return <AlertTriangle size={16} className="text-(--status-warning)" />;
      default:
        return <Clock size={16} className="text-(--text-muted)" />;
    }
  };

  const canUpload =
    selectedFile && selectedTransformerId && uploadStatus !== 'uploading';

  if (initialLoading) {
    return <LoadingOverlay message="Loading import page..." />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">
          Import FRA Data
        </h1>
        <p className="text-(--text-muted) mt-1">
          Upload and parse frequency response analysis measurements
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Upload Area */}
        <div className="lg:col-span-2 space-y-5 animate-fade-in-up stagger-1">
          {/* Drag & Drop Zone */}
          <GlassCard padding="lg" hover={false}>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`drop-zone ${
                isDragOver
                  ? 'active'
                  : selectedFile
                  ? 'success'
                  : ''
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt,.tsv,.xml,.fra,.frax,.m4000"
                onChange={handleFileSelect}
                className="hidden"
              />
              {selectedFile ? (
                <div className="space-y-3">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-(--status-success-bg) flex items-center justify-center">
                    <FileText size={32} className="text-(--status-success)" />
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-(--text-primary)">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-(--text-muted) mt-1">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      resetForm();
                    }}
                    className="inline-flex items-center gap-1.5 text-sm text-(--status-critical) hover:text-red-700 transition-colors"
                  >
                    <Trash2 size={14} />
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-(--bg-secondary) border border-(--card-border) flex items-center justify-center">
                    <Upload size={28} className="text-(--text-muted)" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-(--text-primary)">
                      Upload FRA Measurement File
                    </h3>
                    <p className="text-sm text-(--text-muted) mt-1">
                      Drag & drop your file here, or click to browse
                    </p>
                  </div>
                  <p className="text-xs text-(--text-muted)">
                    Supports: CSV, XML, Omicron (.fra), Megger (.frax), Doble (.m4000)
                  </p>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Upload Result */}
          {uploadStatus === 'success' && uploadResult && (
            <div className="alert alert-success animate-fade-in-up">
              <CheckCircle size={20} className="shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="alert-title">{uploadResult.message}</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 text-sm">
                  <div>Vendor: <strong>{uploadResult.vendor_detected || 'Generic'}</strong></div>
                  <div>Data Points: <strong className="font-mono">{uploadResult.data_points.toLocaleString()}</strong></div>
                  <div>Frequency Range: <strong className="font-mono">{uploadResult.frequency_range}</strong></div>
                  <div>ID: <code className="text-xs">{uploadResult.measurement_id.slice(0, 8)}...</code></div>
                </div>
                {uploadResult.validation_warnings.length > 0 && (
                  <div className="mt-3 p-3 rounded-lg bg-(--status-warning-bg) border border-(--status-warning-border)">
                    <p className="text-xs font-medium text-(--status-warning) mb-1">Warnings:</p>
                    <ul className="text-xs text-(--status-warning) list-disc list-inside opacity-90">
                      {uploadResult.validation_warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="alert alert-critical animate-fade-in-up">
              <XCircle size={20} className="shrink-0 mt-0.5" />
              <div>
                <h4 className="alert-title">Upload Failed</h4>
                <p className="alert-description">{uploadError}</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Configuration Panel */}
        <div className="space-y-5 animate-fade-in-up stagger-2">
          <GlassCard hover={false}>
            <h3 className="font-semibold text-(--text-primary) mb-5">Upload Settings</h3>

            <div className="space-y-4">
              {/* Transformer Selector */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-(--text-secondary)">
                  Transformer <span className="text-(--status-critical)">*</span>
                </label>
                <select
                  value={selectedTransformerId}
                  onChange={(e) => setSelectedTransformerId(e.target.value)}
                  className="input select"
                >
                  <option value="">Select transformer...</option>
                  {transformers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} {t.substation ? `(${t.substation})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Winding Config */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-(--text-secondary)">
                  Winding Configuration
                </label>
                <select
                  value={windingConfig}
                  onChange={(e) => setWindingConfig(e.target.value)}
                  className="input select"
                >
                  {WINDING_CONFIGS.map((wc) => (
                    <option key={wc} value={wc}>
                      {wc}
                    </option>
                  ))}
                </select>
              </div>

              {/* Date */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-(--text-secondary)">
                  Measurement Date
                </label>
                <input
                  type="datetime-local"
                  value={measurementDate}
                  onChange={(e) => setMeasurementDate(e.target.value)}
                  className="input"
                />
              </div>

              {/* Temperature */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-(--text-secondary)">
                  Temperature (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  placeholder="e.g. 25.0"
                  className="input font-mono"
                />
              </div>

              {/* Notes */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-(--text-secondary)">
                  Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  placeholder="Optional notes..."
                  className="input min-h-20 resize-y"
                />
              </div>

              {/* Upload Button */}
              <Button
                fullWidth
                disabled={!canUpload}
                onClick={handleUpload}
                loading={uploadStatus === 'uploading'}
                icon={uploadStatus !== 'uploading' ? <Upload size={16} /> : undefined}
              >
                {uploadStatus === 'uploading' ? 'Processing...' : 'Upload & Parse'}
              </Button>
            </div>
          </GlassCard>

          {/* Supported Formats */}
          <GlassCard hover={false}>
            <h3 className="font-semibold text-(--text-primary) mb-4">Supported Formats</h3>
            <div className="space-y-2.5">
              {[
                { vendor: 'Omicron', ext: '.fra, .csv, .xml', color: 'var(--teal-600)' },
                { vendor: 'Megger FRAX', ext: '.frax, .csv, .xml', color: 'var(--status-info)' },
                { vendor: 'Doble', ext: '.m4000, .csv', color: 'var(--status-warning)' },
                { vendor: 'Generic', ext: '.csv, .txt, .xml', color: 'var(--text-muted)' },
              ].map((v) => (
                <div key={v.vendor} className="flex items-center justify-between text-sm">
                  <span className="font-medium" style={{ color: v.color }}>{v.vendor}</span>
                  <span className="text-(--text-muted) font-mono text-xs">{v.ext}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Import History Table */}
      <div className="animate-fade-in-up stagger-3">
        <GlassCard padding="none" hover={false}>
          <div className="px-6 py-5 border-b border-(--card-border) flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-(--text-primary)">Import History</h3>
              <p className="text-xs text-(--text-muted) mt-0.5">
                {importHistory.length} import{importHistory.length !== 1 ? 's' : ''} recorded
              </p>
            </div>
            <button
              onClick={loadHistory}
              disabled={loadingHistory}
              className="btn btn-ghost text-(--text-muted) hover:text-(--teal-600)"
            >
              <RefreshCw size={14} className={loadingHistory ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {importHistory.length === 0 ? (
            <div className="empty-state">
              <Upload size={48} className="empty-state-icon" />
              <h3 className="empty-state-title">No Imports Yet</h3>
              <p className="empty-state-description">
                Upload a file to get started. Your import history will appear here.
              </p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Filename</th>
                    <th>Vendor</th>
                    <th>Points</th>
                    <th>Freq Range</th>
                    <th>Size</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {importHistory.map((record) => (
                    <tr key={record.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          {statusIcon(record.status)}
                          <span
                            className={`text-xs font-medium capitalize ${
                              record.status === 'success'
                                ? 'text-(--status-success)'
                                : record.status === 'failed'
                                ? 'text-(--status-critical)'
                                : 'text-(--text-muted)'
                            }`}
                          >
                            {record.status}
                          </span>
                        </div>
                      </td>
                      <td className="font-medium text-(--text-primary) max-w-50 truncate">
                        {record.original_filename}
                      </td>
                      <td className="text-(--text-muted)">
                        {record.detected_vendor || '—'}
                      </td>
                      <td className="font-mono text-(--text-muted)">
                        {record.data_points?.toLocaleString() ?? '—'}
                      </td>
                      <td className="font-mono text-xs text-(--text-muted)">
                        {record.frequency_range || '—'}
                      </td>
                      <td className="font-mono text-(--text-muted)">
                        {formatFileSize(record.file_size_bytes)}
                      </td>
                      <td className="text-xs text-(--text-muted)">
                        {new Date(record.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
