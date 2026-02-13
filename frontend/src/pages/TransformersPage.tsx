/**
 * Transformers list page with Soft & Elegant Light Theme.
 */
import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Zap, MapPin, Gauge } from 'lucide-react';
import { getTransformers } from '../api';
import type { Transformer } from '../types';
import { GlassCard, CriticalityBadge, Button, LoadingOverlay } from '../components/ui';

export default function TransformersPage() {
  const [transformers, setTransformers] = useState<Transformer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchTransformers = useCallback(async () => {
    try {
      const data = await getTransformers({ search: search || undefined });
      setTransformers(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchTransformers();
  }, [fetchTransformers]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between animate-fade-in-down">
        <div>
          <h1 className="text-3xl font-bold font-display text-(--text-primary)">
            Transformers
          </h1>
          <p className="text-(--text-muted) mt-1">
            Manage and monitor your transformer fleet
          </p>
        </div>
        <Link to="/transformers/new">
          <Button icon={<Plus size={16} />}>
            Add Transformer
          </Button>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="relative animate-fade-in-up stagger-1">
        <Search
          size={18}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-(--text-muted)"
        />
        <input
          type="text"
          placeholder="Search transformers by name, substation, or manufacturer..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input input-with-icon w-full"
        />
      </div>

      {/* Results */}
      {loading ? (
        <LoadingOverlay message="Loading transformers..." />
      ) : (
        <>
          {/* Stats Bar */}
          <div className="flex items-center gap-4 text-sm text-(--text-muted) animate-fade-in">
            <span>{transformers.length} transformer{transformers.length !== 1 ? 's' : ''} found</span>
            <span className="w-1 h-1 rounded-full bg-(--card-border)" />
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-(--status-critical)" />
              {transformers.filter(t => t.criticality === 'critical').length} critical
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-(--status-warning)" />
              {transformers.filter(t => t.criticality === 'important').length} important
            </span>
          </div>

          {/* Transformer Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {transformers.map((t, index) => (
              <TransformerCard 
                key={t.id} 
                transformer={t} 
                delay={index}
              />
            ))}
            {transformers.length === 0 && (
              <div className="col-span-full">
                <GlassCard hover={false} className="text-center py-16">
                  <Zap size={48} className="mx-auto text-(--text-muted) mb-4" />
                  <h3 className="text-lg font-semibold text-(--text-primary) mb-2">
                    No Transformers Found
                  </h3>
                  <p className="text-sm text-(--text-muted) max-w-md mx-auto mb-6">
                    {search
                      ? `No transformers match "${search}". Try a different search term.`
                      : 'Get started by adding your first transformer to the system.'}
                  </p>
                  {!search && (
                    <Link to="/transformers/new">
                      <Button icon={<Plus size={16} />}>
                        Add Transformer
                      </Button>
                    </Link>
                  )}
                </GlassCard>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function TransformerCard({ 
  transformer: t, 
  delay 
}: { 
  transformer: Transformer;
  delay: number;
}) {
  const criticalityColors: Record<string, string> = {
    critical: 'var(--status-critical)',
    important: 'var(--status-warning)',
    standard: 'var(--teal-500)',
  };

  return (
    <Link
      to={`/transformers/${t.id}`}
      className="block animate-fade-in-up group"
      style={{ animationDelay: `${Math.min(delay, 8) * 50 + 100}ms` }}
    >
      <GlassCard className="relative overflow-hidden">
        {/* Criticality indicator bar */}
        <div 
          className="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg"
          style={{ backgroundColor: criticalityColors[t.criticality] || criticalityColors.standard }}
        />
        
        {/* Content */}
        <div className="pl-3">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="font-semibold text-(--text-primary) group-hover:text-(--teal-600) transition-colors">
                {t.name}
              </h3>
              {t.substation && (
                <p className="text-xs text-(--text-muted) flex items-center gap-1 mt-1">
                  <MapPin size={12} />
                  {t.substation}
                </p>
              )}
            </div>
            <CriticalityBadge level={t.criticality} />
          </div>

          {/* Specs */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-2.5 rounded-lg bg-(--bg-secondary) border border-(--card-border)">
              <p className="text-[10px] uppercase tracking-wider text-(--text-muted) mb-0.5">
                Voltage
              </p>
              <p className="text-sm font-mono font-medium text-(--text-secondary)">
                {t.voltage_rating_kv ? `${t.voltage_rating_kv} kV` : '—'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-(--bg-secondary) border border-(--card-border)">
              <p className="text-[10px] uppercase tracking-wider text-(--text-muted) mb-0.5">
                Power
              </p>
              <p className="text-sm font-mono font-medium text-(--text-secondary)">
                {t.power_rating_mva ? `${t.power_rating_mva} MVA` : '—'}
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-(--card-border)">
            <p className="text-xs text-(--text-muted)">
              {t.manufacturer || 'Unknown manufacturer'}
            </p>
            <div className="flex items-center gap-1.5 text-xs text-(--text-muted)">
              <Gauge size={12} />
              <span className="font-mono">{t.measurement_count}</span>
              <span>reading{t.measurement_count !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>
      </GlassCard>
    </Link>
  );
}
