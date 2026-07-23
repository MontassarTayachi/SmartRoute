import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { getDriversWithoutUserAccount } from '../services/driverService';
import AppIcon from './AppIcon';
import RoleBadge from './RoleBadge';

const DashboardIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="4" />
    <rect x="14" y="12" width="7" height="9" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);

const UsersIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);

const VehicleIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="8" width="18" height="8" rx="2" />
    <path d="M19 10h2a2 2 0 0 1 2 2v4h-4" />
    <circle cx="6" cy="18" r="2" />
    <circle cx="18" cy="18" r="2" />
  </svg>
);

const DriverIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="7" r="4" />
    <path d="M5.5 21a6.5 6.5 0 0 1 13 0" />
  </svg>
);

const DeliveryIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 7h13v10H3z" />
    <path d="M16 10h3l2 2v5h-5z" />
    <circle cx="7" cy="18" r="2" />
    <circle cx="18" cy="18" r="2" />
  </svg>
);

const TrackingIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <circle cx="12" cy="12" r="8" />
    <path d="M12 2v3" />
    <path d="M12 19v3" />
    <path d="M2 12h3" />
    <path d="M19 12h3" />
  </svg>
);

const MissionIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7z" />
  </svg>
);

const ProfileIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="7" r="4" />
    <path d="M5.5 21a6.5 6.5 0 0 1 13 0" />
  </svg>
);

const SettingsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.33 1V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-.33-1 1.65 1.65 0 0 0-1-.6 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1-.33H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1-.33 1.65 1.65 0 0 0 .6-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .33-1V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 .33 1 1.65 1.65 0 0 0 1 .6 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.24.37.37.8.37 1.24 0 .44-.13.87-.37 1.24a1.65 1.65 0 0 0 0 1.52c.24.37.37.8.37 1.24 0 .44-.13.87-.37 1.24z" />
  </svg>
);

const getItemIcon = (item) => {
  if (item.to.includes('dashboard')) return <DashboardIcon />;
  if (item.to.includes('users')) return <UsersIcon />;
  if (item.to.includes('vehicles')) return <VehicleIcon />;
  if (item.to.includes('drivers')) return <DriverIcon />;
  if (item.to.includes('deliveries')) return <DeliveryIcon />;
  if (item.to.includes('tracking')) return <TrackingIcon />;
  if (item.to.includes('missions')) return <MissionIcon />;
  if (item.to.includes('profile')) return <ProfileIcon />;
  if (item.to.includes('settings')) return <SettingsIcon />;
  return <DashboardIcon />;
};

const readTotalCount = (payload) => {
  if (!payload || typeof payload !== 'object') {
    return 0;
  }

  const total = payload.total ?? payload.totalItems ?? payload.total_count ?? payload.totalCount;
  if (typeof total === 'number' && Number.isFinite(total)) {
    return total;
  }

  const list = payload.items ?? payload.results ?? payload.data;
  return Array.isArray(list) ? list.length : 0;
};

const Sidebar = ({ role, roleCode, items, isCollapsed, isMobileOpen, onNavigate }) => {
  const [pendingAccountCount, setPendingAccountCount] = useState(0);

  useEffect(() => {
    if (roleCode !== 'ADMIN') {
      setPendingAccountCount(0);
      return;
    }

    const loadPendingAccounts = async () => {
      try {
        const data = await getDriversWithoutUserAccount({ page: 1, size: 10 });
        setPendingAccountCount(readTotalCount(data));
      } catch {
        setPendingAccountCount(0);
      }
    };

    loadPendingAccounts();

    const handlePendingCountEvent = (event) => {
      if (typeof event?.detail?.count === 'number' && Number.isFinite(event.detail.count)) {
        setPendingAccountCount(event.detail.count);
      }
    };

    window.addEventListener('pending-driver-accounts-updated', handlePendingCountEvent);
    return () => window.removeEventListener('pending-driver-accounts-updated', handlePendingCountEvent);
  }, [roleCode]);

  return (
    <aside className={`app-sidebar ${isCollapsed ? 'app-sidebar-collapsed' : ''} ${isMobileOpen ? 'app-sidebar-mobile-open' : ''}`}>
      <div className="sidebar-brand">
        <AppIcon size={30} className="brand-logo" />
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">SmartRoute</span>
          <RoleBadge role={roleCode} />
        </div>
      </div>

      <nav className="sidebar-nav" aria-label={role}>
        {items.map((item) => {
          const showPendingBadge = roleCode === 'ADMIN' && item.to.includes('users') && pendingAccountCount > 0;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className="sidebar-link"
              onClick={onNavigate}
              title={isCollapsed ? item.label : undefined}
            >
              <span className="sidebar-link-icon" aria-hidden="true">{getItemIcon(item)}</span>
              <span className="sidebar-link-label">{item.label}</span>
              {showPendingBadge ? (
                <span className="sidebar-link-notification" aria-label={`${pendingAccountCount} conducteur(s) sans compte`}>
                  {pendingAccountCount > 99 ? '99+' : pendingAccountCount}
                </span>
              ) : null}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;
