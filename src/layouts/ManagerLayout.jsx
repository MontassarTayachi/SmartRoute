import { Outlet } from 'react-router-dom';
import RoleLayout from './RoleLayout';

const items = [
  { to: '/manager/dashboard', label: 'Dashboard', end: true },
  { to: '/manager/vehicles', label: 'Véhicules' },
  { to: '/manager/drivers', label: 'Conducteurs' },
  { to: '/manager/deliveries', label: 'Livraisons' },
];

const ManagerLayout = () => (
  <RoleLayout role="Gestionnaire logistique" roleCode="MANAGER" title="Espace gestionnaire" items={items}>
    <Outlet />
  </RoleLayout>
);

export default ManagerLayout;
