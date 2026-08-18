import React, { useState, useEffect, useCallback } from 'react';
import { 
  LayoutDashboard, 
  ListTodo, 
  BarChart3, 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  Menu 
} from 'lucide-react';

/**
 * CareWise AI Sidebar Navigation Component
 * Features:
 * - Dashboard, Outreach Queue, Analytics navigation
 * - Workload Queues section with High Priority, Follow-ups, and Completed queues
 * - Live count synchronization from GET /api/dashboard
 * - Collapsible 280px <-> 76px state with subtle status dots & hover tooltips
 * - Active state detection based on pathname and search parameters
 */
export default function Sidebar({ currentPath, currentSearch, onNavigate }) {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('carewise.sidebar.collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const [counts, setCounts] = useState({
    highPriority: null,
    followUps: null,
    completed: null,
    total: null,
  });

  const [loading, setLoading] = useState(true);

  // Fetch live counts from /api/dashboard
  const fetchCounts = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`);
      const data = await res.json();
      
      const highPriority = data.high_priority_members ?? 0;
      const followUps = data.outreach_status?.['Follow-up'] ?? 0;
      const completed = data.outreach_status?.Completed ?? 0;
      const total = data.total_members ?? 0;

      setCounts({
        highPriority,
        followUps,
        completed,
        total,
      });
    } catch (err) {
      console.warn('Sidebar count sync warning:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCounts();

    // Listen for custom status update events across the application
    const handleStatusUpdated = () => fetchCounts();
    window.addEventListener('carewise:status-updated', handleStatusUpdated);
    window.addEventListener('focus', handleStatusUpdated);

    // Periodic live sync every 30 seconds
    const interval = setInterval(fetchCounts, 30000);

    return () => {
      window.removeEventListener('carewise:status-updated', handleStatusUpdated);
      window.removeEventListener('focus', handleStatusUpdated);
      clearInterval(interval);
    };
  }, [fetchCounts]);

  const toggleCollapse = () => {
    setCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('carewise.sidebar.collapsed', String(next));
      } catch {}
      document.body.classList.toggle('cw-sidebar-collapsed', next);
      return next;
    });
  };

  // Determine active item based on pathname and URL search params
  const pathname = currentPath || (typeof window !== 'undefined' ? window.location.pathname : '/');
  const search = currentSearch || (typeof window !== 'undefined' ? window.location.search : '');
  const searchParams = new URLSearchParams(search);
  const priorityParam = (searchParams.get('priority') || '').toLowerCase();
  const statusParam = (searchParams.get('status') || '').toLowerCase();

  const isOutreach = pathname === '/outreach' || pathname === '/outreach.html';
  const isHighPriorityActive = isOutreach && (priorityParam.includes('high'));
  const isFollowUpActive = isOutreach && (statusParam.includes('follow'));
  const isCompletedActive = isOutreach && (statusParam.includes('complete'));
  const isOutreachGeneralActive = isOutreach && !isHighPriorityActive && !isFollowUpActive && !isCompletedActive;
  const isDashboardActive = pathname === '/' || pathname === '/index.html' || pathname === '';
  const isAnalyticsActive = pathname === '/analytics' || pathname === '/analytics.html';

  const formatCount = (n) => {
    if (n === null || n === undefined) return '--';
    return Number(n).toLocaleString();
  };

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      href: '/',
      icon: LayoutDashboard,
      active: isDashboardActive,
    },
    {
      id: 'outreach',
      label: 'Outreach Queue',
      href: '/outreach',
      icon: ListTodo,
      active: isOutreachGeneralActive,
    },
    {
      id: 'analytics',
      label: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      active: isAnalyticsActive,
    },
  ];

  const workloadQueues = [
    {
      id: 'high-priority',
      label: 'High Priority',
      href: '/outreach?priority=High+Priority',
      icon: AlertTriangle,
      active: isHighPriorityActive,
      count: counts.highPriority,
      badgeBg: '#ba1a1a', // Red background (--error / #ba1a1a / #dc2626)
      badgeText: '#ffffff',
      dotColor: '#dc2626',
      tooltip: `High Priority (${formatCount(counts.highPriority)} members)`,
    },
    {
      id: 'follow-ups',
      label: 'Follow-ups',
      href: '/outreach?status=Follow-up',
      icon: Clock,
      active: isFollowUpActive,
      count: counts.followUps,
      badgeBg: '#ea580c', // Amber/Orange background (#d97706 / #ea580c)
      badgeText: '#ffffff',
      dotColor: '#ea580c',
      tooltip: `Follow-ups (${formatCount(counts.followUps)} members)`,
    },
    {
      id: 'completed',
      label: 'Completed',
      href: '/outreach?status=Completed',
      icon: CheckCircle2,
      active: isCompletedActive,
      count: counts.completed,
      badgeBg: '#16a34a', // Clinical green background (#16a34a / #00685f)
      badgeText: '#ffffff',
      dotColor: '#16a34a',
      tooltip: `Completed (${formatCount(counts.completed)} members)`,
    },
  ];

  const handleLinkClick = (e, item) => {
    if (onNavigate) {
      e.preventDefault();
      onNavigate(item.href, item);
    }
  };

  return (
    <nav
      data-sidebar
      aria-label="Sidebar Navigation"
      className={`fixed left-0 top-0 h-screen border-r border-[#bcc9c6] bg-[#ffffff] z-50 flex flex-col py-6 select-none transition-all duration-200 ease-in-out ${
        collapsed ? 'w-[76px]' : 'w-[280px]'
      }`}
      style={{
        borderColor: 'var(--outline-variant, #bcc9c6)',
        backgroundColor: 'var(--surface-container-lowest, #ffffff)',
      }}
    >
      {/* Toggle Button */}
      <div className="px-4 mb-3 flex items-center">
        <button
          type="button"
          onClick={toggleCollapse}
          data-sidebar-toggle
          aria-expanded={!collapsed}
          aria-label={collapsed ? 'Expand navigation sidebar' : 'Collapse navigation sidebar'}
          title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          className="cw-sidebar-toggle inline-flex items-center justify-center w-10 h-10 rounded-full text-[#00685f] hover:bg-[#eff4ff] focus:outline-none transition-colors"
          style={{ color: 'var(--primary, #00685f)' }}
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Brand Header */}
      <div className={`px-6 mb-6 flex items-center gap-3 overflow-hidden ${collapsed ? 'justify-center px-2' : ''}`}>
        <div className="cw-sidebar-logo w-10 h-10 rounded-full bg-[#008378] flex items-center justify-center text-white shrink-0">
          <svg viewBox="0 0 40 40" width="22" height="22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 7C17 1, 3 9, 3 18C3 26, 20 34, 20 34C20 34, 37 26, 37 18C37 9, 23 1, 20 7Z" fill="#008378" />
            <path d="M8 30C8 30, 12 36, 20 32C28 36, 32 30, 32 30" stroke="#008378" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M10 33C10 33, 13 38, 20 35C27 38, 30 33, 30 33" stroke="#f4fffc" strokeWidth="1.5" strokeLinecap="round" opacity="0.9" />
            <g fill="#f4fffc">
              <circle cx="13" cy="19" r="1.8" />
              <circle cx="20" cy="17" r="1.8" />
              <circle cx="27" cy="19" r="1.8" />
            </g>
            <g stroke="#f4fffc" strokeWidth="1.2" strokeLinecap="round">
              <line x1="13" y1="20.8" x2="13" y2="24" />
              <line x1="20" y1="18.8" x2="20" y2="22" />
              <line x1="27" y1="20.8" x2="27" y2="24" />
            </g>
          </svg>
        </div>
        {!collapsed && (
          <h1 className="text-[18px] font-bold text-[#00685f] leading-tight transition-opacity duration-150" style={{ color: 'var(--primary, #00685f)' }}>
            Care Management Outreach Prioritization Assistant
          </h1>
        )}
      </div>

      {/* Navigation Links Scroll Container */}
      <div className="flex-1 px-2 space-y-1 overflow-y-auto overflow-x-hidden">
        {/* Main Section */}
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.id}
                href={item.href}
                onClick={(e) => handleLinkClick(e, item)}
                title={collapsed ? item.label : undefined}
                className={`group relative flex items-center gap-3 px-4 py-3 rounded-lg transition-all cursor-pointer ${
                  item.active
                    ? 'bg-[#e5eeff] text-[#00685f] font-semibold border-r-4 border-[#00685f] rounded-r-none'
                    : 'text-[#3d4947] hover:bg-[#e5eeff]/60 hover:text-[#0b1c30]'
                } ${collapsed ? 'justify-center px-0' : ''}`}
                style={
                  item.active
                    ? {
                        backgroundColor: 'var(--surface-container, #e5eeff)',
                        color: 'var(--primary, #00685f)',
                        borderRight: '4px solid var(--primary, #00685f)',
                        fontWeight: 600,
                      }
                    : {}
                }
              >
                <div className="flex items-center justify-center shrink-0 w-6 h-6">
                  <Icon size={20} strokeWidth={item.active ? 2.5 : 2} />
                </div>
                {!collapsed && (
                  <span className="text-[13px] font-medium tracking-wide whitespace-nowrap">
                    {item.label}
                  </span>
                )}
              </a>
            );
          })}
        </div>

        {/* WORKLOAD QUEUES Section */}
        <div className="pt-5 pb-1">
          {!collapsed ? (
            <div className="px-4 pb-2 text-[11px] font-bold tracking-wider text-[#6d7a77] uppercase transition-opacity duration-150">
              WORKLOAD QUEUES
            </div>
          ) : (
            <div className="my-2 mx-auto w-8 border-t border-[#bcc9c6]/50" />
          )}

          <div className="space-y-1">
            {workloadQueues.map((item) => {
              const Icon = item.icon;
              return (
                <a
                  key={item.id}
                  href={item.href}
                  onClick={(e) => handleLinkClick(e, item)}
                  title={item.tooltip}
                  aria-label={`${item.label} (${formatCount(item.count)} members)`}
                  className={`group relative flex items-center justify-between px-4 py-3 rounded-lg transition-all cursor-pointer ${
                    item.active
                      ? 'bg-[#e5eeff] text-[#00685f] font-semibold border-r-4 border-[#00685f] rounded-r-none'
                      : 'text-[#3d4947] hover:bg-[#e5eeff]/60 hover:text-[#0b1c30]'
                  } ${collapsed ? 'justify-center px-0' : ''}`}
                  style={
                    item.active
                      ? {
                          backgroundColor: 'var(--surface-container, #e5eeff)',
                          color: 'var(--primary, #00685f)',
                          borderRight: '4px solid var(--primary, #00685f)',
                          fontWeight: 600,
                        }
                      : {}
                  }
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="relative flex items-center justify-center shrink-0 w-6 h-6">
                      <Icon size={20} strokeWidth={item.active ? 2.5 : 2} />
                      {/* Subtle status indicator dot in collapsed mode */}
                      {collapsed && (
                        <span
                          className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-white shadow-xs"
                          style={{ backgroundColor: item.dotColor }}
                        />
                      )}
                    </div>
                    {!collapsed && (
                      <span className="text-[13px] font-medium tracking-wide truncate">
                        {item.label}
                      </span>
                    )}
                  </div>

                  {/* Counter Badge in expanded mode */}
                  {!collapsed && (
                    <span
                      className="inline-flex items-center justify-center px-2 py-0.5 min-w-[24px] text-[11px] font-bold rounded-full leading-tight shadow-xs transition-transform group-hover:scale-105"
                      style={{
                        backgroundColor: item.badgeBg,
                        color: item.badgeText,
                      }}
                    >
                      {formatCount(item.count)}
                    </span>
                  )}
                </a>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer / Info */}
      {!collapsed && (
        <div className="px-4 pt-4 border-t border-[#bcc9c6]/40 text-[11px] text-[#6d7a77] flex items-center justify-between">
          <span>Care Management v1.0</span>
          {counts.total !== null && <span>{formatCount(counts.total)} total</span>}
        </div>
      )}
    </nav>
  );
}
