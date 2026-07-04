const roleClassMap = {
  ADMIN: 'badge-role-admin',
  MANAGER: 'badge-role-manager',
  DRIVER: 'badge-role-driver',
};

const RoleBadge = ({ role }) => (
  <span className={`badge ${roleClassMap[role] ?? 'badge-info'}`}>{role ?? 'N/A'}</span>
);

export default RoleBadge;
