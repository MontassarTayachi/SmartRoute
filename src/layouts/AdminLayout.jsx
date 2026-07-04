import { Outlet } from 'react-router-dom';
import RoleLayout from './RoleLayout';

const items = [
  { to: '/admin/dashboard', label: 'Dashboard', end: true },
  { to: '/admin/users', label: 'Utilisateurs' },
  { to: '/admin/vehicles', label: 'Véhicules' },
  { to: '/admin/drivers', label: 'Conducteurs' },
  { to: '/admin/settings', label: 'Paramètres' },
];

const AdminLayout = () => (
  <RoleLayout role="Administrateur" roleCode="ADMIN" title="Espace administrateur" items={items}>
    <Outlet />
  </RoleLayout>
);

export default AdminLayout;
