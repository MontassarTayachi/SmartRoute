import { useAuth } from '../hooks/useAuth';
import RoleBadge from './RoleBadge';

const AppHeader = ({ title }) => {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <span className="header-title">{title}</span>

      <div className="header-right">
        <div className="header-user-chip">
          <span className="header-user-name">{user?.name}</span>
          <RoleBadge role={user?.role} />
        </div>
        <button type="button" className="btn-ghost" onClick={logout}>
          Déconnexion
        </button>
      </div>
    </header>
  );
};

export default AppHeader;
