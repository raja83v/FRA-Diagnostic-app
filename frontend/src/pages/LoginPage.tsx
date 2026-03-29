import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, LockKeyhole, Mail, Radar } from 'lucide-react';

import { useAuth } from '../auth/AuthProvider';
import { Button, GlassCard, Input } from '../components/ui';

type FormState = {
  email: string;
  password: string;
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { authNotice, clearAuthNotice, login } = useAuth();
  const [form, setForm] = useState<FormState>({ email: '', password: '' });
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  const redirectTo = location.state?.from?.pathname ?? '/';

  useEffect(() => {
    return () => clearAuthNotice();
  }, [clearAuthNotice]);

  const validate = () => {
    const nextErrors: Partial<FormState> = {};

    if (!form.email.trim()) nextErrors.email = 'Email is required';
    if (!form.password.trim()) nextErrors.password = 'Password is required';

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setServerError('');
    if (!validate()) return;

    setLoading(true);
    try {
      await login({ email: form.email.trim(), password: form.password });
      navigate(redirectTo, { replace: true });
    } catch (error: any) {
      setServerError(error?.response?.data?.detail ?? 'Unable to sign in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-stage">
      <div className="auth-grid" />
      <section className="auth-hero animate-fade-in-up">
        <div className="auth-kicker">
          <Radar size={16} />
          FRA Mission Control
        </div>
        <h1 className="auth-title">
          Secure access for transformer diagnostics teams.
        </h1>
        <p className="auth-subtitle">
          Sign in to review fleet health, run FRA analysis, and export engineering reports from a single secured workspace.
        </p>

        <div className="auth-signal-panel">
          <div>
            <p className="auth-metric-label">Protected workflows</p>
            <p className="auth-metric-value">Analysis, imports, reports</p>
          </div>
          <div>
            <p className="auth-metric-label">Session model</p>
            <p className="auth-metric-value">HTTP-only signed cookies</p>
          </div>
          <div>
            <p className="auth-metric-label">Access posture</p>
            <p className="auth-metric-value">Operator accounts with live session restore</p>
          </div>
        </div>
      </section>

      <GlassCard className="auth-panel animate-fade-in-up stagger-2" padding="lg" hover={false}>
        <div className="space-y-2">
          <p className="auth-panel-label">Sign in</p>
          <h2 className="text-2xl font-display text-(--text-primary)">Continue to the diagnostics console</h2>
          <p className="text-sm text-(--text-muted)">
            Use your engineering account to open the protected workspace.
          </p>
        </div>

        <form className="space-y-4 mt-8" onSubmit={handleSubmit}>
          {authNotice && (
            <div className={`auth-notice auth-notice-${authNotice.kind}`}>
              {authNotice.message}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            error={errors.email}
            placeholder="engineer@utility.example"
            autoComplete="email"
            icon={<Mail size={16} />}
          />
          <Input
            label="Password"
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            error={errors.password}
            placeholder="Enter your password"
            autoComplete="current-password"
            icon={<LockKeyhole size={16} />}
          />

          {serverError && (
            <div className="rounded-2xl border border-(--status-critical-border) bg-(--status-critical-bg) px-4 py-3 text-sm text-(--status-critical)">
              {serverError}
            </div>
          )}

          <Button type="submit" fullWidth size="lg" loading={loading} iconRight={!loading ? <ArrowRight size={16} /> : undefined}>
            Access workspace
          </Button>
        </form>

        <div className="auth-panel-footer">
          <span className="text-sm text-(--text-muted)">Need an account?</span>
          <Link to="/signup" className="font-medium text-(--teal-700)">
            Create one now
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}