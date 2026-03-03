/**
 * Dashboard page - Fleet overview with real analysis data and trend chart.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Plot from 'react-plotly.js';
import {
  Zap,
  Activity,
  ArrowRight,
  TrendingUp,
  Brain,
  ClipboardList,
} from 'lucide-react';
import { getTransformers, listAnalyses, getRecommendations } from '../api';
import type { Transformer, AnalysisResult, Recommendation } from '../types';
import { GlassCard, CriticalityBadge, LoadingOverlay } from '../components/ui';

export default function Dashboard() {
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getTransformers(),
      listAnalyses().catch(() => []),
      getRecommendations().catch(() => []),
    ])
      .then(([t, a, r]) => {
        setTransformers(t);
        setAnalyses(a);
        setRecommendations(r);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const criticalCount = transformers.filter((t) => t.criticality === 'critical').length;
  const importantCount = transformers.filter((t) => t.criticality === 'important').length;
  const totalMeasurements = transformers.reduce((sum, t) => sum + t.measurement_count, 0);
  const pendingRecs = recommendations.filter((r) => r.status === 'pending').length;

  /* Average health score from latest analyses (deduplicated per measurement) */
  const seenMeasurements = new Set<string>();
  const latestAnalyses: AnalysisResult[] = [];
  for (const a of analyses) {
    if (!seenMeasurements.has(a.measurement_id)) {
      seenMeasurements.add(a.measurement_id);
      latestAnalyses.push(a);
    }
  }
  const avgHealth =
    latestAnalyses.length > 0
      ? latestAnalyses.reduce((sum, a) => sum + (a.health_score ?? 0), 0) / latestAnalyses.length
      : null;

  if (loading) return <LoadingOverlay message="Loading dashboard..." />;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">Dashboard</h1>
        <p className="text-(--text-muted) mt-1">Fleet overview and system health monitoring</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <SummaryCard
          icon={<Zap size={22} />}
          label="Total Transformers"
          value={transformers.length}
          trend={`${criticalCount} critical, ${importantCount} important`}
          color="teal"
          delay={0}
        />
        <SummaryCard
          icon={<Activity size={22} />}
          label="Total Measurements"
          value={totalMeasurements}
          trend="Active monitoring"
          color="info"
          delay={1}
        />
        <SummaryCard
          icon={<Brain size={22} />}
          label="Analyses Run"
          value={analyses.length}
          trend={avgHealth != null ? `Avg health: ${Math.round(avgHealth)}` : 'Run analysis to see scores'}
          color="success"
          delay={2}
        />
        <SummaryCard
          icon={<ClipboardList size={22} />}
          label="Pending Actions"
          value={pendingRecs}
          trend={pendingRecs > 0 ? 'Needs attention' : 'All clear'}
          color={pendingRecs > 0 ? 'critical' : 'success'}
          delay={3}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Transformer Fleet Table */}
        <div className="lg:col-span-2 animate-fade-in-up stagger-4">
          <GlassCard padding="none" hover={false}>
            <div className="px-6 py-5 border-b border-(--card-border) flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold font-display text-(--text-primary)">
                  Transformer Fleet
                </h2>
                <p className="text-xs text-(--text-muted) mt-0.5">
                  {transformers.length} assets registered
                </p>
              </div>
              <Link
                to="/transformers"
                className="btn btn-ghost text-(--teal-600) hover:text-(--teal-700) group"
              >
                View All
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Substation</th>
                    <th>Voltage</th>
                    <th>Power</th>
                    <th>Criticality</th>
                    <th>Measurements</th>
                  </tr>
                </thead>
                <tbody>
                  {transformers.slice(0, 5).map((t, index) => (
                    <tr
                      key={t.id}
                      className="animate-fade-in"
                      style={{ animationDelay: `${(index + 5) * 50}ms` }}
                    >
                      <td>
                        <Link
                          to={`/transformers/${t.id}`}
                          className="font-medium text-(--teal-600) hover:text-(--teal-700) transition-colors"
                        >
                          {t.name}
                        </Link>
                      </td>
                      <td className="text-(--text-muted)">{t.substation || '—'}</td>
                      <td className="font-mono text-(--text-secondary)">
                        {t.voltage_rating_kv ? `${t.voltage_rating_kv} kV` : '—'}
                      </td>
                      <td className="font-mono text-(--text-secondary)">
                        {t.power_rating_mva ? `${t.power_rating_mva} MVA` : '—'}
                      </td>
                      <td>
                        <CriticalityBadge level={t.criticality} />
                      </td>
                      <td className="font-mono text-(--text-muted)">{t.measurement_count}</td>
                    </tr>
                  ))}
                  {transformers.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-(--text-muted)">
                        No transformers registered yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>

        {/* Right panel */}
        <div className="space-y-5 animate-fade-in-up stagger-5">
          {/* System Health */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-(--text-primary)">System Health</h3>
              <div className="w-2 h-2 rounded-full bg-(--teal-500)" />
            </div>
            <div className="flex items-center justify-center py-4">
              <HealthRing
                value={
                  avgHealth != null
                    ? avgHealth
                    : transformers.length > 0
                      ? ((transformers.length - criticalCount) / transformers.length) * 100
                      : 100
                }
                label={avgHealth != null ? 'ML Avg' : 'Fleet Health'}
              />
            </div>
          </GlassCard>

          {/* Quick Actions */}
          <GlassCard>
            <h3 className="font-semibold text-(--text-primary) mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Link
                to="/import"
                className="flex items-center gap-3 p-3 rounded-lg bg-(--bg-secondary) hover:bg-(--teal-50) border border-(--card-border) hover:border-(--teal-200) transition-all group"
              >
                <div className="icon-circle-sm"><Activity size={14} /></div>
                <span className="text-sm text-(--text-secondary) group-hover:text-(--teal-700)">Import FRA Data</span>
              </Link>
              <Link
                to="/analysis"
                className="flex items-center gap-3 p-3 rounded-lg bg-(--bg-secondary) hover:bg-(--teal-50) border border-(--card-border) hover:border-(--teal-200) transition-all group"
              >
                <div className="icon-circle-sm"><TrendingUp size={14} /></div>
                <span className="text-sm text-(--text-secondary) group-hover:text-(--teal-700)">Run Analysis</span>
              </Link>
              <Link
                to="/recommendations"
                className="flex items-center gap-3 p-3 rounded-lg bg-(--bg-secondary) hover:bg-(--teal-50) border border-(--card-border) hover:border-(--teal-200) transition-all group"
              >
                <div className="icon-circle-sm"><ClipboardList size={14} /></div>
                <span className="text-sm text-(--text-secondary) group-hover:text-(--teal-700)">
                  Recommendations{pendingRecs > 0 && ` (${pendingRecs})`}
                </span>
              </Link>
            </div>
          </GlassCard>

          {/* Recent Analyses mini-list */}
          {analyses.length > 0 && (
            <GlassCard>
              <h3 className="font-semibold text-(--text-primary) mb-3">Recent Analyses</h3>
              <div className="space-y-2">
                {analyses.slice(0, 4).map((a) => (
                  <div
                    key={a.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-(--bg-secondary) text-xs"
                  >
                    <span
                      className="font-medium"
                      style={{
                        color:
                          a.fault_type === 'healthy'
                            ? 'var(--status-success)'
                            : 'var(--status-warning)',
                      }}
                    >
                      {a.fault_type.replace(/_/g, ' ')}
                    </span>
                    <span className="font-mono text-(--text-muted)">
                      {a.health_score != null ? `${Math.round(a.health_score)}%` : '—'}
                    </span>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>
      </div>

      {/* Health Score Trend Chart */}
      {analyses.length > 1 && (
        <div className="animate-fade-in-up stagger-6">
          <HealthScoreTrend analyses={analyses} />
        </div>
      )}
    </div>
  );
}

/* ── Health Ring (SVG) ── */
function HealthRing({ value, label }: { value: number; label: string }) {
  const r = 56;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 80 ? 'var(--teal-500)' : value >= 60 ? '#22C55E' : value >= 40 ? '#D97706' : '#DC2626';

  return (
    <div className="relative">
      <svg className="w-32 h-32 transform -rotate-90">
        <circle cx="64" cy="64" r={r} stroke="var(--bg-secondary)" strokeWidth="8" fill="none" />
        <circle
          cx="64"
          cy="64"
          r={r}
          stroke={color}
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'all 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold font-display text-(--text-primary)">
          {Math.round(value)}%
        </span>
        <span className="text-xs text-(--text-muted)">{label}</span>
      </div>
    </div>
  );
}

/* ── Health Score Trend (Plotly) ── */
function HealthScoreTrend({ analyses }: { analyses: AnalysisResult[] }) {
  // Sort by created_at ascending
  const sorted = [...analyses]
    .filter((a) => a.health_score != null)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  if (sorted.length < 2) return null;

  return (
    <GlassCard padding="none" hover={false}>
      <div className="px-6 py-5 border-b border-(--card-border)">
        <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
          <TrendingUp size={20} className="text-(--teal-600)" />
          Health Score Trend
        </h2>
        <p className="text-xs text-(--text-muted) mt-0.5">
          Historical health scores from ML analyses over time
        </p>
      </div>
      <div className="p-4">
        <Plot
          data={[
            {
              x: sorted.map((a) => a.created_at),
              y: sorted.map((a) => a.health_score),
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Health Score',
              line: { color: '#0D9488', width: 2.5, shape: 'spline' },
              marker: { color: '#0D9488', size: 8, line: { color: '#fff', width: 2 } },
              fill: 'tozeroy',
              fillcolor: 'rgba(20, 184, 166, 0.06)',
            },
          ]}
          layout={{
            xaxis: {
              title: { text: 'Date', font: { color: '#334155', size: 12 } },
              gridcolor: 'rgba(226, 232, 240, 0.8)',
              linecolor: '#E2E8F0',
              tickfont: { color: '#64748B', size: 11 },
            },
            yaxis: {
              title: { text: 'Health Score', font: { color: '#334155', size: 12 } },
              range: [0, 105],
              gridcolor: 'rgba(226, 232, 240, 0.8)',
              linecolor: '#E2E8F0',
              tickfont: { color: '#64748B', size: 11, family: 'JetBrains Mono' },
              zerolinecolor: '#E2E8F0',
            },
            margin: { t: 20, r: 30, b: 50, l: 60 },
            height: 300,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { family: 'Inter, sans-serif', size: 12, color: '#334155' },
            hovermode: 'x unified',
            hoverlabel: {
              bgcolor: '#FFFFFF',
              bordercolor: '#0D9488',
              font: { color: '#0F172A', family: 'JetBrains Mono' },
            },
            shapes: [
              {
                type: 'line',
                xref: 'paper',
                yref: 'y',
                x0: 0,
                x1: 1,
                y0: 80,
                y1: 80,
                line: { color: 'rgba(34, 197, 94, 0.4)', width: 1, dash: 'dash' },
              },
              {
                type: 'line',
                xref: 'paper',
                yref: 'y',
                x0: 0,
                x1: 1,
                y0: 40,
                y1: 40,
                line: { color: 'rgba(220, 38, 38, 0.3)', width: 1, dash: 'dash' },
              },
            ],
          }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>
    </GlassCard>
  );
}

function SummaryCard({
  icon,
  label,
  value,
  trend,
  color,
  delay,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  trend?: string;
  color: 'teal' | 'info' | 'critical' | 'success';
  delay: number;
}) {
  const colorClasses = {
    teal: {
      bg: 'bg-(--teal-50)',
      text: 'text-(--teal-600)',
      border: 'border border-(--teal-100)',
    },
    info: {
      bg: 'bg-(--status-info-bg)',
      text: 'text-(--status-info)',
      border: 'border border-(--status-info-border)',
    },
    critical: {
      bg: 'bg-(--status-critical-bg)',
      text: 'text-(--status-critical)',
      border: 'border border-(--status-critical-border)',
    },
    success: {
      bg: 'bg-(--status-success-bg)',
      text: 'text-(--status-success)',
      border: 'border border-(--status-success-border)',
    },
  };

  const colors = colorClasses[color];

  return (
    <GlassCard 
      className={`animate-fade-in-up stagger-${delay + 1}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-(--text-muted) mb-1">{label}</p>
          <p className="text-4xl font-bold font-display text-(--text-primary)">
            {value}
          </p>
          {trend && (
            <p className="text-xs text-(--text-muted) mt-2 flex items-center gap-1">
              <TrendingUp size={12} className={colors.text} />
              {trend}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-xl ${colors.bg} ${colors.border}`}>
          <div className={colors.text}>{icon}</div>
        </div>
      </div>
    </GlassCard>
  );
}
