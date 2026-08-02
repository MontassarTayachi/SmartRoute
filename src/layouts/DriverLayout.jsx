import { Outlet } from 'react-router-dom';
import RoleLayout from './RoleLayout';

const items = [
  { to: '/driver/profile', label: 'Profil' },
  { to: '/driver/tracking', label: 'Suivi GPS' },
  { to: '/driver/missions', label: 'Missions' },
];

const DriverLayout = () => (
  <RoleLayout role="Conducteur" roleCode="DRIVER" title="Espace conducteur" items={items}>
    <Outlet />
  </RoleLayout>
);

export default DriverLayout;
