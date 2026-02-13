/**
 * Dashboard page - Fleet overview with Soft & Elegant Light Theme.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Zap, Activity, AlertTriangle, CheckCircle, ArrowRight, TrendingUp } from 'lucide-react';
import { getTransformers } from '../api';
import type { Transformer } from '../types';
import { GlassCard, CriticalityBadge, LoadingOverlay } from '../components/ui';

export default function Dashboard() {
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTransformers()
      .then(setTransformers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const criticalCount = transformers.filter(
    (t) => t.criticality === 'critical'
  ).length;
  const importantCount = transformers.filter(
    (t) => t.criticality === 'important'
  ).length;
  const totalMeasurements = transformers.reduce(
    (sum, t) => sum + t.measurement_count,
    0
  );

  if (loading) {
    return <LoadingOverlay message="Loading dashboard..." />;
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">
          Dashboard
        </h1>
        <p className="text-(--text-muted) mt-1">
          Fleet overview and system health monitoring
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <SummaryCard
          icon={<Zap size={22} />}
          label="Total Transformers"
          value={transformers.length}
          trend="+2 this month"
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
          icon={<AlertTriangle size={22} />}
          label="Critical Assets"
          value={criticalCount}
          trend={importantCount > 0 ? `${importantCount} important` : 'All stable'}
          color="critical"
          delay={2}
        />
        <SummaryCard
          icon={<CheckCircle size={22} />}
          label="Analyses Run"
          value={0}
          trend="Phase 4"
          color="success"
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
                      <td className="text-(--text-muted)">
                        {t.substation || '—'}
                      </td>
                      <td className="font-mono text-(--text-secondary)">
                        {t.voltage_rating_kv ? `${t.voltage_rating_kv} kV` : '—'}
                      </td>
                      <td className="font-mono text-(--text-secondary)">
                        {t.power_rating_mva ? `${t.power_rating_mva} MVA` : '—'}
                      </td>
                      <td>
                        <CriticalityBadge level={t.criticality} />
                      </td>
                      <td className="font-mono text-(--text-muted)">
                        {t.measurement_count}
                      </td>
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

        {/* Quick Stats Panel */}
        <div className="space-y-5 animate-fade-in-up stagger-5">
          {/* System Health */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-(--text-primary)">System Health</h3>
              <div className="w-2 h-2 rounded-full bg-(--teal-500)" />
            </div>
            <div className="flex items-center justify-center py-4">
              <div className="relative">
                <svg className="w-32 h-32 transform -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="var(--bg-secondary)"
                    strokeWidth="8"
                    fill="none"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="url(#healthGradient)"
                    strokeWidth="8"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${(transformers.length > 0 ? ((transformers.length - criticalCount) / transformers.length) * 100 : 100) * 3.52} 352`}
                    className="transition-all duration-1000 ease-out"
                  />
                  <defs>
                    <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="var(--teal-400)" />
                      <stop offset="100%" stopColor="var(--teal-600)" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold font-display text-(--text-primary)">
                    {transformers.length > 0
                      ? Math.round(((transformers.length - criticalCount) / transformers.length) * 100)
                      : 100}%
                  </span>
                  <span className="text-xs text-(--text-muted)">Healthy</span>
                </div>
              </div>
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
                <div className="icon-circle-sm">
                  <Activity size={14} />
                </div>
                <span className="text-sm text-(--text-secondary) group-hover:text-(--teal-700)">
                  Import FRA Data
                </span>
              </Link>
              <Link
                to="/analysis"
                className="flex items-center gap-3 p-3 rounded-lg bg-(--bg-secondary) hover:bg-(--teal-50) border border-(--card-border) hover:border-(--teal-200) transition-all group"
              >
                <div className="icon-circle-sm">
                  <TrendingUp size={14} />
                </div>
                <span className="text-sm text-(--text-secondary) group-hover:text-(--teal-700)">
                  Run Analysis
                </span>
              </Link>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
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
