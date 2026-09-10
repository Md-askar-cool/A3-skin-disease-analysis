// ============================================================
// SafeSkin AI – Navbar Component
// Responsive navigation with auth state awareness
// ============================================================
import React, { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Menu,
  X,
  User,
  LogOut,
  Settings,
  ChevronDown,
  Activity,
  History,
  TrendingUp,
  Home,
  Info,
  BookOpen,
  LayoutDashboard,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuth } from '@/hooks/useAuth';
import toast from 'react-hot-toast';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  protected?: boolean;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Home', href: '/', icon: <Home size={16} /> },
  { label: 'How It Works', href: '/how-it-works', icon: <BookOpen size={16} /> },
  { label: 'Screening', href: '/screening', icon: <Activity size={16} />, protected: true },
  { label: 'History', href: '/history', icon: <History size={16} />, protected: true },
  { label: 'Progress', href: '/progress', icon: <TrendingUp size={16} />, protected: true },
  { label: 'About', href: '/about', icon: <Info size={16} /> },
];

export const Navbar: React.FC = () => {
  const { user, loading, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Detect scroll for navbar shadow
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleSignOut = async () => {
    await signOut();
    toast.success('Signed out successfully');
    navigate('/');
  };

  const visibleNavItems = navItems.filter(
    (item) => !item.protected || !!user,
  );

  return (
    <>
      {/* ── Main navbar ────────────────────────────────────────── */}
      <header
        className={clsx(
          'fixed top-0 left-0 right-0 z-50',
          'transition-all duration-300',
          scrolled
            ? 'bg-white/90 backdrop-blur-lg shadow-sm border-b border-primary-100/50'
            : 'bg-white/70 backdrop-blur-md',
        )}
      >
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">

            {/* ── Logo ─────────────────────────────────────────── */}
            <Link
              to="/"
              className="flex items-center gap-2.5 group"
              aria-label="SafeSkin AI Home"
            >
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center shadow-md group-hover:shadow-glow transition-shadow duration-300">
                  <Shield size={18} className="text-white" />
                </div>
                <div className="absolute -inset-1 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 opacity-0 group-hover:opacity-20 blur transition-opacity duration-300" />
              </div>
              <div className="flex flex-col leading-none">
                <span className="text-base font-bold bg-gradient-to-r from-primary-600 to-secondary-600 bg-clip-text text-transparent">
                  SafeSkin AI
                </span>
                <span className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">
                  Skin Screening
                </span>
              </div>
            </Link>

            {/* ── Desktop nav links ─────────────────────────────── */}
            <div className="hidden md:flex items-center gap-1">
              {visibleNavItems.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  end={item.href === '/'}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium',
                      'transition-all duration-200',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-slate-600 hover:text-primary-600 hover:bg-primary-50/60',
                    )
                  }
                >
                  {item.icon}
                  {item.label}
                </NavLink>
              ))}

              {/* Admin link */}
              {user?.role === 'admin' && (
                <NavLink
                  to="/admin"
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium',
                      'transition-all duration-200',
                      isActive
                        ? 'bg-secondary-50 text-secondary-700'
                        : 'text-slate-600 hover:text-secondary-600 hover:bg-secondary-50/60',
                    )
                  }
                >
                  <LayoutDashboard size={16} />
                  Admin
                </NavLink>
              )}
            </div>

            {/* ── Right side: auth ─────────────────────────────── */}
            <div className="flex items-center gap-2">
              {loading ? (
                <div className="w-8 h-8 rounded-full bg-primary-100 animate-pulse" />
              ) : user ? (
                /* ── User avatar dropdown ─────────────────────── */
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen((o) => !o)}
                    className={clsx(
                      'flex items-center gap-2 pl-1.5 pr-2.5 py-1.5 rounded-xl',
                      'border border-slate-200 bg-white shadow-sm',
                      'hover:border-primary-300 hover:shadow-md',
                      'transition-all duration-200',
                    )}
                    aria-expanded={dropdownOpen}
                    aria-haspopup="true"
                  >
                    {/* Avatar */}
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={user.full_name ?? user.email}
                        className="w-7 h-7 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">
                          {(user.full_name ?? user.email).charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <span className="hidden sm:block text-sm font-medium text-slate-700 max-w-[100px] truncate">
                      {user.full_name ?? user.email.split('@')[0]}
                    </span>
                    <ChevronDown
                      size={14}
                      className={clsx(
                        'text-slate-400 transition-transform duration-200',
                        dropdownOpen && 'rotate-180',
                      )}
                    />
                  </button>

                  {/* Dropdown menu */}
                  <AnimatePresence>
                    {dropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -8, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -8, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 mt-2 w-52 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50"
                      >
                        {/* User info */}
                        <div className="px-4 py-2 border-b border-slate-100 mb-1">
                          <p className="text-sm font-semibold text-slate-800 truncate">
                            {user.full_name ?? 'User'}
                          </p>
                          <p className="text-xs text-slate-500 truncate">{user.email}</p>
                          {user.role !== 'user' && (
                            <span className="inline-block mt-1 text-2xs font-semibold px-1.5 py-0.5 rounded-md bg-secondary-100 text-secondary-600 capitalize">
                              {user.role}
                            </span>
                          )}
                        </div>

                        <DropdownItem icon={<User size={15} />} onClick={() => { setDropdownOpen(false); }}>
                          Profile
                        </DropdownItem>
                        <DropdownItem icon={<Settings size={15} />} onClick={() => { setDropdownOpen(false); }}>
                          Settings
                        </DropdownItem>
                        {user.role === 'admin' && (
                          <DropdownItem
                            icon={<LayoutDashboard size={15} />}
                            onClick={() => { setDropdownOpen(false); navigate('/admin'); }}
                          >
                            Admin Dashboard
                          </DropdownItem>
                        )}
                        <div className="border-t border-slate-100 mt-1 pt-1">
                          <DropdownItem
                            icon={<LogOut size={15} />}
                            onClick={handleSignOut}
                            danger
                          >
                            Sign Out
                          </DropdownItem>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                /* ── Auth buttons ─────────────────────────────── */
                <div className="hidden md:flex items-center gap-2">
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-primary-600 rounded-lg hover:bg-primary-50 transition-all duration-200"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-primary-500 to-secondary-600 rounded-xl shadow-md hover:shadow-lg hover:shadow-primary-500/25 transition-all duration-200"
                  >
                    Get Started
                  </Link>
                </div>
              )}

              {/* Mobile hamburger */}
              <button
                onClick={() => setMobileOpen((o) => !o)}
                className="md:hidden p-2 rounded-xl text-slate-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              >
                {mobileOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </nav>
      </header>

      {/* ── Mobile drawer ──────────────────────────────────────── */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed top-0 right-0 bottom-0 z-50 w-72 bg-white shadow-2xl md:hidden overflow-y-auto"
            >
              {/* Drawer header */}
              <div className="flex items-center justify-between p-5 border-b border-slate-100">
                <Link to="/" className="flex items-center gap-2" onClick={() => setMobileOpen(false)}>
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center">
                    <Shield size={16} className="text-white" />
                  </div>
                  <span className="font-bold text-primary-700">SafeSkin AI</span>
                </Link>
                <button
                  onClick={() => setMobileOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Nav links */}
              <div className="p-4 space-y-1">
                {visibleNavItems.map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    end={item.href === '/'}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium',
                        'transition-all duration-200',
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-slate-600 hover:text-primary-600 hover:bg-slate-50',
                      )
                    }
                  >
                    <span className="text-primary-500">{item.icon}</span>
                    {item.label}
                  </NavLink>
                ))}
              </div>

              {/* Auth section */}
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-white">
                {user ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 px-3 py-2">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">
                          {(user.full_name ?? user.email).charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-800">{user.full_name ?? 'User'}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => { setMobileOpen(false); void handleSignOut(); }}
                      className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-danger-600 hover:bg-danger-50 transition-colors"
                    >
                      <LogOut size={16} />
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Link
                      to="/login"
                      onClick={() => setMobileOpen(false)}
                      className="block w-full text-center px-4 py-2.5 rounded-xl text-sm font-medium border border-primary-300 text-primary-600 hover:bg-primary-50"
                    >
                      Sign In
                    </Link>
                    <Link
                      to="/register"
                      onClick={() => setMobileOpen(false)}
                      className="block w-full text-center px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-primary-500 to-secondary-600 shadow-md"
                    >
                      Get Started Free
                    </Link>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Spacer to prevent content from going under fixed navbar */}
      <div className="h-16" />
    </>
  );
};

// ── Helper: Dropdown item ─────────────────────────────────────
interface DropdownItemProps {
  icon: React.ReactNode;
  onClick: () => void;
  danger?: boolean;
  children: React.ReactNode;
}
const DropdownItem: React.FC<DropdownItemProps> = ({ icon, onClick, danger, children }) => (
  <button
    onClick={onClick}
    className={clsx(
      'w-full flex items-center gap-2.5 px-4 py-2 text-sm font-medium',
      'transition-colors duration-150',
      danger
        ? 'text-danger-600 hover:bg-danger-50'
        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800',
    )}
  >
    <span className={danger ? 'text-danger-500' : 'text-slate-400'}>{icon}</span>
    {children}
  </button>
);

export default Navbar;
