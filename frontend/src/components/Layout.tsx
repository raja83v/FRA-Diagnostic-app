/**
 * Main layout wrapper with glassmorphic sidebar and content area.
 * Premium dark theme with emerald accents.
 */
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main 
        className="ml-70 flex-1 p-8 animate-fade-in"
        style={{ animationDelay: '100ms' }}
      >
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
