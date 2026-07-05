import { useEffect, useState } from 'react';
import AppHeader from '../components/AppHeader';
import Sidebar from '../components/Sidebar';

const MOBILE_BREAKPOINT = 1024;

const RoleLayout = ({ role, roleCode, items, title, children }) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(
    typeof window !== 'undefined' ? window.innerWidth <= MOBILE_BREAKPOINT : false,
  );

  useEffect(() => {
    const onResize = () => {
      setIsMobileViewport(window.innerWidth <= MOBILE_BREAKPOINT);
      if (window.innerWidth > MOBILE_BREAKPOINT) {
        setIsMobileSidebarOpen(false);
      }
    };

    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleToggleSidebar = () => {
    if (window.innerWidth <= MOBILE_BREAKPOINT) {
      setIsMobileSidebarOpen((prev) => !prev);
      return;
    }

    setIsSidebarCollapsed((prev) => !prev);
  };

  const closeMobileSidebar = () => setIsMobileSidebarOpen(false);

  return (
    <div className={`role-layout ${isSidebarCollapsed ? 'role-layout-collapsed' : ''}`}>
      <Sidebar
        role={role}
        roleCode={roleCode}
        items={items}
        isCollapsed={isSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        onNavigate={closeMobileSidebar}
      />
      {isMobileSidebarOpen ? (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="Fermer le menu"
          onClick={closeMobileSidebar}
        />
      ) : null}
      <div className="role-layout-main">
        <AppHeader
          title={title}
          onToggleSidebar={handleToggleSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
          isMobileSidebarOpen={isMobileSidebarOpen}
          isMobileViewport={isMobileViewport}
        />
        <main className="role-layout-content">{children}</main>
      </div>
    </div>
  );
};

export default RoleLayout;
