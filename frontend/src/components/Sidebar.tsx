/**
 * Elegant sidebar navigation component.
 * Soft & Elegant Light Theme with teal accents.
 */
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  Upload,
  BarChart3,
  ClipboardList,
  Activity,
  LogOut,
  ShieldCheck,
} from 'lucide-react';

import { useAuth } from '../auth/AuthProvider';
import Button from './ui/Button';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/transformers', icon: Zap, label: 'Transformers' },
  { to: '/import', icon: Upload, label: 'Import Data' },
  { to: '/analysis', icon: BarChart3, label: 'Analysis' },
  { to: '/recommendations', icon: ClipboardList, label: 'Recommendations' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const initials = user?.full_name
    ?.split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() ?? user?.email.slice(0, 2).toUpperCase() ?? 'OP';

  return (
    <aside 
      className="fixed left-0 top-0 h-screen w-70 flex flex-col z-50"
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--card-bg)',
        borderRight: '1px solid var(--card-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Logo / Title */}
      <div className="px-6 py-6 border-b border-(--card-border)">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ 
              background: 'var(--gradient-teal)',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <Activity size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight font-display">
              <span className="text-gradient">FRA</span>{' '}
              <span className="text-(--text-primary)">Diagnostics</span>
            </h1>
            <p className="text-xs text-(--text-muted) mt-0.5">
              Transformer Health Analysis
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }, index) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-(--teal-50) text-(--teal-700) border border-(--teal-200)'
                  : 'text-(--text-muted) hover:text-(--text-primary) hover:bg-(--bg-secondary) border border-transparent'
              }`
            }
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {({ isActive }) => (
              <>
                <div
                  className={`p-1.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-(--teal-100)'
                      : 'group-hover:bg-(--bg-primary)'
                  }`}
                >
                  <Icon
                    size={18}
                    className={`transition-colors duration-200 ${
                      isActive ? 'text-(--teal-600)' : 'text-(--text-muted) group-hover:text-(--text-secondary)'
                    }`}
                  />
                </div>
                <span>{label}</span>
                {isActive && (
                  <div
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-(--teal-500)"
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-6 py-5 border-t border-(--card-border) space-y-4">
        <div className="rounded-2xl border border-(--card-border) bg-(--bg-secondary) p-3">
          <div className="flex items-center gap-3">
            <div
              className="flex h-11 w-11 items-center justify-center rounded-2xl text-sm font-semibold text-white"
              style={{ background: 'var(--gradient-teal)' }}
            >
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-(--text-primary)">
                {user?.full_name || 'Authenticated user'}
              </p>
              <p className="truncate text-xs text-(--text-muted)">{user?.email}</p>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between rounded-xl bg-white/70 px-3 py-2 text-xs">
            <div className="flex items-center gap-2 text-(--text-muted)">
              <ShieldCheck size={14} className="text-(--teal-600)" />
              <span>Role</span>
            </div>
            <span className="font-medium text-(--text-primary)">{user?.role ?? 'engineer'}</span>
          </div>

          <Button
            type="button"
            variant="ghost"
            fullWidth
            className="mt-3 justify-center"
            icon={<LogOut size={15} />}
            onClick={() => logout()}
          >
            Sign out
          </Button>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-[10px] text-(--text-dim) font-mono">
            v1.0.0
          </p>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-(--teal-500)" />
            <span className="text-[10px] text-(--text-muted)">Session secured</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
