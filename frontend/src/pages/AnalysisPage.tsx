/**
 * Analysis Page — ML-powered transformer fault analysis with real-time visualization.
 * Connects to XGBoost inference backend, displays health scores, fault probabilities,
 * feature importance, and FRA curve overlays.
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import Plot from 'react-plotly.js';
import {
  Brain,
  AlertCircle,
  Zap,
  Activity,
  Play,
  ChevronDown,
  Shield,
  BarChart3,
  TrendingDown,
  Clock,
  CheckCircle2,
  Info,
} from 'lucide-react';
import {
  getTransformers,
  getTransformerMeasurements,
  getMeasurement,
  runAnalysis,
  listAnalyses,
  downloadAnalysesExcel,
} from '../api';
import type {
  Transformer,
  MeasurementSummary,
  Measurement,
  AnalysisResult,
  FaultType,
} from '../types';
import { GlassCard, Button, LoadingOverlay, CriticalityBadge } from '../components/ui';

/* ── Fault metadata ── */
const FAULT_META: Record<
  string,
  { label: string; color: string; bg: string; freqRange: string; icon: typeof Zap }
> = {
  healthy: {
    label: 'Healthy',
    color: 'var(--status-success)',
    bg: 'var(--status-success-bg)',
    freqRange: '—',
    icon: CheckCircle2,
  },
  axial_displacement: {
    label: 'Axial Displacement',
    color: 'var(--status-critical)',
    bg: 'var(--status-critical-bg)',
    freqRange: '2–20 kHz',
    icon: AlertCircle,
  },
  radial_deformation: {
    label: 'Radial Deformation',
    color: '#D97706',
    bg: 'var(--status-warning-bg)',
    freqRange: '< 2 kHz',
    icon: AlertCircle,
  },
  core_grounding: {
    label: 'Core Grounding',
    color: '#D97706',
    bg: 'var(--status-warning-bg)',
    freqRange: '< 1 kHz',
    icon: Zap,
  },
  winding_short_circuit: {
    label: 'Winding Short Circuit',
    color: 'var(--status-critical)',
    bg: 'var(--status-critical-bg)',
    freqRange: '> 100 kHz',
    icon: Zap,
  },
  loose_clamping: {
    label: 'Loose Clamping',
    color: 'var(--status-info)',
    bg: 'var(--status-info-bg)',
    freqRange: 'Broadband',
    icon: Activity,
  },
  moisture_ingress: {
    label: 'Moisture Ingress',
    color: 'var(--status-info)',
    bg: 'var(--status-info-bg)',
    freqRange: 'General',
    icon: TrendingDown,
  },
};

function faultLabel(type: string): string {
  return FAULT_META[type]?.label ?? type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function faultColor(type: string): string {
  return FAULT_META[type]?.color ?? '#64748B';
}

/* ── Health score ring colour ── */
function healthColor(score: number): string {
  if (score >= 80) return 'var(--teal-500)';
  if (score >= 60) return '#22C55E';
  if (score >= 40) return '#D97706';
  if (score >= 20) return '#EA580C';
  return '#DC2626';
}

export default function AnalysisPage() {
  /* ── Selection state ── */
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [selectedTransformerId, setSelectedTransformerId] = useState('');
  const [measurements, setMeasurements] = useState<MeasurementSummary[]>([]);
  const [selectedMeasurementId, setSelectedMeasurementId] = useState('');
  const [measurement, setMeasurement] = useState<Measurement | null>(null);

  /* ── Analysis state ── */
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState('');

  /* ── Loading ── */
  const [loadingPage, setLoadingPage] = useState(true);

  /* ── Load transformers ── */
  useEffect(() => {
    getTransformers()
      .then(setTransformers)
      .catch(console.error)
      .finally(() => setLoadingPage(false));
  }, []);

  /* ── Load measurements when transformer changes ── */
  useEffect(() => {
    if (!selectedTransformerId) {
      setMeasurements([]);
      setSelectedMeasurementId('');
      setMeasurement(null);
      return;
    }
    getTransformerMeasurements(selectedTransformerId)
      .then((m) => {
        setMeasurements(m);
        if (m.length > 0) {
          setSelectedMeasurementId(m[0].id);
        } else {
          setSelectedMeasurementId('');
        }
      })
      .catch(console.error);
  }, [selectedTransformerId]);

  /* ── Load full measurement data ── */
  useEffect(() => {
    if (!selectedMeasurementId) {
      setMeasurement(null);
      return;
    }
    getMeasurement(selectedMeasurementId).then(setMeasurement).catch(console.error);
    // Load analysis history for this measurement
    listAnalyses({ measurement_id: selectedMeasurementId })
      .then(setAnalysisHistory)
      .catch(console.error);
  }, [selectedMeasurementId]);

  /* ── Run analysis ── */
  const handleRunAnalysis = useCallback(async () => {
    if (!selectedMeasurementId) return;
    setAnalyzing(true);
    setError('');
    try {
      const result = await runAnalysis(selectedMeasurementId);
      setAnalysisResult(result);
      setAnalysisHistory((prev) => [result, ...prev]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed';
      setError(msg);
    } finally {
      setAnalyzing(false);
    }
  }, [selectedMeasurementId]);

  /* ── Selected transformer object ── */
  const selectedTransformer = useMemo(
    () => transformers.find((t) => t.id === selectedTransformerId) ?? null,
    [transformers, selectedTransformerId]
  );

  if (loadingPage) return <LoadingOverlay message="Loading analysis page..." />;

  return (
    <div className="space-y-6">
      {/* ── Page Header ── */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">
          Fault Analysis
        </h1>
        <p className="text-(--text-muted) mt-1">
          ML-powered transformer health assessment and fault detection
        </p>
      </div>

      {/* ── Selection Panel ── */}
      <SelectorPanel
        transformers={transformers}
        selectedTransformerId={selectedTransformerId}
        onTransformerChange={setSelectedTransformerId}
        measurements={measurements}
        selectedMeasurementId={selectedMeasurementId}
        onMeasurementChange={setSelectedMeasurementId}
        onRunAnalysis={handleRunAnalysis}
        analyzing={analyzing}
        transformer={selectedTransformer}
      />

      {error && (
        <div className="alert alert-critical animate-fade-in">
          <AlertCircle size={18} className="shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* ── Analysis Results ── */}
      {analysisResult && (
        <>
          {/* Top results row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-fade-in-up stagger-1">
            <HealthScoreCard score={analysisResult.health_score ?? 0} />
            <FaultTypeCard result={analysisResult} />
            <ModelInfoCard result={analysisResult} />
          </div>

          {/* Probability bars + Feature importance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 animate-fade-in-up stagger-2">
            <FaultProbabilityChart result={analysisResult} />
            <FeatureImportanceChart result={analysisResult} />
          </div>

          {/* FRA Curve with analysis fault bands */}
          {measurement && (
            <div className="animate-fade-in-up stagger-3">
              <FRACurveWithAnalysis
                measurement={measurement}
                faultType={analysisResult.fault_type}
              />
            </div>
          )}
        </>
      )}

      {/* ── No result prompt ── */}
      {!analysisResult && !analyzing && selectedMeasurementId && (
        <AnalysisPrompt hasHistory={analysisHistory.length > 0} />
      )}

      {/* ── Analysis in progress ── */}
      {analyzing && (
        <GlassCard className="text-center py-16 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-(--teal-50) mb-6">
            <Brain size={36} className="text-(--teal-600) animate-pulse" />
          </div>
          <h3 className="text-xl font-semibold font-display text-(--text-primary) mb-2">
            Running XGBoost Inference…
          </h3>
          <p className="text-sm text-(--text-muted)">
            Extracting features and classifying fault patterns
          </p>
          <div className="mt-6 mx-auto w-48 h-1.5 rounded-full bg-(--bg-secondary) overflow-hidden">
            <div className="h-full rounded-full bg-(--gradient-teal) animate-shimmer" />
          </div>
        </GlassCard>
      )}

      {/* ── Analysis History ── */}
      {analysisHistory.length > 0 && (
        <AnalysisHistoryTable
          history={analysisHistory}
          onSelect={setAnalysisResult}
          activeId={analysisResult?.id}
        />
      )}

      {/* ── No transformer selected ── */}
      {!selectedTransformerId && (
        <GlassCard className="text-center py-16 animate-fade-in-up stagger-1">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-(--bg-secondary) border border-(--card-border) flex items-center justify-center mb-5">
            <Brain size={40} className="text-(--text-muted)" />
          </div>
          <h3 className="text-xl font-semibold font-display text-(--text-primary) mb-3">
            Select a Transformer to Analyze
          </h3>
          <p className="text-sm text-(--text-muted) max-w-md mx-auto">
            Choose a transformer and measurement from the panel above, then run the
            XGBoost ML model to detect faults and generate health scores.
          </p>
        </GlassCard>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   SUB-COMPONENTS
   ═══════════════════════════════════════════════════════════════════ */

/* ── Selector Panel ── */
function SelectorPanel({
  transformers,
  selectedTransformerId,
  onTransformerChange,
  measurements,
  selectedMeasurementId,
  onMeasurementChange,
  onRunAnalysis,
  analyzing,
  transformer,
}: {
  transformers: Transformer[];
  selectedTransformerId: string;
  onTransformerChange: (id: string) => void;
  measurements: MeasurementSummary[];
  selectedMeasurementId: string;
  onMeasurementChange: (id: string) => void;
  onRunAnalysis: () => void;
  analyzing: boolean;
  transformer: Transformer | null;
}) {
  return (
    <GlassCard hover={false} className="animate-fade-in-up">
      <div className="flex flex-col lg:flex-row items-start lg:items-end gap-4">
        {/* Transformer selector */}
        <div className="flex-1 w-full lg:w-auto">
          <label className="block text-xs font-semibold uppercase tracking-wider text-(--text-muted) mb-2">
            Transformer
          </label>
          <div className="relative">
            <select
              className="input w-full pr-10 appearance-none cursor-pointer"
              value={selectedTransformerId}
              onChange={(e) => onTransformerChange(e.target.value)}
            >
              <option value="">Select transformer…</option>
              {transformers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} — {t.substation || t.location || 'No location'}{' '}
                  ({t.measurement_count} measurements)
                </option>
              ))}
            </select>
            <ChevronDown
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-(--text-muted) pointer-events-none"
            />
          </div>
        </div>

        {/* Measurement selector */}
        <div className="flex-1 w-full lg:w-auto">
          <label className="block text-xs font-semibold uppercase tracking-wider text-(--text-muted) mb-2">
            Measurement
          </label>
          <div className="relative">
            <select
              className="input w-full pr-10 appearance-none cursor-pointer"
              value={selectedMeasurementId}
              onChange={(e) => onMeasurementChange(e.target.value)}
              disabled={!selectedTransformerId || measurements.length === 0}
            >
              {measurements.length === 0 && (
                <option value="">
                  {selectedTransformerId ? 'No measurements available' : 'Select transformer first'}
                </option>
              )}
              {measurements.map((m) => (
                <option key={m.id} value={m.id}>
                  {new Date(m.measurement_date).toLocaleDateString()} — {m.winding_config}
                  {m.vendor ? ` (${m.vendor})` : ''} — {m.data_points} pts
                </option>
              ))}
            </select>
            <ChevronDown
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-(--text-muted) pointer-events-none"
            />
          </div>
        </div>

        {/* Run button */}
        <div className="w-full lg:w-auto">
          <Button
            onClick={onRunAnalysis}
            disabled={!selectedMeasurementId || analyzing}
            loading={analyzing}
            icon={<Play size={16} />}
            size="lg"
          >
            {analyzing ? 'Analyzing…' : 'Run Analysis'}
          </Button>
        </div>
      </div>

      {/* Transformer quick info */}
      {transformer && (
        <div className="mt-4 pt-4 border-t border-(--card-border) flex flex-wrap items-center gap-4 text-xs text-(--text-muted)">
          <CriticalityBadge level={transformer.criticality} />
          {transformer.voltage_rating_kv && (
            <span className="font-mono">{transformer.voltage_rating_kv} kV</span>
          )}
          {transformer.power_rating_mva && (
            <span className="font-mono">{transformer.power_rating_mva} MVA</span>
          )}
          {transformer.manufacturer && <span>{transformer.manufacturer}</span>}
          <span className="ml-auto">
            <Link
              to={`/transformers/${transformer.id}`}
              className="text-(--teal-600) hover:text-(--teal-700) font-medium"
            >
              View Details →
            </Link>
          </span>
        </div>
      )}
    </GlassCard>
  );
}

/* ── Health Score Card ── */
function HealthScoreCard({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 52;
  const offset = circumference - (score / 100) * circumference;
  const color = healthColor(score);

  return (
    <GlassCard className="text-center">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-(--text-muted) mb-4 flex items-center justify-center gap-2">
        <Shield size={16} className="text-(--teal-600)" />
        Health Score
      </h3>
      <div className="relative inline-flex items-center justify-center">
        <svg width="140" height="140" className="transform -rotate-90">
          <circle
            cx="70"
            cy="70"
            r="52"
            fill="none"
            stroke="var(--bg-secondary)"
            strokeWidth="10"
          />
          <circle
            cx="70"
            cy="70"
            r="52"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-4xl font-bold font-display"
            style={{ color }}
          >
            {Math.round(score)}
          </span>
          <span className="text-xs text-(--text-muted) mt-0.5">/100</span>
        </div>
      </div>
      <p className="mt-3 text-xs text-(--text-muted)">
        {score >= 80
          ? 'Good condition'
          : score >= 60
            ? 'Moderate — monitor closely'
            : score >= 40
              ? 'Degraded — schedule inspection'
              : 'Critical — immediate action needed'}
      </p>
    </GlassCard>
  );
}

/* ── Detected Fault Card ── */
function FaultTypeCard({ result }: { result: AnalysisResult }) {
  const meta = FAULT_META[result.fault_type];
  const Icon = meta?.icon ?? AlertCircle;

  return (
    <GlassCard className="text-center">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-(--text-muted) mb-4 flex items-center justify-center gap-2">
        <Zap size={16} className="text-(--teal-600)" />
        Detected Fault
      </h3>
      <div
        className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-3"
        style={{ backgroundColor: meta?.bg ?? '#F1F5F9' }}
      >
        <Icon size={32} style={{ color: faultColor(result.fault_type) }} />
      </div>
      <p
        className="text-xl font-bold font-display mb-1"
        style={{ color: faultColor(result.fault_type) }}
      >
        {faultLabel(result.fault_type)}
      </p>
      <p className="text-sm text-(--text-muted)">
        {(result.probability_score * 100).toFixed(1)}% probability
      </p>
      <div className="mt-3 flex items-center justify-center gap-2 text-xs text-(--text-muted)">
        <Info size={12} />
        Confidence: {((result.confidence_level ?? 0) * 100).toFixed(0)}%
      </div>
    </GlassCard>
  );
}

/* ── Model Info Card ── */
function ModelInfoCard({ result }: { result: AnalysisResult }) {
  return (
    <GlassCard className="text-center">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-(--text-muted) mb-4 flex items-center justify-center gap-2">
        <Brain size={16} className="text-(--teal-600)" />
        Model Info
      </h3>
      <div className="space-y-3">
        <div>
          <p className="text-xs text-(--text-muted) mb-0.5">Model</p>
          <p className="font-mono text-sm text-(--text-primary) font-medium">
            {result.model_version ?? '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-(--text-muted) mb-0.5">Type</p>
          <p className="font-mono text-sm text-(--text-primary)">
            {result.model_type ?? '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-(--text-muted) mb-0.5">Analyzed</p>
          <p className="font-mono text-sm text-(--text-secondary)">
            {new Date(result.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </GlassCard>
  );
}

/* ── Fault Probability Horizontal Bar Chart ── */
function FaultProbabilityChart({ result }: { result: AnalysisResult }) {
  const probs = result.all_probabilities;
  if (!probs) return null;

  // Sort by probability descending
  const sorted = Object.entries(probs).sort(([, a], [, b]) => b - a);

  return (
    <GlassCard padding="none" hover={false}>
      <div className="px-6 py-5 border-b border-(--card-border)">
        <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
          <BarChart3 size={20} className="text-(--teal-600)" />
          Fault Probabilities
        </h2>
        <p className="text-xs text-(--text-muted) mt-0.5">
          Per-class probability scores from XGBoost classifier
        </p>
      </div>
      <div className="p-6 space-y-3">
        {sorted.map(([fault, prob]) => (
          <div key={fault}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-(--text-secondary)">
                {faultLabel(fault)}
              </span>
              <span
                className="text-sm font-mono font-semibold"
                style={{ color: faultColor(fault) }}
              >
                {(prob * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-2.5 rounded-full bg-(--bg-secondary) overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${Math.max(prob * 100, 0.5)}%`,
                  backgroundColor: faultColor(fault),
                  opacity: fault === result.fault_type ? 1 : 0.6,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

/* ── Feature Importance Bar Chart (Plotly) ── */
function FeatureImportanceChart({ result }: { result: AnalysisResult }) {
  const features = result.feature_importance;
  if (!features) return null;

  // Top 15 features sorted by importance
  const sorted = Object.entries(features)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 15);

  const labels = sorted.map(([name]) =>
    name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
  );
  const values = sorted.map(([, v]) => v);

  return (
    <GlassCard padding="none" hover={false}>
      <div className="px-6 py-5 border-b border-(--card-border)">
        <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
          <Activity size={20} className="text-(--teal-600)" />
          Feature Importance
        </h2>
        <p className="text-xs text-(--text-muted) mt-0.5">
          Top features driving the classification decision
        </p>
      </div>
      <div className="p-4">
        <Plot
          data={[
            {
              type: 'bar',
              orientation: 'h',
              y: [...labels].reverse(),
              x: [...values].reverse(),
              marker: {
                color: [...values].reverse().map((_, i, arr) => {
                  const t = 1 - i / (arr.length - 1 || 1);
                  return `rgba(13, 148, 136, ${0.4 + t * 0.6})`;
                }),
                line: { color: 'rgba(13, 148, 136, 0.8)', width: 1 },
              },
              hovertemplate: '%{y}: %{x:.4f}<extra></extra>',
            },
          ]}
          layout={{
            height: 420,
            margin: { t: 10, r: 30, b: 40, l: 140 },
            xaxis: {
              title: { text: 'Importance', font: { color: '#334155', size: 12 } },
              gridcolor: 'rgba(226, 232, 240, 0.8)',
              linecolor: '#E2E8F0',
              tickfont: { color: '#64748B', size: 10, family: 'JetBrains Mono' },
              zerolinecolor: '#E2E8F0',
            },
            yaxis: {
              tickfont: { color: '#334155', size: 10, family: 'Inter' },
              automargin: true,
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { family: 'Inter, sans-serif', size: 11, color: '#334155' },
            bargap: 0.15,
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>
    </GlassCard>
  );
}

/* ── FRA Curve with Fault Band Highlighting ── */
function FRACurveWithAnalysis({
  measurement,
  faultType,
}: {
  measurement: Measurement;
  faultType: FaultType | string;
}) {
  const [showPhase, setShowPhase] = useState(false);
  const hasPhase =
    measurement.phase_degrees &&
    measurement.phase_degrees.length > 0 &&
    measurement.phase_degrees.some((v) => v !== 0);

  /* Fault frequency band shapes for highlighting */
  const shapes: Partial<Plotly.Shape>[] = [];
  if (faultType === 'axial_displacement') {
    shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: 2000,
      x1: 20000,
      y0: 0,
      y1: 1,
      fillcolor: 'rgba(220, 38, 38, 0.07)',
      line: { color: 'rgba(220, 38, 38, 0.3)', width: 1, dash: 'dot' },
    });
  } else if (faultType === 'radial_deformation') {
    shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: 20,
      x1: 2000,
      y0: 0,
      y1: 1,
      fillcolor: 'rgba(217, 119, 6, 0.07)',
      line: { color: 'rgba(217, 119, 6, 0.3)', width: 1, dash: 'dot' },
    });
  } else if (faultType === 'core_grounding') {
    shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: 20,
      x1: 1000,
      y0: 0,
      y1: 1,
      fillcolor: 'rgba(217, 119, 6, 0.07)',
      line: { color: 'rgba(217, 119, 6, 0.3)', width: 1, dash: 'dot' },
    });
  } else if (faultType === 'winding_short_circuit') {
    shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: 100000,
      x1: 2000000,
      y0: 0,
      y1: 1,
      fillcolor: 'rgba(220, 38, 38, 0.07)',
      line: { color: 'rgba(220, 38, 38, 0.3)', width: 1, dash: 'dot' },
    });
  }

  const traces: Plotly.Data[] = [
    {
      x: measurement.frequency_hz,
      y: measurement.magnitude_db,
      type: 'scatter',
      mode: 'lines',
      name: 'Magnitude (dB)',
      line: { color: '#0D9488', width: 2, shape: 'spline' },
      fill: 'tozeroy',
      fillcolor: 'rgba(20, 184, 166, 0.08)',
      yaxis: 'y',
    },
  ];

  if (showPhase && hasPhase) {
    traces.push({
      x: measurement.frequency_hz,
      y: measurement.phase_degrees!,
      type: 'scatter',
      mode: 'lines',
      name: 'Phase (°)',
      line: { color: '#8B5CF6', width: 1.5, shape: 'spline', dash: 'dot' },
      yaxis: 'y2',
    });
  }

  return (
    <GlassCard padding="none" hover={false}>
      <div className="px-6 py-5 border-b border-(--card-border) flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
            <Activity size={20} className="text-(--teal-600)" />
            FRA Curve — Analyzed Measurement
          </h2>
          <p className="text-xs text-(--text-muted) mt-0.5">
            {faultType !== 'healthy' && (
              <span style={{ color: faultColor(faultType) }}>
                Highlighted: {faultLabel(faultType)} frequency band
              </span>
            )}
            {faultType === 'healthy' && 'No anomalous frequency bands detected'}
          </p>
        </div>
        {hasPhase && (
          <Button
            variant={showPhase ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowPhase(!showPhase)}
          >
            {showPhase ? 'Hide Phase' : 'Show Phase'}
          </Button>
        )}
      </div>
      <div className="p-4">
        <Plot
          data={traces}
          layout={{
            xaxis: {
              title: { text: 'Frequency (Hz)', font: { color: '#334155', size: 12 } },
              type: 'log',
              showgrid: true,
              gridcolor: 'rgba(226, 232, 240, 0.8)',
              linecolor: '#E2E8F0',
              tickfont: { color: '#64748B', size: 11, family: 'JetBrains Mono' },
              zerolinecolor: '#E2E8F0',
            },
            yaxis: {
              title: { text: 'Magnitude (dB)', font: { color: '#0D9488', size: 12 } },
              showgrid: true,
              gridcolor: 'rgba(226, 232, 240, 0.8)',
              linecolor: '#E2E8F0',
              tickfont: { color: '#64748B', size: 11, family: 'JetBrains Mono' },
              zerolinecolor: '#E2E8F0',
            },
            yaxis2: showPhase
              ? {
                  title: { text: 'Phase (°)', font: { color: '#8B5CF6', size: 12 } },
                  overlaying: 'y',
                  side: 'right',
                  showgrid: false,
                  tickfont: { color: '#8B5CF6', size: 11, family: 'JetBrains Mono' },
                }
              : undefined,
            margin: { t: 20, r: showPhase ? 70 : 30, b: 60, l: 70 },
            height: 420,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { family: 'Inter, sans-serif', size: 12, color: '#334155' },
            hovermode: 'x unified',
            hoverlabel: {
              bgcolor: '#FFFFFF',
              bordercolor: '#0D9488',
              font: { color: '#0F172A', family: 'JetBrains Mono' },
            },
            legend: {
              x: 0,
              y: 1.12,
              orientation: 'h',
              font: { size: 11, color: '#64748B' },
            },
            shapes: shapes as Plotly.Layout['shapes'],
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
            displaylogo: false,
          }}
          style={{ width: '100%' }}
        />
      </div>
      <div className="px-6 py-3 border-t border-(--card-border) flex flex-wrap items-center gap-4 text-xs">
        <span className="font-mono text-(--teal-600)">{measurement.winding_config}</span>
        <span className="w-1 h-1 rounded-full bg-(--card-border)" />
        <span className="text-(--text-muted)">
          {new Date(measurement.measurement_date).toLocaleDateString()}
        </span>
        <span className="w-1 h-1 rounded-full bg-(--card-border)" />
        <span className="font-mono text-(--text-muted)">
          {measurement.frequency_hz.length.toLocaleString()} data points
        </span>
        <span className="w-1 h-1 rounded-full bg-(--card-border)" />
        <span className="text-(--text-muted)">
          Vendor: <span className="text-(--text-secondary)">{measurement.vendor ?? '—'}</span>
        </span>
      </div>
    </GlassCard>
  );
}

/* ── Analysis History Table ── */
function AnalysisHistoryTable({
  history,
  onSelect,
  activeId,
}: {
  history: AnalysisResult[];
  onSelect: (r: AnalysisResult) => void;
  activeId?: string;
}) {
  return (
    <div className="animate-fade-in-up stagger-4">
      <GlassCard padding="none" hover={false}>
        <div className="px-6 py-5 border-b border-(--card-border) flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
              <Clock size={20} className="text-(--teal-600)" />
              Analysis History
            </h2>
            <p className="text-xs text-(--text-muted) mt-0.5">
              {history.length} analysis run{history.length !== 1 ? 's' : ''} for this measurement
            </p>
          </div>
          {history.length > 0 && (
            <button
              onClick={() => downloadAnalysesExcel()}
              className="btn btn-secondary text-xs flex items-center gap-1.5"
            >
              Export Excel
            </button>
          )}
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Fault Type</th>
                <th>Probability</th>
                <th>Health Score</th>
                <th>Model</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((a) => (
                <tr
                  key={a.id}
                  className={activeId === a.id ? 'bg-(--teal-50)' : ''}
                >
                  <td className="font-mono text-(--text-secondary) text-sm">
                    {new Date(a.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                      style={{
                        backgroundColor: FAULT_META[a.fault_type]?.bg ?? '#F1F5F9',
                        color: faultColor(a.fault_type),
                      }}
                    >
                      {faultLabel(a.fault_type)}
                    </span>
                  </td>
                  <td className="font-mono text-sm" style={{ color: faultColor(a.fault_type) }}>
                    {(a.probability_score * 100).toFixed(1)}%
                  </td>
                  <td>
                    <span
                      className="font-mono text-sm font-semibold"
                      style={{ color: healthColor(a.health_score ?? 0) }}
                    >
                      {a.health_score != null ? Math.round(a.health_score) : '—'}
                    </span>
                  </td>
                  <td className="font-mono text-xs text-(--text-muted)">
                    {a.model_version ?? '—'}
                  </td>
                  <td>
                    <button
                      onClick={() => onSelect(a)}
                      className={`text-sm font-medium transition-colors ${
                        activeId === a.id
                          ? 'text-(--teal-600)'
                          : 'text-(--text-muted) hover:text-(--teal-600)'
                      }`}
                    >
                      {activeId === a.id ? '● Viewing' : 'View'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

/* ── Run Analysis Prompt ── */
function AnalysisPrompt({ hasHistory }: { hasHistory: boolean }) {
  return (
    <GlassCard className="text-center py-12 animate-fade-in-up stagger-1">
      <div className="w-16 h-16 mx-auto rounded-2xl bg-(--teal-50) flex items-center justify-center mb-5">
        <Play size={32} className="text-(--teal-600) ml-1" />
      </div>
      <h3 className="text-lg font-semibold font-display text-(--text-primary) mb-2">
        {hasHistory ? 'Run Another Analysis' : 'Ready to Analyze'}
      </h3>
      <p className="text-sm text-(--text-muted) max-w-md mx-auto">
        Click <strong>"Run Analysis"</strong> above to execute the XGBoost ML model
        on the selected measurement. The system will extract 49 features from the
        FRA curve and classify potential fault types.
      </p>
    </GlassCard>
  );
}
