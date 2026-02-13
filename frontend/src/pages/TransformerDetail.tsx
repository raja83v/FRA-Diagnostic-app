/**
 * Transformer detail page with Soft & Elegant Light Theme and light Plotly charts.
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Activity, Upload, Calendar, FileText } from 'lucide-react';
import Plot from 'react-plotly.js';
import { getTransformer, getTransformerMeasurements, getMeasurement } from '../api';
import type { Transformer, MeasurementSummary, Measurement } from '../types';
import { GlassCard, CriticalityBadge, Button, LoadingOverlay } from '../components/ui';

export default function TransformerDetail() {
  const { id } = useParams<{ id: string }>();
  const [transformer, setTransformer] = useState<Transformer | null>(null);
  const [measurements, setMeasurements] = useState<MeasurementSummary[]>([]);
  const [selectedMeasurement, setSelectedMeasurement] =
    useState<Measurement | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([getTransformer(id), getTransformerMeasurements(id)])
      .then(([t, m]) => {
        setTransformer(t);
        setMeasurements(m);
        // Auto-load the latest measurement for curve preview
        if (m.length > 0) {
          getMeasurement(m[0].id).then(setSelectedMeasurement);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <LoadingOverlay message="Loading transformer details..." />;
  }

  if (!transformer) {
    return (
      <GlassCard className="text-center py-16">
        <p className="text-(--status-critical)">Transformer not found.</p>
        <Link to="/transformers" className="btn btn-secondary mt-4">
          Back to Transformers
        </Link>
      </GlassCard>
    );
  }

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
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in-up stagger-1">
        <InfoCard 
          label="Voltage Rating" 
          value={transformer.voltage_rating_kv ? `${transformer.voltage_rating_kv} kV` : '—'} 
          icon={<Activity size={16} />}
        />
        <InfoCard 
          label="Power Rating" 
          value={transformer.power_rating_mva ? `${transformer.power_rating_mva} MVA` : '—'} 
          icon={<Activity size={16} />}
        />
        <InfoCard 
          label="Manufacturer" 
          value={transformer.manufacturer || '—'} 
          icon={<FileText size={16} />}
        />
        <InfoCard
          label="Year"
          value={transformer.year_of_manufacture?.toString() || '—'}
          icon={<Calendar size={16} />}
        />
      </div>

      {/* FRA Curve Preview */}
      {selectedMeasurement && (
        <div className="animate-fade-in-up stagger-2">
          <GlassCard padding="none" hover={false}>
            <div className="px-6 py-5 border-b border-(--card-border)">
              <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-(--teal-50)">
                  <Activity size={18} className="text-(--teal-600)" />
                </div>
                FRA Curve — Latest Measurement
              </h2>
            </div>
            <div className="p-4">
              <Plot
                data={[
                  {
                    x: selectedMeasurement.frequency_hz,
                    y: selectedMeasurement.magnitude_db,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Magnitude (dB)',
                    line: { 
                      color: '#0D9488', 
                      width: 2,
                      shape: 'spline',
                    },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(20, 184, 166, 0.1)',
                  },
                ]}
                layout={{
                  xaxis: {
                    title: {
                      text: 'Frequency (Hz)',
                      font: { color: '#334155', size: 12 },
                    },
                    type: 'log',
                    showgrid: true,
                    gridcolor: 'rgba(226, 232, 240, 0.8)',
                    linecolor: '#E2E8F0',
                    tickfont: { color: '#64748B', size: 11, family: 'JetBrains Mono' },
                    zerolinecolor: '#E2E8F0',
                  },
                  yaxis: {
                    title: {
                      text: 'Magnitude (dB)',
                      font: { color: '#334155', size: 12 },
                    },
                    showgrid: true,
                    gridcolor: 'rgba(226, 232, 240, 0.8)',
                    linecolor: '#E2E8F0',
                    tickfont: { color: '#64748B', size: 11, family: 'JetBrains Mono' },
                    zerolinecolor: '#E2E8F0',
                  },
                  margin: { t: 20, r: 30, b: 60, l: 70 },
                  height: 400,
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  font: { family: 'Inter, sans-serif', size: 12, color: '#334155' },
                  hovermode: 'x unified',
                  hoverlabel: {
                    bgcolor: '#FFFFFF',
                    bordercolor: '#0D9488',
                    font: { color: '#0F172A', family: 'JetBrains Mono' },
                  },
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
            <div className="px-6 py-4 border-t border-(--card-border) flex flex-wrap items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-(--text-muted)">
                <span className="font-mono text-(--teal-600)">{selectedMeasurement.winding_config}</span>
              </span>
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
                <Button icon={<Upload size={16} />}>
                  Import FRA Data
                </Button>
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Winding Config</th>
                    <th>Vendor</th>
                    <th>Data Points</th>
                    <th>Temperature</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.map((m) => (
                    <tr
                      key={m.id}
                      className={selectedMeasurement?.id === m.id ? 'bg-(--teal-50)' : ''}
                    >
                      <td className="font-mono text-(--text-secondary)">
                        {new Date(m.measurement_date).toLocaleDateString()}
                      </td>
                      <td>
                        <span className="badge badge-neutral font-mono">
                          {m.winding_config}
                        </span>
                      </td>
                      <td className="text-(--text-muted)">{m.vendor || '—'}</td>
                      <td className="font-mono text-(--text-muted)">
                        {m.data_points.toLocaleString()}
                      </td>
                      <td className="text-(--text-muted)">—</td>
                      <td>
                        <button
                          onClick={() => getMeasurement(m.id).then(setSelectedMeasurement)}
                          className={`text-sm font-medium transition-colors ${
                            selectedMeasurement?.id === m.id
                              ? 'text-(--teal-600)'
                              : 'text-(--text-muted) hover:text-(--teal-600)'
                          }`}
                        >
                          {selectedMeasurement?.id === m.id ? '● Viewing' : 'View Curve'}
                        </button>
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
        <p className="text-xs uppercase tracking-wider text-(--text-muted)">
          {label}
        </p>
      </div>
      <p className="text-xl font-semibold font-display text-(--text-primary)">
        {value}
      </p>
    </GlassCard>
  );
}
