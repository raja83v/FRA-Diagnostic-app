/**
 * Transformer detail page with enhanced FRA visualization:
 * - Phase overlay on secondary Y-axis
 * - Multi-curve comparison (select multiple measurements to overlay)
 * - Run analysis button per measurement
 */
import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, Upload, Calendar, FileText, Layers, Eye, EyeOff, Play, Download, FileSpreadsheet } from 'lucide-react';
import Plot from 'react-plotly.js';
import { getTransformer, getTransformerMeasurements, getMeasurement, downloadPdfReport, downloadMeasurementsExcel } from '../api';
import type { Transformer, MeasurementSummary, Measurement } from '../types';
import { GlassCard, CriticalityBadge, Button, LoadingOverlay } from '../components/ui';

/* Colour palette for multi-curve overlay */
const CURVE_COLORS = [
  '#0D9488', '#8B5CF6', '#D97706', '#2563EB', '#DC2626', '#059669', '#7C3AED', '#EA580C',
];

export default function TransformerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [transformer, setTransformer] = useState<Transformer | null>(null);
  const [measurements, setMeasurements] = useState<MeasurementSummary[]>([]);
  const [selectedMeasurement, setSelectedMeasurement] = useState<Measurement | null>(null);
  const [loading, setLoading] = useState(true);

  /* Multi-curve comparison state */
  const [comparisonIds, setComparisonIds] = useState<Set<string>>(new Set());
  const [comparisonData, setComparisonData] = useState<Map<string, Measurement>>(new Map());
  const [showPhase, setShowPhase] = useState(false);
  const [compareMode, setCompareMode] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.all([getTransformer(id), getTransformerMeasurements(id)])
      .then(([t, m]) => {
        setTransformer(t);
        setMeasurements(m);
        if (m.length > 0) {
          getMeasurement(m[0].id).then(setSelectedMeasurement);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  /* Load comparison measurements */
  const toggleComparison = async (mId: string) => {
    const next = new Set(comparisonIds);
    if (next.has(mId)) {
      next.delete(mId);
      setComparisonData((prev) => {
        const copy = new Map(prev);
        copy.delete(mId);
        return copy;
      });
    } else {
      if (next.size >= 6) return; // max 6 overlays
      next.add(mId);
      if (!comparisonData.has(mId)) {
        const data = await getMeasurement(mId);
        setComparisonData((prev) => new Map(prev).set(mId, data));
      }
    }
    setComparisonIds(next);
  };

  if (loading) return <LoadingOverlay message="Loading transformer details..." />;

  if (!transformer) {
    return (
      <GlassCard className="text-center py-16">
        <p className="text-(--status-critical)">Transformer not found.</p>
        <Link to="/transformers" className="btn btn-secondary mt-4">Back to Transformers</Link>
      </GlassCard>
    );
  }

  /* Build Plotly traces for comparison mode */
  const comparisonTraces: Plotly.Data[] = [];
  if (compareMode && comparisonIds.size > 0) {
    let colorIdx = 0;
    comparisonIds.forEach((mId) => {
      const m = comparisonData.get(mId);
      if (!m) return;
      const summary = measurements.find((ms) => ms.id === mId);
      const label = summary
        ? `${new Date(summary.measurement_date).toLocaleDateString()} — ${summary.winding_config}`
        : mId.slice(0, 8);
      const color = CURVE_COLORS[colorIdx % CURVE_COLORS.length];

      comparisonTraces.push({
        x: m.frequency_hz,
        y: m.magnitude_db,
        type: 'scatter',
        mode: 'lines',
        name: label,
        line: { color, width: 2, shape: 'spline' },
      });

      if (showPhase && m.phase_degrees?.length) {
        comparisonTraces.push({
          x: m.frequency_hz,
          y: m.phase_degrees,
          type: 'scatter',
          mode: 'lines',
          name: `${label} (Phase)`,
          line: { color, width: 1, shape: 'spline', dash: 'dot' },
          yaxis: 'y2',
        });
      }
      colorIdx++;
    });
  }

  /* Build single measurement traces */
  const singleTraces: Plotly.Data[] = selectedMeasurement
    ? [
        {
          x: selectedMeasurement.frequency_hz,
          y: selectedMeasurement.magnitude_db,
          type: 'scatter',
          mode: 'lines',
          name: 'Magnitude (dB)',
          line: { color: '#0D9488', width: 2, shape: 'spline' },
          fill: 'tozeroy',
          fillcolor: 'rgba(20, 184, 166, 0.08)',
        },
        ...(showPhase && selectedMeasurement.phase_degrees?.some((v) => v !== 0)
          ? [
              {
                x: selectedMeasurement.frequency_hz,
                y: selectedMeasurement.phase_degrees!,
                type: 'scatter' as const,
                mode: 'lines' as const,
                name: 'Phase (°)',
                line: { color: '#8B5CF6', width: 1.5, shape: 'spline' as const, dash: 'dot' as const },
                yaxis: 'y2',
              },
            ]
          : []),
      ]
    : [];

  const traces = compareMode && comparisonTraces.length > 0 ? comparisonTraces : singleTraces;
  const hasPhaseData = selectedMeasurement?.phase_degrees?.some((v) => v !== 0) ?? false;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 animate-fade-in-down">
        <Link
          to="/transformers"
          className="p-2.5 rounded-xl bg-(--card-bg) border border-(--card-border) hover:border-(--teal-300) transition-all shadow-sm"
        >
          <ArrowLeft size={20} className="text-(--text-secondary)" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold font-display text-(--text-primary)">
              {transformer.name}
            </h1>
            <CriticalityBadge level={transformer.criticality} />
          </div>
          <p className="text-(--text-muted) mt-1">
            {transformer.substation && `${transformer.substation} · `}
            {transformer.location || 'Location not specified'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => downloadPdfReport(transformer.id)}
            className="btn btn-secondary flex items-center gap-1.5 text-xs"
            title="Download PDF Report"
          >
            <Download size={14} /> PDF Report
          </button>
          <button
            onClick={() => downloadMeasurementsExcel(transformer.id)}
            className="btn btn-secondary flex items-center gap-1.5 text-xs"
            title="Export Measurements to Excel"
          >
            <FileSpreadsheet size={14} /> Excel
          </button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in-up stagger-1">
        <InfoCard label="Voltage Rating" value={transformer.voltage_rating_kv ? `${transformer.voltage_rating_kv} kV` : '—'} icon={<Activity size={16} />} />
        <InfoCard label="Power Rating" value={transformer.power_rating_mva ? `${transformer.power_rating_mva} MVA` : '—'} icon={<Activity size={16} />} />
        <InfoCard label="Manufacturer" value={transformer.manufacturer || '—'} icon={<FileText size={16} />} />
        <InfoCard label="Year" value={transformer.year_of_manufacture?.toString() || '—'} icon={<Calendar size={16} />} />
      </div>

      {/* FRA Curve — Enhanced */}
      {(selectedMeasurement || (compareMode && comparisonTraces.length > 0)) && (
        <div className="animate-fade-in-up stagger-2">
          <GlassCard padding="none" hover={false}>
            <div className="px-6 py-5 border-b border-(--card-border) flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-(--teal-50)">
                    <Activity size={18} className="text-(--teal-600)" />
                  </div>
                  {compareMode ? 'FRA Curve Comparison' : 'FRA Curve — Latest Measurement'}
                </h2>
                {compareMode && (
                  <p className="text-xs text-(--text-muted) mt-1">
                    {comparisonIds.size} measurement{comparisonIds.size !== 1 ? 's' : ''} overlaid
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {(hasPhaseData || compareMode) && (
                  <Button
                    variant={showPhase ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => setShowPhase(!showPhase)}
                    icon={showPhase ? <EyeOff size={14} /> : <Eye size={14} />}
                  >
                    Phase
                  </Button>
                )}
                <Button
                  variant={compareMode ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setCompareMode(!compareMode)}
                  icon={<Layers size={14} />}
                >
                  {compareMode ? 'Exit Compare' : 'Compare'}
                </Button>
              </div>
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
                    title: { text: 'Magnitude (dB)', font: { color: '#334155', size: 12 } },
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
                    y: 1.15,
                    orientation: 'h',
                    font: { size: 11, color: '#64748B' },
                  },
                  showlegend: compareMode || showPhase,
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
            {selectedMeasurement && !compareMode && (
              <div className="px-6 py-4 border-t border-(--card-border) flex flex-wrap items-center gap-4 text-xs">
                <span className="font-mono text-(--teal-600)">{selectedMeasurement.winding_config}</span>
                <span className="w-1 h-1 rounded-full bg-(--card-border)" />
                <span className="flex items-center gap-1.5 text-(--text-muted)">
                  <Calendar size={12} />
                  {new Date(selectedMeasurement.measurement_date).toLocaleDateString()}
                </span>
                <span className="w-1 h-1 rounded-full bg-(--card-border)" />
                <span className="font-mono text-(--text-muted)">
                  {selectedMeasurement.frequency_hz.length.toLocaleString()} data points
                </span>
                <span className="w-1 h-1 rounded-full bg-(--card-border)" />
                <span className="text-(--text-muted)">
                  Vendor: <span className="text-(--text-secondary)">{selectedMeasurement.vendor}</span>
                </span>
              </div>
            )}
          </GlassCard>
        </div>
      )}

      {/* Measurements Table */}
      <div className="animate-fade-in-up stagger-3">
        <GlassCard padding="none" hover={false}>
          <div className="px-6 py-5 border-b border-(--card-border) flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold font-display text-(--text-primary)">
                Measurements
              </h2>
              <p className="text-xs text-(--text-muted) mt-0.5">
                {measurements.length} recording{measurements.length !== 1 ? 's' : ''} available
              </p>
            </div>
            <Link to="/import">
              <Button variant="secondary" size="sm" icon={<Upload size={14} />}>
                Upload New
              </Button>
            </Link>
          </div>
          {measurements.length === 0 ? (
            <div className="empty-state">
              <Activity size={48} className="empty-state-icon" />
              <h3 className="empty-state-title">No Measurements Yet</h3>
              <p className="empty-state-description">
                Upload FRA data to start monitoring this transformer's health.
              </p>
              <Link to="/import" className="mt-4">
                <Button icon={<Upload size={16} />}>Import FRA Data</Button>
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    {compareMode && <th className="w-12">Compare</th>}
                    <th>Date</th>
                    <th>Winding Config</th>
                    <th>Vendor</th>
                    <th>Data Points</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.map((m) => (
                    <tr
                      key={m.id}
                      className={
                        selectedMeasurement?.id === m.id && !compareMode
                          ? 'bg-(--teal-50)'
                          : comparisonIds.has(m.id)
                            ? 'bg-(--teal-50)/50'
                            : ''
                      }
                    >
                      {compareMode && (
                        <td>
                          <input
                            type="checkbox"
                            checked={comparisonIds.has(m.id)}
                            onChange={() => toggleComparison(m.id)}
                            className="w-4 h-4 accent-(--teal-600) cursor-pointer"
                          />
                          {comparisonIds.has(m.id) && (
                            <span
                              className="inline-block w-2.5 h-2.5 rounded-full ml-2"
                              style={{
                                backgroundColor:
                                  CURVE_COLORS[
                                    [...comparisonIds].indexOf(m.id) % CURVE_COLORS.length
                                  ],
                              }}
                            />
                          )}
                        </td>
                      )}
                      <td className="font-mono text-(--text-secondary)">
                        {new Date(m.measurement_date).toLocaleDateString()}
                      </td>
                      <td>
                        <span className="badge badge-neutral font-mono">{m.winding_config}</span>
                      </td>
                      <td className="text-(--text-muted)">{m.vendor || '—'}</td>
                      <td className="font-mono text-(--text-muted)">{m.data_points.toLocaleString()}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => getMeasurement(m.id).then(setSelectedMeasurement)}
                            className={`text-sm font-medium transition-colors ${
                              selectedMeasurement?.id === m.id
                                ? 'text-(--teal-600)'
                                : 'text-(--text-muted) hover:text-(--teal-600)'
                            }`}
                          >
                            {selectedMeasurement?.id === m.id ? '● Viewing' : 'View'}
                          </button>
                          <button
                            onClick={() => navigate(`/analysis?transformer=${id}&measurement=${m.id}`)}
                            className="text-sm text-(--text-muted) hover:text-purple-600 transition-colors flex items-center gap-1"
                            title="Run ML Analysis"
                          >
                            <Play size={12} /> Analyze
                          </button>
                        </div>
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

function InfoCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <GlassCard className="text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        <span className="text-(--teal-600)">{icon}</span>
        <p className="text-xs uppercase tracking-wider text-(--text-muted)">{label}</p>
      </div>
      <p className="text-xl font-semibold font-display text-(--text-primary)">{value}</p>
    </GlassCard>
  );
}
