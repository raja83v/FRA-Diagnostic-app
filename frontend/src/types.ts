/**
 * TypeScript type definitions matching the backend Pydantic schemas.
 */

// === Enums ===

export type TransformerCriticality = 'critical' | 'important' | 'standard';

export type WindingConfig =
  | 'HV-LV' | 'HV-TV' | 'LV-TV'
  | 'HV-GND' | 'LV-GND' | 'TV-GND'
  | 'HV-Open' | 'LV-Open' | 'Other';

export type FaultType =
  | 'axial_displacement' | 'radial_deformation' | 'core_grounding'
  | 'winding_short_circuit' | 'loose_clamping' | 'moisture_ingress' | 'healthy';

export type UrgencyLevel = 'urgent' | 'high' | 'medium' | 'low' | 'info';

export type RecommendationStatus =
  | 'pending' | 'in_progress' | 'completed' | 'deferred' | 'cancelled';

// === Models ===

export interface Transformer {
  id: string;
  name: string;
  location: string | null;
  substation: string | null;
  voltage_rating_kv: number | null;
  power_rating_mva: number | null;
  manufacturer: string | null;
  year_of_manufacture: number | null;
  serial_number: string | null;
  criticality: TransformerCriticality;
  baseline_measurement_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  measurement_count: number;
}

export interface TransformerCreate {
  name: string;
  location?: string;
  substation?: string;
  voltage_rating_kv?: number;
  power_rating_mva?: number;
  manufacturer?: string;
  year_of_manufacture?: number;
  serial_number?: string;
  criticality?: TransformerCriticality;
  notes?: string;
}

export interface MeasurementSummary {
  id: string;
  transformer_id: string;
  measurement_date: string;
  winding_config: string;
  vendor: string | null;
  original_filename: string | null;
  data_points: number;
  created_at: string;
}

export interface Measurement {
  id: string;
  transformer_id: string;
  measurement_date: string;
  winding_config: string;
  frequency_hz: number[];
  magnitude_db: number[];
  phase_degrees: number[] | null;
  vendor: string | null;
  original_format: string | null;
  original_filename: string | null;
  metadata_json: Record<string, unknown> | null;
  temperature_celsius: number | null;
  notes: string | null;
  created_at: string;
}

export interface AnalysisResult {
  id: string;
  measurement_id: string;
  fault_type: FaultType;
  probability_score: number;
  confidence_level: number;
  all_probabilities: Record<FaultType, number> | null;
  health_score: number | null;
  model_version: string | null;
  model_type: string | null;
  feature_importance: Record<string, number> | null;
  created_at: string;
}

export interface Recommendation {
  id: string;
  fault_analysis_id: string;
  transformer_id: string;
  urgency: UrgencyLevel;
  title: string;
  action_description: string;
  fault_type: string | null;
  due_date: string | null;
  assigned_to: string | null;
  status: RecommendationStatus;
  status_notes: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  measurement_id: string;
  transformer_id: string;
  filename: string;
  vendor_detected: string | null;
  data_points: number;
  frequency_range: string;
  validation_warnings: string[];
  message: string;
}

export interface ImportHistoryRecord {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  status: 'pending' | 'parsing' | 'validating' | 'normalizing' | 'success' | 'partial' | 'failed';
  measurement_id: string | null;
  transformer_id: string | null;
  detected_vendor: string | null;
  detected_format: string | null;
  parser_used: string | null;
  data_points: number | null;
  frequency_range: string | null;
  warnings_json: string[] | null;
  errors_json: string[] | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}
