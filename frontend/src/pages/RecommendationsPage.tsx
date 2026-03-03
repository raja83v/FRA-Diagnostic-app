/**
 * Recommendations page — connects to backend API and displays
 * real maintenance recommendations with filtering and status updates.
 */
import { useEffect, useState, useCallback } from 'react';
import {
  ClipboardList,
  AlertCircle,
  Shield,
  Clock,
  CheckCircle2,
  Filter,
  ChevronDown,
  ArrowUpRight,
  MessageSquare,
} from 'lucide-react';
import {
  getRecommendations,
  updateRecommendationStatus,
  getTransformers,
} from '../api';
import type { Recommendation, UrgencyLevel, RecommendationStatus } from '../types';
import type { Transformer } from '../types';
import { GlassCard, Badge, Button, LoadingOverlay } from '../components/ui';

/* ── Urgency metadata ── */
const URGENCY_META: Record<UrgencyLevel, { label: string; color: string; bg: string; icon: typeof AlertCircle }> = {
  urgent: { label: 'Urgent', color: 'var(--status-critical)', bg: 'var(--status-critical-bg)', icon: AlertCircle },
  high: { label: 'High', color: '#EA580C', bg: '#FFF7ED', icon: AlertCircle },
  medium: { label: 'Medium', color: 'var(--status-warning)', bg: 'var(--status-warning-bg)', icon: Clock },
  low: { label: 'Low', color: 'var(--status-info)', bg: 'var(--status-info-bg)', icon: Clock },
  info: { label: 'Info', color: '#64748B', bg: '#F1F5F9', icon: MessageSquare },
};

const STATUS_META: Record<RecommendationStatus, { label: string; color: string; bg: string }> = {
  pending: { label: 'Pending', color: 'var(--status-warning)', bg: 'var(--status-warning-bg)' },
  in_progress: { label: 'In Progress', color: 'var(--status-info)', bg: 'var(--status-info-bg)' },
  completed: { label: 'Completed', color: 'var(--status-success)', bg: 'var(--status-success-bg)' },
  deferred: { label: 'Deferred', color: '#64748B', bg: '#F1F5F9' },
  cancelled: { label: 'Cancelled', color: '#94A3B8', bg: '#F8FAFC' },
};

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterUrgency, setFilterUrgency] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterTransformer, setFilterTransformer] = useState('');
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchRecs = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (filterUrgency) params.urgency = filterUrgency;
      if (filterStatus) params.status = filterStatus;
      if (filterTransformer) params.transformer_id = filterTransformer;
      const data = await getRecommendations(params);
      setRecommendations(data);
    } catch (err) {
      console.error('Failed to fetch recommendations', err);
    }
  }, [filterUrgency, filterStatus, filterTransformer]);

  useEffect(() => {
    Promise.all([fetchRecs(), getTransformers().then(setTransformers)])
      .finally(() => setLoading(false));
  }, [fetchRecs]);

  const handleStatusUpdate = async (id: string, newStatus: RecommendationStatus) => {
    setUpdatingId(id);
    try {
      const updated = await updateRecommendationStatus(id, { status: newStatus });
      setRecommendations((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (err) {
      console.error('Failed to update status', err);
    } finally {
      setUpdatingId(null);
    }
  };

  /* ── Summary counts ── */
  const urgentCount = recommendations.filter((r) => r.urgency === 'urgent' && r.status === 'pending').length;
  const highCount = recommendations.filter((r) => r.urgency === 'high' && r.status === 'pending').length;
  const pendingCount = recommendations.filter((r) => r.status === 'pending').length;
  const completedCount = recommendations.filter((r) => r.status === 'completed').length;

  if (loading) return <LoadingOverlay message="Loading recommendations..." />;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">
          Maintenance Recommendations
        </h1>
        <p className="text-(--text-muted) mt-1">
          AI-generated maintenance priorities based on fault analysis
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in-up stagger-1">
        <SummaryCard
          icon={<AlertCircle size={20} />}
          label="Urgent"
          count={urgentCount}
          color="var(--status-critical)"
          bg="var(--status-critical-bg)"
        />
        <SummaryCard
          icon={<Clock size={20} />}
          label="High Priority"
          count={highCount}
          color="#EA580C"
          bg="#FFF7ED"
        />
        <SummaryCard
          icon={<ClipboardList size={20} />}
          label="Pending"
          count={pendingCount}
          color="var(--status-warning)"
          bg="var(--status-warning-bg)"
        />
        <SummaryCard
          icon={<CheckCircle2 size={20} />}
          label="Completed"
          count={completedCount}
          color="var(--status-success)"
          bg="var(--status-success-bg)"
        />
      </div>

      {/* Filters */}
      <GlassCard hover={false} className="animate-fade-in-up stagger-2">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} className="text-(--teal-600)" />
          <span className="text-sm font-semibold text-(--text-secondary)">Filters</span>
        </div>
        <div className="flex flex-col md:flex-row gap-3">
          <FilterSelect
            label="Urgency"
            value={filterUrgency}
            onChange={setFilterUrgency}
            options={[
              { value: '', label: 'All Urgency Levels' },
              { value: 'urgent', label: 'Urgent' },
              { value: 'high', label: 'High' },
              { value: 'medium', label: 'Medium' },
              { value: 'low', label: 'Low' },
              { value: 'info', label: 'Info' },
            ]}
          />
          <FilterSelect
            label="Status"
            value={filterStatus}
            onChange={setFilterStatus}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'pending', label: 'Pending' },
              { value: 'in_progress', label: 'In Progress' },
              { value: 'completed', label: 'Completed' },
              { value: 'deferred', label: 'Deferred' },
            ]}
          />
          <FilterSelect
            label="Transformer"
            value={filterTransformer}
            onChange={setFilterTransformer}
            options={[
              { value: '', label: 'All Transformers' },
              ...transformers.map((t) => ({ value: t.id, label: t.name })),
            ]}
          />
        </div>
      </GlassCard>

      {/* Recommendations List */}
      {recommendations.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-4 animate-fade-in-up stagger-3">
          {recommendations.map((rec, index) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              onStatusChange={handleStatusUpdate}
              updating={updatingId === rec.id}
              transformerName={transformers.find((t) => t.id === rec.transformer_id)?.name}
              index={index}
            />
          ))}
        </div>
      )}

      {/* Criticality Matrix */}
      <CriticalityMatrix />
    </div>
  );
}

/* ── Sub-components ── */

function SummaryCard({
  icon,
  label,
  count,
  color,
  bg,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
  color: string;
  bg: string;
}) {
  return (
    <GlassCard>
      <div className="flex items-center gap-3">
        <div
          className="p-2.5 rounded-xl"
          style={{ backgroundColor: bg }}
        >
          <span style={{ color }}>{icon}</span>
        </div>
        <div>
          <p className="text-2xl font-bold font-display text-(--text-primary)">{count}</p>
          <p className="text-xs text-(--text-muted)">{label}</p>
        </div>
      </div>
    </GlassCard>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex-1">
      <label className="block text-xs text-(--text-muted) mb-1">{label}</label>
      <div className="relative">
        <select
          className="input w-full pr-8 appearance-none cursor-pointer text-sm"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-(--text-muted) pointer-events-none"
        />
      </div>
    </div>
  );
}

function RecommendationCard({
  rec,
  onStatusChange,
  updating,
  transformerName,
  index,
}: {
  rec: Recommendation;
  onStatusChange: (id: string, status: RecommendationStatus) => void;
  updating: boolean;
  transformerName?: string;
  index: number;
}) {
  const urgency = URGENCY_META[rec.urgency] ?? URGENCY_META.info;
  const status = STATUS_META[rec.status] ?? STATUS_META.pending;
  const UrgencyIcon = urgency.icon;

  const nextStatus: Record<string, RecommendationStatus> = {
    pending: 'in_progress',
    in_progress: 'completed',
  };
  const nextAction: Record<string, string> = {
    pending: 'Start',
    in_progress: 'Complete',
  };

  return (
    <GlassCard
      hover={false}
      className="animate-fade-in"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex flex-col md:flex-row gap-4">
        {/* Urgency indicator */}
        <div className="flex items-start gap-3 md:w-48 shrink-0">
          <div
            className="p-2 rounded-lg shrink-0"
            style={{ backgroundColor: urgency.bg }}
          >
            <UrgencyIcon size={18} style={{ color: urgency.color }} />
          </div>
          <div>
            <span
              className="text-xs font-bold uppercase tracking-wide"
              style={{ color: urgency.color }}
            >
              {urgency.label}
            </span>
            <p
              className="text-xs mt-0.5 px-2 py-0.5 rounded-full inline-block"
              style={{ backgroundColor: status.bg, color: status.color }}
            >
              {status.label}
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-(--text-primary) mb-1">{rec.title}</h3>
          <p className="text-sm text-(--text-muted) leading-relaxed mb-3">
            {rec.action_description}
          </p>
          <div className="flex flex-wrap items-center gap-3 text-xs text-(--text-muted)">
            {transformerName && (
              <span className="flex items-center gap-1">
                <ArrowUpRight size={12} className="text-(--teal-600)" />
                {transformerName}
              </span>
            )}
            {rec.fault_type && (
              <Badge variant="neutral">
                {rec.fault_type.replace(/_/g, ' ')}
              </Badge>
            )}
            {rec.due_date && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Due: {new Date(rec.due_date).toLocaleDateString()}
              </span>
            )}
            {rec.assigned_to && (
              <span>Assigned: {rec.assigned_to}</span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-start gap-2 shrink-0">
          {nextStatus[rec.status] && (
            <Button
              size="sm"
              variant={rec.urgency === 'urgent' ? 'primary' : 'secondary'}
              onClick={() => onStatusChange(rec.id, nextStatus[rec.status])}
              loading={updating}
            >
              {nextAction[rec.status]}
            </Button>
          )}
          {rec.status === 'pending' && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onStatusChange(rec.id, 'deferred')}
              loading={updating}
            >
              Defer
            </Button>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

function EmptyState() {
  return (
    <GlassCard hover={false} className="text-center py-16 animate-fade-in-up stagger-3">
      <div className="w-20 h-20 mx-auto rounded-2xl bg-(--bg-secondary) border border-(--card-border) flex items-center justify-center mb-5">
        <ClipboardList size={40} className="text-(--text-muted)" />
      </div>
      <h3 className="text-xl font-semibold font-display text-(--text-primary) mb-3">
        No Recommendations Found
      </h3>
      <p className="text-sm text-(--text-muted) max-w-md mx-auto">
        Recommendations are generated automatically when fault analysis detects issues.
        Run analysis on transformer measurements from the{' '}
        <a href="/analysis" className="text-(--teal-600) hover:text-(--teal-700) font-medium">
          Analysis page
        </a>{' '}
        to generate maintenance recommendations.
      </p>
    </GlassCard>
  );
}

function CriticalityMatrix() {
  return (
    <div className="animate-fade-in-up stagger-4">
      <GlassCard padding="none" hover={false}>
        <div className="px-6 py-5 border-b border-(--card-border)">
          <h2 className="text-lg font-semibold font-display text-(--text-primary) flex items-center gap-2">
            <Shield size={20} className="text-(--teal-600)" />
            Criticality Escalation Matrix
          </h2>
          <p className="text-xs text-(--text-muted) mt-1">
            How recommendations are prioritized based on asset criticality and fault probability
          </p>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Transformer Type</th>
                <th>Low Fault Prob.</th>
                <th>Medium Fault Prob.</th>
                <th>High Fault Prob.</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><Badge variant="critical">Critical</Badge></td>
                <td className="text-(--text-muted)">Monitor Monthly</td>
                <td className="text-(--status-warning) font-medium">Schedule Inspection</td>
                <td>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-(--status-critical-bg) text-(--status-critical) font-bold text-xs">
                    <AlertCircle size={12} />URGENT ACTION
                  </span>
                </td>
              </tr>
              <tr>
                <td><Badge variant="warning">Important</Badge></td>
                <td className="text-(--text-muted)">Monitor Quarterly</td>
                <td className="text-(--text-muted)">Monitor Monthly</td>
                <td className="text-(--status-warning) font-medium">Schedule Inspection</td>
              </tr>
              <tr>
                <td><Badge variant="success">Standard</Badge></td>
                <td className="text-(--text-muted)">Log Only</td>
                <td className="text-(--text-muted)">Monitor Quarterly</td>
                <td className="text-(--status-warning) font-medium">Schedule Inspection</td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}
