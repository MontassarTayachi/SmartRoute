import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import RoleBadge from '../components/RoleBadge';
import { useToast } from '../context/ToastContext';
import { getDriversWithoutUserAccount } from '../services/driverService';
import { createDriverAccount, createUser, deleteUser, getUsers, updateUser } from '../services/userService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', driverId: '', name: '', email: '', password: '', role: 'dispatcher' };

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

const UsersPage = () => {
  const toast = useToast();
  const [users, setUsers] = useState([]);
  const [driversWithoutAccount, setDriversWithoutAccount] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [loadingDrivers, setLoadingDrivers] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await getUsers({ page: 1, size: 25 });
      setUsers(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les utilisateurs'));
    } finally {
      setLoading(false);
    }
  };

  const loadDriversWithoutAccount = async () => {
    setLoadingDrivers(true);
    try {
      const data = await getDriversWithoutUserAccount({ page: 1, size: 10 });
      const nextList = Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? [];
      setDriversWithoutAccount(nextList);
      window.dispatchEvent(
        new CustomEvent('pending-driver-accounts-updated', {
          detail: { count: readTotalCount(data) },
        }),
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les conducteurs sans compte'));
    } finally {
      setLoadingDrivers(false);
    }
  };

  useEffect(() => {
    loadUsers();
    loadDriversWithoutAccount();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openCreateForDriver = (driver) => {
    setForm({
      ...emptyForm,
      driverId: driver.id ?? '',
      name: driver.fullName ?? '',
      role: 'driver',
    });
    setModalOpen(true);
  };

  const openEdit = (user) => {
    setForm({ ...emptyForm, ...user, password: '' });
    setModalOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const payload = {
        name: form.name,
        email: form.email,
        role: form.role,
      };

      if (form.password) {
        payload.password = form.password;
      }

      if (form.id) {
        await updateUser(form.id, payload);
        toast.success('Utilisateur mis à jour');
      } else if (form.driverId) {
        await createDriverAccount({
          driverId: form.driverId,
          name: form.name,
          email: form.email,
          password: form.password,
          isActive: true,
        });
        toast.success('Compte conducteur créé');
      } else {
        await createUser({ ...payload, password: form.password });
        toast.success('Utilisateur créé');
      }

      setModalOpen(false);
      setForm(emptyForm);
      await loadUsers();
      await loadDriversWithoutAccount();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Opération utilisateur impossible'));
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteUser(id);
      toast.success('Utilisateur désactivé');
      await loadUsers();
      await loadDriversWithoutAccount();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Suppression impossible'));
    }
  };

  return (
    <section className="resource-page">
      <div className="resource-header">
        <div>
          <h1>Utilisateurs</h1>
          <p>Administration des comptes.</p>
        </div>
        <div className="resource-actions">
          <button type="button" className="btn-primary" onClick={openCreate}>
            Nouvel utilisateur
          </button>
        </div>
      </div>
      {loading ? <p className="loading-row">Chargement…</p> : null}
      <div className="resource-table-wrapper">
        <table className="resource-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Rôle</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>
                  <RoleBadge role={user.role} />
                </td>
                <td>
                  <div className="table-actions">
                    <button type="button" className="icon-button icon-button-edit" onClick={() => openEdit(user)}>
                      Editer
                    </button>
                    <button type="button" className="icon-button icon-button-delete" onClick={() => handleDelete(user.id)}>
                      Supprimer
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="users-notification-section">
        <div className="users-notification-title-row">
          <h2>Conducteurs sans compte utilisateur</h2>
          {driversWithoutAccount.length > 0 ? (
            <span className="users-notification-badge">{driversWithoutAccount.length}</span>
          ) : null}
        </div>
        <p>Ces conducteurs n&apos;ont pas encore de compte de connexion.</p>
        {loadingDrivers ? <p className="loading-row">Chargement…</p> : null}
        {!loadingDrivers && driversWithoutAccount.length === 0 ? (
          <p className="loading-row">Aucun conducteur en attente de compte.</p>
        ) : null}
        {!loadingDrivers && driversWithoutAccount.length > 0 ? (
          <div className="resource-table-wrapper">
            <table className="resource-table">
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>Téléphone</th>
                  <th>Permis</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {driversWithoutAccount.map((driver) => (
                  <tr key={driver.id}>
                    <td>{driver.fullName}</td>
                    <td>{driver.phone ?? '-'}</td>
                    <td>{driver.licenseNumber ?? '-'}</td>
                    <td>
                      <button type="button" className="icon-button icon-button-assign" onClick={() => openCreateForDriver(driver)}>
                        Créer le compte
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {modalOpen ? (
        <Modal title={form.id ? 'Modifier un utilisateur' : 'Créer un utilisateur'} onClose={() => setModalOpen(false)}>
          <form className="resource-form" onSubmit={handleSubmit}>
            <input className="input-glass" placeholder="Nom" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            <input className="input-glass" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <input className="input-glass" placeholder="Mot de passe" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            <select
              className="input-glass"
              value={form.role}
              disabled={Boolean(form.driverId)}
              onChange={(event) => setForm({ ...form, role: event.target.value })}
            >
              <option value="admin">ADMIN</option>
              <option value="dispatcher">DISPATCHER</option>
              <option value="driver">DRIVER</option>
            </select>
            <div className="modal-footer">
              <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
                Annuler
              </button>
              <button className="btn-primary" type="submit">
                Enregistrer
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </section>
  );
};

export default UsersPage;
