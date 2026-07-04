import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import RoleBadge from '../components/RoleBadge';
import { useToast } from '../context/ToastContext';
import { createUser, deleteUser, getUsers, updateUser } from '../services/userService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', name: '', email: '', password: '', role: 'MANAGER' };

const UsersPage = () => {
  const toast = useToast();
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    loadUsers();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
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
      } else {
        await createUser({ ...payload, password: form.password });
        toast.success('Utilisateur créé');
      }

      setModalOpen(false);
      setForm(emptyForm);
      await loadUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Opération utilisateur impossible'));
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteUser(id);
      toast.success('Utilisateur désactivé');
      await loadUsers();
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

      {modalOpen ? (
        <Modal title={form.id ? 'Modifier un utilisateur' : 'Créer un utilisateur'} onClose={() => setModalOpen(false)}>
          <form className="resource-form" onSubmit={handleSubmit}>
            <input className="input-glass" placeholder="Nom" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            <input className="input-glass" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <input className="input-glass" placeholder="Mot de passe" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            <select className="input-glass" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
              <option value="ADMIN">ADMIN</option>
              <option value="MANAGER">MANAGER</option>
              <option value="DRIVER">DRIVER</option>
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
