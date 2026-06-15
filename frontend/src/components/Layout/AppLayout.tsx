import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
  LayoutDashboard, Users,
  Upload, ClipboardList, LogOut, Menu,
  Wallet, ChevronRight, Bell,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { authApi } from '../../api/endpoints';
import clsx from 'clsx';
import ErrorBoundary from '../ErrorBoundary';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/groups', icon: Users, label: 'Groups' },
  { path: '/import', icon: Upload, label: 'Import Center' },
  { path: '/audit', icon: ClipboardList, label: 'Audit History' },
];

function NavItem({ path, icon: Icon, label }: { path: string; icon: any; label: string }) {
  const location = useLocation();
  const isActive = location.pathname === path || location.pathname.startsWith(path + '/');
  return (
    <Link to={path} className={clsx(isActive ? 'nav-item-active' : 'nav-item', 'group')}>
      <Icon size={18} className={clsx(isActive ? 'text-primary-400' : 'text-slate-500 group-hover:text-slate-300')} />
      <span>{label}</span>
      {isActive && <ChevronRight size={14} className="ml-auto text-primary-400" />}
    </Link>
  );
}

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout, refreshToken } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } catch {}
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-[#f4f7fc] overflow-hidden light-theme">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed lg:static inset-y-0 left-0 z-30 w-64 flex flex-col',
          'bg-[#eef2f6] border-r border-slate-200/60',
          'transition-transform duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-900/50">
              <Wallet size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg leading-none">ExpenseFlow</h1>
              <p className="text-slate-500 text-xs mt-0.5">Smart expense sharing</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavItem key={item.path} {...item} />
          ))}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-white/5">
          <div className="glass-card p-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
              {user?.first_name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-slate-500 text-xs truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-slate-500 hover:text-red-400 transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="h-16 flex lg:hidden items-center justify-between px-6 border-b border-slate-200/60 bg-white/70 backdrop-blur-xl flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-slate-500 hover:text-slate-900 transition-colors"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-3 ml-auto">
            <button className="w-9 h-9 rounded-xl bg-slate-100 hover:bg-slate-200/70 border border-slate-200/50 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-all">
              <Bell size={16} />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 max-w-7xl mx-auto animate-fade-in">
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
