/**
 * Recommendations page with Soft & Elegant Light Theme.
 * Placeholder for Phase 6 recommendation engine.
 */
import { ClipboardList, AlertCircle, Shield, Clock, CheckCircle2 } from 'lucide-react';
import { GlassCard, Badge } from '../components/ui';

export default function RecommendationsPage() {
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

      {/* Empty State */}
      <div className="animate-fade-in-up stagger-1">
        <GlassCard hover={false} className="text-center py-16">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-(--bg-secondary) border border-(--card-border) flex items-center justify-center mb-5">
            <ClipboardList size={40} className="text-(--text-muted)" />
          </div>
          <h3 className="text-xl font-semibold font-display text-(--text-primary) mb-3">
            No Recommendations Yet
          </h3>
          <p className="text-sm text-(--text-muted) max-w-md mx-auto">
            Recommendations are automatically generated after running ML analysis
            on transformer measurements. The system uses fault probabilities and
            transformer criticality to prioritize maintenance actions.
          </p>
        </GlassCard>
      </div>

      {/* Criticality Matrix Preview */}
      <div className="animate-fade-in-up stagger-2">
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
                  <td>
                    <Badge variant="critical">Critical</Badge>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-(--text-muted)" />
                      <span className="text-(--text-muted)">Monitor Monthly</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <AlertCircle size={14} className="text-(--status-warning)" />
                      <span className="text-(--status-warning) font-medium">Schedule Inspection</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-(--status-critical-bg) border border-(--status-critical-border)">
                      <AlertCircle size={14} className="text-(--status-critical)" />
                      <span className="text-(--status-critical) font-bold">URGENT ACTION</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>
                    <Badge variant="warning">Important</Badge>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-(--text-muted)" />
                      <span className="text-(--text-muted)">Monitor Quarterly</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-(--text-muted)" />
                      <span className="text-(--text-muted)">Monitor Monthly</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <AlertCircle size={14} className="text-(--status-warning)" />
                      <span className="text-(--status-warning) font-medium">Schedule Inspection</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>
                    <Badge variant="success">Standard</Badge>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 size={14} className="text-(--text-muted)" />
                      <span className="text-(--text-muted)">Log Only</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-(--text-muted)" />
                      <span className="text-(--text-muted)">Monitor Quarterly</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <AlertCircle size={14} className="text-(--status-warning)" />
                      <span className="text-(--status-warning) font-medium">Schedule Inspection</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </GlassCard>
      </div>

      {/* Recommendation Types */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-fade-in-up stagger-3">
        {[
          {
            icon: AlertCircle,
            title: 'Urgent Actions',
            desc: 'Immediate attention required for critical assets with high fault probability',
            color: 'var(--status-critical)',
            bg: 'var(--status-critical-bg)',
          },
          {
            icon: Clock,
            title: 'Scheduled Inspections',
            desc: 'Planned maintenance activities based on detected anomalies',
            color: 'var(--status-warning)',
            bg: 'var(--status-warning-bg)',
          },
          {
            icon: CheckCircle2,
            title: 'Monitoring Tasks',
            desc: 'Regular observation and trending for early detection',
            color: 'var(--status-success)',
            bg: 'var(--status-success-bg)',
          },
        ].map((item) => (
          <GlassCard key={item.title}>
            <div 
              className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
              style={{ backgroundColor: item.bg }}
            >
              <item.icon size={24} style={{ color: item.color }} />
            </div>
            <h3 className="font-semibold text-(--text-primary) mb-2">{item.title}</h3>
            <p className="text-sm text-(--text-muted)">{item.desc}</p>
            <div className="mt-4 pt-4 border-t border-(--card-border)">
              <span className="text-3xl font-bold font-display text-(--text-muted)">0</span>
              <span className="text-xs text-(--text-muted) ml-2">pending</span>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Info Banner */}
      <div className="alert alert-warning animate-fade-in-up stagger-4">
        <AlertCircle size={20} className="shrink-0 mt-0.5" />
        <div>
          <h4 className="alert-title">Phase 6: Recommendation Engine</h4>
          <p className="alert-description">
            The recommendation engine combines fault analysis results with
            transformer criticality to generate prioritized maintenance
            recommendations. API endpoints are ready at{' '}
            <code className="text-(--status-warning) bg-(--status-warning-bg) px-1 py-0.5 rounded">GET /api/v1/recommendations/</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
