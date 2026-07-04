import { NavLink } from 'react-router-dom';
import AppIcon from './AppIcon';
import RoleBadge from './RoleBadge';

const Sidebar = ({ role, roleCode, items }) => (
  <aside className="app-sidebar">
    <div className="sidebar-brand">
      <AppIcon size={30} className="brand-logo" />
      <div className="sidebar-brand-text">
        <span className="sidebar-brand-name">SmartRoute</span>
        <RoleBadge role={roleCode} />
      </div>
    </div>

    <nav className="sidebar-nav" aria-label={role}>
      {items.map((item) => (
        <NavLink key={item.to} to={item.to} end={item.end} className="sidebar-link">
          <span className="sidebar-link-dot" aria-hidden="true" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  </aside>
);

export default Sidebar;
