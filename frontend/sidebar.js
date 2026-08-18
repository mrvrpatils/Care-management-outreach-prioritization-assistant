(() => {
  const storageKey = 'carewise.sidebar.collapsed';
  const collapsedClass = 'cw-sidebar-collapsed';

  // Auth guard: Check authentication status on non-login pages
  const currentPath = window.location.pathname.toLowerCase();
  const isLoginPage = currentPath.includes('/login');
  const token = localStorage.getItem('carewise_token');
  const userStr = localStorage.getItem('carewise_user');

  if (!isLoginPage && (!token || !userStr)) {
    const redirectParam = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.replace(`/login?redirect=${redirectParam}`);
    return;
  }

  let currentUser = null;
  try {
    currentUser = JSON.parse(userStr || 'null');
  } catch (e) {
    currentUser = null;
  }

  // Logout handler
  window.carewiseLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {}
    localStorage.removeItem('carewise_token');
    localStorage.removeItem('carewise_user');
    window.location.replace('/login');
  };

  // Helper functions
  const getInitials = (name) => {
    if (!name) return 'CW';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const escapeHtml = (str) => {
    return String(str || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  };

  // SVG Icons (Lucide style stroke-based vectors)
  const ICONS = {
    dashboard: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>`,
    outreach: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h5"/><path d="M2 5h10"/><path d="M2 19h5"/><circle cx="17" cy="12" r="5"/><path d="m15 12 1.5 1.5 3-3"/></svg>`,
    analytics: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>`,
    careGaps: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m14 12-8.5 8.5a2.12 2.12 0 1 1-3-3L11 9"/><path d="M15 13 9 7l4-4 6 6-4 4Z"/></svg>`,
    alertTriangle: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    clock: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    checkCircle2: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`,
    menu: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>`,
    logout: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>`
  };

  const applyState = (collapsed) => {
    document.body.classList.toggle(collapsedClass, collapsed);
    const button = document.querySelector('[data-sidebar-toggle]');
    if (button) {
      button.setAttribute('aria-expanded', String(!collapsed));
      button.setAttribute('aria-label', collapsed ? 'Expand navigation sidebar' : 'Collapse navigation sidebar');
      button.title = collapsed ? 'Expand navigation' : 'Collapse navigation';
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '--';
    return Number(num).toLocaleString();
  };

  // State for live counts
  let liveCounts = {
    highPriority: null,
    followUps: null,
    completed: null,
    total: null
  };

  const updateBadgeDOM = () => {
    const highBadge = document.querySelector('[data-badge="high-priority"]');
    const highDot = document.querySelector('[data-dot="high-priority"]');
    const highLink = document.querySelector('[data-nav="high-priority"]');
    if (highBadge) highBadge.textContent = formatNumber(liveCounts.highPriority);
    if (highLink) highLink.title = `High Priority (${formatNumber(liveCounts.highPriority)} members)`;

    const followBadge = document.querySelector('[data-badge="follow-ups"]');
    const followLink = document.querySelector('[data-nav="follow-ups"]');
    if (followBadge) followBadge.textContent = formatNumber(liveCounts.followUps);
    if (followLink) followLink.title = `Follow-ups (${formatNumber(liveCounts.followUps)} members)`;

    const completedBadge = document.querySelector('[data-badge="completed"]');
    const completedLink = document.querySelector('[data-nav="completed"]');
    if (completedBadge) completedBadge.textContent = formatNumber(liveCounts.completed);
    if (completedLink) completedLink.title = `Completed (${formatNumber(liveCounts.completed)} members)`;
  };

  const fetchLiveCounts = async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (!res.ok) return;
      const data = await res.json();
      
      liveCounts.highPriority = data.high_priority_members ?? 0;
      liveCounts.followUps = data.outreach_status?.['Follow-up'] ?? 0;
      liveCounts.completed = data.outreach_status?.Completed ?? 0;
      liveCounts.total = data.total_members ?? 0;

      updateBadgeDOM();
    } catch (e) {
      console.warn('Sidebar count fetch error:', e);
    }
  };

  // Expose global refresher
  window.refreshSidebarCounts = fetchLiveCounts;

  const determineActiveRoute = () => {
    const path = window.location.pathname.toLowerCase();
    const search = window.location.search.toLowerCase();
    const params = new URLSearchParams(window.location.search);
    const priority = (params.get('priority') || '').toLowerCase();
    const status = (params.get('status') || '').toLowerCase();

    const isOutreach = path.includes('/outreach');
    if (isOutreach && priority.includes('high')) return 'high-priority';
    if (isOutreach && status.includes('follow')) return 'follow-ups';
    if (isOutreach && status.includes('complete')) return 'completed';
    if (isOutreach) return 'outreach';
    if (path.includes('/analytics')) return 'analytics';
    if (path.includes('/care-gaps')) return 'care-gaps';
    if (path === '/' || path.includes('/index')) return 'dashboard';
    return '';
  };

  const renderSidebarContent = (sidebar) => {
    const activeRoute = determineActiveRoute();

    // Check if workload queues already rendered
    let navContainer = sidebar.querySelector('.cw-sidebar-nav-container');
    if (!navContainer) {
      let oldContainer = sidebar.querySelector('.flex-1.overflow-y-auto') || sidebar.querySelector('.flex-1.px-2');
      if (oldContainer) {
        navContainer = oldContainer;
        navContainer.className = 'cw-sidebar-nav-container flex-1 px-2 space-y-1 overflow-y-auto overflow-x-hidden';
      } else {
        navContainer = document.createElement('div');
        navContainer.className = 'cw-sidebar-nav-container flex-1 px-2 space-y-1 overflow-y-auto overflow-x-hidden';
        sidebar.appendChild(navContainer);
      }
    }

    const isItemActive = (id) => activeRoute === id;

    const baseClass = 'cw-nav-item flex items-center gap-3 px-4 py-3 rounded-lg transition-all cursor-pointer select-none';
    const activeClass = 'cw-nav-active bg-surface-container text-primary font-semibold border-r-4 border-primary rounded-r-none';
    const inactiveClass = 'text-on-surface-variant hover:bg-surface-container/60 hover:text-on-surface';

    navContainer.innerHTML = `
      <!-- Main Core Navigation -->
      <div class="space-y-1 cw-main-nav-group">
        <a href="/" data-nav="dashboard" title="Dashboard" class="${baseClass} ${isItemActive('dashboard') ? activeClass : inactiveClass}">
          <span class="cw-nav-icon flex items-center justify-center shrink-0 w-6 h-6">${ICONS.dashboard}</span>
          <span class="text-label-md cw-sidebar-label font-medium tracking-wide">Dashboard</span>
        </a>
        <a href="/outreach" data-nav="outreach" title="Outreach Queue" class="${baseClass} ${isItemActive('outreach') ? activeClass : inactiveClass}">
          <span class="cw-nav-icon flex items-center justify-center shrink-0 w-6 h-6">${ICONS.outreach}</span>
          <span class="text-label-md cw-sidebar-label font-medium tracking-wide">Outreach Queue</span>
        </a>
        <a href="/analytics" data-nav="analytics" title="Analytics" class="${baseClass} ${isItemActive('analytics') ? activeClass : inactiveClass}">
          <span class="cw-nav-icon flex items-center justify-center shrink-0 w-6 h-6">${ICONS.analytics}</span>
          <span class="text-label-md cw-sidebar-label font-medium tracking-wide">Analytics</span>
        </a>
      </div>

      <!-- WORKLOAD QUEUES Section -->
      <div class="cw-workload-section pt-5 pb-1">
        <div class="cw-section-header px-4 pb-2 text-[11px] font-bold tracking-wider text-outline uppercase select-none">
          WORKLOAD QUEUES
        </div>
        <div class="cw-section-divider my-2 mx-auto w-8 border-t border-outline-variant hidden"></div>

        <div class="space-y-1">
          <!-- High Priority Queue -->
          <a href="/outreach?priority=High+Priority" data-nav="high-priority" title="High Priority (${formatNumber(liveCounts.highPriority)} members)" class="${baseClass} ${isItemActive('high-priority') ? activeClass : inactiveClass} justify-between">
            <div class="flex items-center gap-3 min-w-0">
              <div class="cw-nav-icon relative flex items-center justify-center shrink-0 w-6 h-6 text-[#ba1a1a]">
                ${ICONS.alertTriangle}
                <span data-dot="high-priority" class="cw-status-dot absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#ba1a1a] border-2 border-white shadow-xs hidden"></span>
              </div>
              <span class="text-label-md cw-sidebar-label font-medium tracking-wide truncate">High Priority</span>
            </div>
            <span data-badge="high-priority" class="cw-counter-badge inline-flex items-center justify-center px-2 py-0.5 min-w-[24px] text-[11px] font-bold rounded-full text-white bg-[#ba1a1a] leading-tight shadow-xs transition-transform hover:scale-105">
              ${formatNumber(liveCounts.highPriority)}
            </span>
          </a>

          <!-- Follow-ups Queue -->
          <a href="/outreach?status=Follow-up" data-nav="follow-ups" title="Follow-ups (${formatNumber(liveCounts.followUps)} members)" class="${baseClass} ${isItemActive('follow-ups') ? activeClass : inactiveClass} justify-between">
            <div class="flex items-center gap-3 min-w-0">
              <div class="cw-nav-icon relative flex items-center justify-center shrink-0 w-6 h-6 text-[#ea580c]">
                ${ICONS.clock}
                <span data-dot="follow-ups" class="cw-status-dot absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#ea580c] border-2 border-white shadow-xs hidden"></span>
              </div>
              <span class="text-label-md cw-sidebar-label font-medium tracking-wide truncate">Follow-ups</span>
            </div>
            <span data-badge="follow-ups" class="cw-counter-badge inline-flex items-center justify-center px-2 py-0.5 min-w-[24px] text-[11px] font-bold rounded-full text-white bg-[#ea580c] leading-tight shadow-xs transition-transform hover:scale-105">
              ${formatNumber(liveCounts.followUps)}
            </span>
          </a>

          <!-- Completed Queue -->
          <a href="/outreach?status=Completed" data-nav="completed" title="Completed (${formatNumber(liveCounts.completed)} members)" class="${baseClass} ${isItemActive('completed') ? activeClass : inactiveClass} justify-between">
            <div class="flex items-center gap-3 min-w-0">
              <div class="cw-nav-icon relative flex items-center justify-center shrink-0 w-6 h-6 text-[#16a34a]">
                ${ICONS.checkCircle2}
                <span data-dot="completed" class="cw-status-dot absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#16a34a] border-2 border-white shadow-xs hidden"></span>
              </div>
              <span class="text-label-md cw-sidebar-label font-medium tracking-wide truncate">Completed</span>
            </div>
            <span data-badge="completed" class="cw-counter-badge inline-flex items-center justify-center px-2 py-0.5 min-w-[24px] text-[11px] font-bold rounded-full text-white bg-[#16a34a] leading-tight shadow-xs transition-transform hover:scale-105">
              ${formatNumber(liveCounts.completed)}
            </span>
          </a>
        </div>
      </div>
    `;

    // Render User Profile / Logout footer at bottom of sidebar
    let profileFooter = sidebar.querySelector('.cw-user-profile-section');
    if (!profileFooter) {
      profileFooter = document.createElement('div');
      profileFooter.className = 'cw-user-profile-section border-t border-outline-variant/40 px-3 py-3 mt-auto bg-surface-container-lowest';
      sidebar.appendChild(profileFooter);
    }

    const userName = currentUser?.full_name || currentUser?.username || 'Care Manager';
    const userRole = currentUser?.role || 'Staff';
    const initials = getInitials(userName);

    profileFooter.innerHTML = `
      <div class="flex items-center justify-between gap-2.5 p-2 rounded-xl bg-surface-container-low/70 border border-outline-variant/30 hover:bg-surface-container transition group">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="cw-user-avatar flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-white font-bold text-xs shrink-0 shadow-xs">
            ${escapeHtml(initials)}
          </div>
          <div class="cw-user-meta min-w-0">
            <div class="text-xs font-semibold text-on-surface truncate cw-sidebar-label">${escapeHtml(userName)}</div>
            <div class="text-[10px] text-outline font-medium truncate cw-sidebar-label uppercase tracking-wider">${escapeHtml(userRole)}</div>
          </div>
        </div>
        <button
          type="button"
          onclick="window.carewiseLogout()"
          title="Sign Out"
          class="cw-logout-btn flex items-center justify-center w-7 h-7 rounded-lg text-outline hover:text-[#ba1a1a] hover:bg-[#ba1a1a]/10 transition shrink-0"
          aria-label="Sign out of Care Management Outreach Portal"
        >
          ${ICONS.logout}
        </button>
      </div>
    `;
  };

  const initialize = () => {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;

    const logo = sidebar.querySelector('.cw-sidebar-logo');
    if (logo && !logo.querySelector('img')) {
      logo.innerHTML = '<img src="/static/brand-mark.svg" alt="Care Management Outreach Prioritization Assistant Logo" class="cw-brand-mark">';
    }

    const brand = sidebar.querySelector('.px-6.mb-8') || sidebar.querySelector('.px-6.mb-6') || sidebar.querySelector('.cw-sidebar-brand');
    if (brand) brand.classList.add('cw-sidebar-brand');

    // Add toggle button if not already present
    if (!sidebar.querySelector('[data-sidebar-toggle]')) {
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'cw-sidebar-toggle';
      toggle.setAttribute('data-sidebar-toggle', '');
      toggle.innerHTML = ICONS.menu;
      toggle.addEventListener('click', () => {
        const next = !document.body.classList.contains(collapsedClass);
        localStorage.setItem(storageKey, String(next));
        applyState(next);
      });
      sidebar.prepend(toggle);
    }

    // Render modern workload navigation structure & user profile
    renderSidebarContent(sidebar);

    // Apply collapsed state from localStorage
    applyState(localStorage.getItem(storageKey) === 'true');

    // Fetch initial live counts
    fetchLiveCounts();

    // Listen for cross-app updates
    window.addEventListener('carewise:status-updated', fetchLiveCounts);
    window.addEventListener('focus', fetchLiveCounts);
    setInterval(fetchLiveCounts, 30000);
  };

  const style = document.createElement('style');
  style.textContent = `
    :root {
      --primary: #00685f;
      --error: #ba1a1a;
      --secondary: #006591;
      --surface-container: #e5eeff;
      --surface-container-lowest: #ffffff;
      --outline-variant: #bcc9c6;
    }
    @media (min-width: 768px) {
      [data-sidebar] { width: 280px !important; transition: width 220ms cubic-bezier(0.4, 0, 0.2, 1); overflow-x: hidden; }
      [data-sidebar-main] { margin-left: 280px !important; transition: margin-left 220ms cubic-bezier(0.4, 0, 0.2, 1); }
      .cw-sidebar-toggle { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; margin: 0 0 12px 18px; border-radius: 9999px; color: var(--primary, #00685f); transition: background-color 160ms ease; border: none; background: transparent; cursor: pointer; }
      .cw-sidebar-toggle:hover, .cw-sidebar-toggle:focus-visible { background: #eff4ff; outline: none; }
      .cw-brand-mark { width: 34px; height: 34px; object-fit: contain; }
      .cw-sidebar-brand, .cw-sidebar-label, .cw-counter-badge, .cw-section-header { transition: opacity 160ms ease, max-width 220ms ease, transform 160ms ease; }
      
      /* Collapsed State Styling */
      body.${collapsedClass} [data-sidebar] { width: 76px !important; }
      body.${collapsedClass} [data-sidebar-main] { margin-left: 76px !important; }
      body.${collapsedClass} .cw-sidebar-toggle { margin-left: 18px; }
      body.${collapsedClass} .cw-sidebar-brand { padding-left: 18px; padding-right: 18px; gap: 0; }
      body.${collapsedClass} .cw-sidebar-brand > :not(.cw-sidebar-logo) { opacity: 0; max-width: 0; overflow: hidden; display: none; }
      body.${collapsedClass} .cw-sidebar-label { opacity: 0; max-width: 0; overflow: hidden; white-space: nowrap; display: none; }
      body.${collapsedClass} .cw-counter-badge { opacity: 0; max-width: 0; overflow: hidden; display: none; }
      body.${collapsedClass} .cw-section-header { opacity: 0; max-width: 0; overflow: hidden; display: none; }
      body.${collapsedClass} .cw-section-divider { display: block !important; }
      body.${collapsedClass} .cw-status-dot { display: block !important; }
      body.${collapsedClass} .cw-nav-item { justify-content: center !important; padding-left: 0 !important; padding-right: 0 !important; }
      body.${collapsedClass} .cw-nav-active { border-right: 4px solid var(--primary, #00685f) !important; }
      body.${collapsedClass} .cw-user-profile-section { padding-left: 8px; padding-right: 8px; }
      body.${collapsedClass} .cw-logout-btn { margin: 0 auto; }
    }
  `;
  document.head.append(style);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();

