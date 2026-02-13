/**
 * API client for the FRA Diagnostic backend.
 * All requests go through the Vite proxy (/api -> localhost:8000).
 */
import axios from 'axios';
import type {
  Transformer,
  TransformerCreate,
  MeasurementSummary,
  Measurement,
  AnalysisResult,
  Recommendation,
  UploadResponse,
  ImportHistoryRecord,
} from './types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// ── Transformers ──

export const getTransformers = async (params?: {
  search?: string;
  criticality?: string;
}): Promise<Transformer[]> => {
  const { data } = await api.get('/transformers/', { params });
  return data;
};

export const getTransformer = async (id: string): Promise<Transformer> => {
  const { data } = await api.get(`/transformers/${id}`);
  return data;
};

export const createTransformer = async (
  body: TransformerCreate
): Promise<Transformer> => {
  const { data } = await api.post('/transformers/', body);
  return data;
};

export const updateTransformer = async (
  id: string,
  body: Partial<TransformerCreate>
): Promise<Transformer> => {
  const { data } = await api.put(`/transformers/${id}`, body);
  return data;
};

export const deleteTransformer = async (id: string): Promise<void> => {
  await api.delete(`/transformers/${id}`);
};

// ── Measurements ──

export const getMeasurements = async (params?: {
  transformer_id?: string;
  vendor?: string;
}): Promise<MeasurementSummary[]> => {
  const { data } = await api.get('/measurements/', { params });
  return data;
};

export const getMeasurement = async (id: string): Promise<Measurement> => {
  const { data } = await api.get(`/measurements/${id}`);
  return data;
};

export const getTransformerMeasurements = async (
  transformerId: string
): Promise<MeasurementSummary[]> => {
  const { data } = await api.get(`/measurements/transformer/${transformerId}`);
  return data;
};

// ── Analysis ──

export const runAnalysis = async (
  measurementId: string
): Promise<AnalysisResult> => {
  const { data } = await api.post(`/analysis/run/${measurementId}`);
  return data;
};

export const getAnalysisResults = async (
  analysisId: string
): Promise<AnalysisResult> => {
  const { data } = await api.get(`/analysis/${analysisId}/results`);
  return data;
};

export const listAnalyses = async (params?: {
  measurement_id?: string;
}): Promise<AnalysisResult[]> => {
  const { data } = await api.get('/analysis/', { params });
  return data;
};

// ── Recommendations ──

export const getRecommendations = async (params?: {
  transformer_id?: string;
  status?: string;
  urgency?: string;
}): Promise<Recommendation[]> => {
  const { data } = await api.get('/recommendations/', { params });
  return data;
};

export const getTransformerRecommendations = async (
  transformerId: string
): Promise<Recommendation[]> => {
  const { data } = await api.get(`/recommendations/transformer/${transformerId}`);
  return data;
};

export const updateRecommendationStatus = async (
  id: string,
  body: { status: string; status_notes?: string; assigned_to?: string }
): Promise<Recommendation> => {
  const { data } = await api.put(`/recommendations/${id}/status`, body);
  return data;
};

// ── File Upload ──

export const uploadFRAFile = async (params: {
  file: File;
  transformer_id: string;
  winding_config?: string;
  measurement_date?: string;
  temperature_celsius?: number;
  notes?: string;
}): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('transformer_id', params.transformer_id);
  if (params.winding_config) formData.append('winding_config', params.winding_config);
  if (params.measurement_date) formData.append('measurement_date', params.measurement_date);
  if (params.temperature_celsius !== undefined)
    formData.append('temperature_celsius', String(params.temperature_celsius));
  if (params.notes) formData.append('notes', params.notes);

  const { data } = await api.post('/measurements/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

// ── Import History ──

export const getImportHistory = async (params?: {
  status?: string;
  transformer_id?: string;
}): Promise<ImportHistoryRecord[]> => {
  const { data } = await api.get('/imports/', { params });
  return data;
};

export const getImportStats = async (): Promise<{
  total_imports: number;
  successful: number;
  failed: number;
  partial: number;
}> => {
  const { data } = await api.get('/imports/stats');
  return data;
};

export default api;
