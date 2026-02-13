/**
 * Analysis page with Soft & Elegant Light Theme.
 * Placeholder for Phase 4 ML analysis features.
 */
import { BarChart3, Brain, AlertCircle, Zap, Activity, TrendingUp } from 'lucide-react';
import { GlassCard } from '../components/ui';

export default function AnalysisPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="animate-fade-in-down">
        <h1 className="text-3xl font-bold font-display text-(--text-primary)">
          Fault Analysis
        </h1>
        <p className="text-(--text-muted) mt-1">
          ML-powered transformer health assessment and fault detection
        </p>
      </div>

      {/* Analysis Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 animate-fade-in-up stagger-1">
        <GlassCard className="text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-(--teal-50) flex items-center justify-center mb-4">
            <BarChart3 size={28} className="text-(--teal-600)" />
          </div>
          <h3 className="font-semibold text-(--text-primary) mb-2">Health Score</h3>
          <p className="text-5xl font-bold font-display text-(--text-muted) mb-2">—</p>
          <span className="badge badge-neutral">Phase 4</span>
        </GlassCard>

        <GlassCard className="text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-purple-50 flex items-center justify-center mb-4">
            <Brain size={28} className="text-purple-600" />
          </div>
          <h3 className="font-semibold text-(--text-primary) mb-2">Fault Detection</h3>
          <p className="text-sm text-(--text-muted) mt-2 mb-3">
            Ensemble ML model combining XGBoost, CNN, and Autoencoder
          </p>
          <span className="badge badge-neutral">Phase 4</span>
        </GlassCard>

        <GlassCard className="text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-(--status-info-bg) flex items-center justify-center mb-4">
            <TrendingUp size={28} className="text-(--status-info)" />
          </div>
          <h3 className="font-semibold text-(--text-primary) mb-2">Trend Analysis</h3>
          <p className="text-sm text-(--text-muted) mt-2 mb-3">
            Historical health monitoring and degradation trends
          </p>
          <span className="badge badge-neutral">Phase 5</span>
        </GlassCard>
      </div>

      {/* Fault Types Info */}
      <div className="animate-fade-in-up stagger-2">
        <GlassCard hover={false}>
          <h2 className="text-lg font-semibold font-display text-(--text-primary) mb-5 flex items-center gap-2">
            <Zap size={20} className="text-(--teal-600)" />
            Detectable Fault Types
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                type: 'Axial Displacement',
                range: '2–20 kHz',
                desc: 'Shift in resonance frequencies, altered peak amplitudes',
                color: 'var(--status-critical)',
              },
              {
                type: 'Radial Deformation',
                range: '< 2 kHz',
                desc: 'Low-frequency response changes, capacitance variations',
                color: 'var(--status-warning)',
              },
              {
                type: 'Core Grounding',
                range: '< 1 kHz',
                desc: 'Low-frequency anomalies, altered inductance patterns',
                color: 'var(--status-warning)',
              },
              {
                type: 'Winding Short Circuit',
                range: '> 100 kHz',
                desc: 'New resonance peaks, amplitude variations',
                color: 'var(--status-critical)',
              },
              {
                type: 'Loose Clamping',
                range: 'Broadband',
                desc: 'Increased damping, progressive degradation',
                color: 'var(--status-info)',
              },
              {
                type: 'Moisture Ingress',
                range: 'General',
                desc: 'Response degradation, reduced insulation quality',
                color: 'var(--status-info)',
              },
            ].map((f, index) => (
              <div
                key={f.type}
                className="p-4 rounded-xl bg-(--bg-secondary) border border-(--card-border) hover:border-(--teal-300) transition-all animate-fade-in"
                style={{ animationDelay: `${(index + 3) * 50}ms` }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: f.color }}
                  />
                  <h4 className="font-medium text-(--text-primary) text-sm">{f.type}</h4>
                </div>
                <p className="text-xs font-mono text-(--teal-600) mb-1.5">
                  Freq: {f.range}
                </p>
                <p className="text-xs text-(--text-muted) leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* ML Pipeline Info */}
      <div className="animate-fade-in-up stagger-3">
        <GlassCard hover={false}>
          <h2 className="text-lg font-semibold font-display text-(--text-primary) mb-5 flex items-center gap-2">
            <Activity size={20} className="text-purple-600" />
            ML Pipeline Architecture
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { step: '1', title: 'Feature Extraction', desc: 'Statistical, spectral, and wavelet features from FRA curves' },
              { step: '2', title: 'XGBoost Classifier', desc: 'Gradient boosting for tabular feature classification' },
              { step: '3', title: 'CNN Analysis', desc: '1D convolutional network for pattern recognition' },
              { step: '4', title: 'Ensemble Voting', desc: 'Combined predictions with confidence scoring' },
            ].map((item) => (
              <div
                key={item.step}
                className="relative p-4 rounded-xl bg-(--bg-secondary) border border-(--card-border)"
              >
                <div className="absolute -top-3 -left-3 w-8 h-8 rounded-lg bg-(--gradient-teal) flex items-center justify-center text-sm font-bold text-white shadow-sm">
                  {item.step}
                </div>
                <h4 className="font-medium text-(--text-primary) text-sm mt-2 mb-2">{item.title}</h4>
                <p className="text-xs text-(--text-muted)">{item.desc}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Info Banner */}
      <div className="alert alert-info animate-fade-in-up stagger-4">
        <AlertCircle size={20} className="shrink-0 mt-0.5" />
        <div>
          <h4 className="alert-title">Phase 3–4: ML Fault Detection Engine</h4>
          <p className="alert-description">
            Synthetic data generation, feature extraction, ML model training
            (XGBoost + CNN + Autoencoder ensemble), and inference API will be
            implemented in Phases 3–4. A placeholder analysis endpoint is
            available at <code className="text-(--teal-700) bg-(--teal-50) px-1 py-0.5 rounded">POST /api/v1/analysis/run/{'{'}measurement_id{'}'}</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
