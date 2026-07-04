import AppHeader from '../components/AppHeader';
import Sidebar from '../components/Sidebar';

const RoleLayout = ({ role, roleCode, items, title, children }) => (
  <div className="role-layout">
    <Sidebar role={role} roleCode={roleCode} items={items} />
    <div className="role-layout-main">
      <AppHeader title={title} />
      <main className="role-layout-content">{children}</main>
    </div>
  </div>
);

export default RoleLayout;
