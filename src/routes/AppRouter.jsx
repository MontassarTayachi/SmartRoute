import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import AdminLayout from '../layouts/AdminLayout';
import DriverLayout from '../layouts/DriverLayout';
import ManagerLayout from '../layouts/ManagerLayout';
import DashboardPage from '../pages/DashboardPage';
import DriversPage from '../pages/DriversPage';
import Login from '../pages/Login';
import NotFound from '../pages/NotFound';
import Unauthorized from '../pages/Unauthorized';
import UsersPage from '../pages/UsersPage';
import VehiclesPage from '../pages/VehiclesPage';

const AppRouter = () => (
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/unauthorized" element={<Unauthorized />} />

    <Route
      path="/admin"
      element={
        <ProtectedRoute allowedRoles={['ADMIN']}>
          <AdminLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage title="Dashboard administrateur" description="Vue globale des utilisateurs, véhicules et conducteurs." />} />
      <Route path="users" element={<UsersPage />} />
      <Route path="vehicles" element={<VehiclesPage />} />
      <Route path="drivers" element={<DriversPage />} />
      <Route path="settings" element={<DashboardPage title="Paramètres" description="Configuration de la plateforme." />} />
    </Route>

    <Route
      path="/manager"
      element={
        <ProtectedRoute allowedRoles={['MANAGER']}>
          <ManagerLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage title="Dashboard gestionnaire" description="Pilotage opérationnel de la flotte et des conducteurs." />} />
      <Route path="vehicles" element={<VehiclesPage />} />
      <Route path="drivers" element={<DriversPage />} />
      <Route path="deliveries" element={<DashboardPage title="Livraisons" description="Module à prévoir pour la suite du projet." />} />
    </Route>

    <Route
      path="/driver"
      element={
        <ProtectedRoute allowedRoles={['DRIVER']}>
          <DriverLayout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage title="Dashboard conducteur" description="Vue de mission et statut personnel." />} />
      <Route path="profile" element={<DashboardPage title="Profil conducteur" description="Fiche personnelle du conducteur." />} />
      <Route path="missions" element={<DashboardPage title="Missions" description="Module à prévoir pour la suite du projet." />} />
    </Route>

    <Route path="/" element={<Navigate to="/login" replace />} />
    <Route path="*" element={<NotFound />} />
  </Routes>
);

export default AppRouter;
