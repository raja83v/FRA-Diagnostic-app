import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, BadgeCheck, LockKeyhole, Mail, UserRound } from 'lucide-react';

import { useAuth } from '../auth/AuthProvider';
import { Button, GlassCard, Input } from '../components/ui';

type FormState = {
  full_name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

export default function SignupPage() {
  const navigate = useNavigate();
  const { authNotice, clearAuthNotice, signup } = useAuth();
  const [form, setForm] = useState<FormState>({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    return () => clearAuthNotice();
  }, [clearAuthNotice]);

  const validate = () => {
    const nextErrors: Partial<FormState> = {};

    if (!form.full_name.trim()) nextErrors.full_name = 'Name is required';
    if (!form.email.trim()) nextErrors.email = 'Email is required';
    if (form.password.length < 8) nextErrors.password = 'Use at least 8 characters';
    if (form.confirmPassword !== form.password) nextErrors.confirmPassword = 'Passwords do not match';

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setServerError('');
    if (!validate()) return;

    setLoading(true);
    try {
      await signup({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      navigate('/', { replace: true });
    } catch (error: any) {
      setServerError(error?.response?.data?.detail ?? 'Unable to create your account right now.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-stage auth-stage-signup">
      <div className="auth-grid" />
      <section className="auth-hero animate-fade-in-up">
        <div className="auth-kicker auth-kicker-alt">
          <BadgeCheck size={16} />
          Operator enrollment
        </div>
        <h1 className="auth-title">
          Create a secure engineering account in under a minute.
        </h1>
        <p className="auth-subtitle">
          New operators can self-enroll, then move directly into transformer monitoring, FRA imports, and maintenance recommendation review.
        </p>

        <div className="auth-signal-panel">
          <div>
            <p className="auth-metric-label">Default access</p>
            <p className="auth-metric-value">Engineer workspace role</p>
          </div>
          <div>
            <p className="auth-metric-label">Password policy</p>
            <p className="auth-metric-value">Minimum 8 characters</p>
          </div>
          <div>
            <p className="auth-metric-label">Immediate result</p>
            <p className="auth-metric-value">Session starts after signup</p>
          </div>
        </div>
      </section>

      <GlassCard className="auth-panel animate-fade-in-up stagger-2" padding="lg" hover={false}>
        <div className="space-y-2">
          <p className="auth-panel-label">Create account</p>
          <h2 className="text-2xl font-display text-(--text-primary)">Open a new operator workspace</h2>
          <p className="text-sm text-(--text-muted)">
            Register with your work email and you will be signed in automatically.
          </p>
        </div>

        <form className="space-y-4 mt-8" onSubmit={handleSubmit}>
          {authNotice && (
            <div className={`auth-notice auth-notice-${authNotice.kind}`}>
              {authNotice.message}
            </div>
          )}

          <Input
            label="Full name"
            value={form.full_name}
            onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
            error={errors.full_name}
            placeholder="Raj Velayuthan"
            autoComplete="name"
            icon={<UserRound size={16} />}
          />
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
            placeholder="Create a password"
            autoComplete="new-password"
            icon={<LockKeyhole size={16} />}
          />
          <Input
            label="Confirm password"
            type="password"
            value={form.confirmPassword}
            onChange={(event) => setForm((current) => ({ ...current, confirmPassword: event.target.value }))}
            error={errors.confirmPassword}
            placeholder="Repeat your password"
            autoComplete="new-password"
            icon={<LockKeyhole size={16} />}
          />

          {serverError && (
            <div className="rounded-2xl border border-(--status-critical-border) bg-(--status-critical-bg) px-4 py-3 text-sm text-(--status-critical)">
              {serverError}
            </div>
          )}

          <Button type="submit" fullWidth size="lg" loading={loading} iconRight={!loading ? <ArrowRight size={16} /> : undefined}>
            Create account
          </Button>
        </form>

        <div className="auth-panel-footer">
          <span className="text-sm text-(--text-muted)">Already registered?</span>
          <Link to="/login" className="font-medium text-(--teal-700)">
            Sign in instead
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}