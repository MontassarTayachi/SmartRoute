import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';
import { assignVehicle, createDriver, getDrivers, updateDriver } from '../services/driverService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', fullName: '', phone: '', licenseNumber: '', vehicleId: '' };

const DriversPage = () => {
  const toast = useToast();
  const [drivers, setDrivers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const loadDrivers = async () => {
    setLoading(true);
    try {
      const data = await getDrivers({ page: 1 });
      setDrivers(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les conducteurs'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrivers();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openEdit = (driver) => {
    setForm({
      id: driver.id,
      fullName: driver.fullName ?? '',
      phone: driver.phone ?? '',
      licenseNumber: driver.licenseNumber ?? '',
      vehicleId: form.vehicleId,
    });
    setModalOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const payload = {
      fullName: form.fullName,
      phone: form.phone,
      licenseNumber: form.licenseNumber,
    };

    try {
      if (form.id) {
        await updateDriver(form.id, payload);
        toast.success('Conducteur mis à jour');
      } else {
        await createDriver(payload);
        toast.success('Conducteur créé');
      }
      setModalOpen(false);
      setForm(emptyForm);
      await loadDrivers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Opération conducteur impossible'));
    }
  };

  const handleAssign = async (driverId) => {
    if (!form.vehicleId) {
      toast.error('Renseignez un identifiant de véhicule');
      return;
    }

    try {
      await assignVehicle(driverId, form.vehicleId);
      toast.success('Véhicule affecté');
      await loadDrivers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Affectation impossible'));
    }
  };

  return (
    <section className="resource-page">
      <div className="resource-header">
        <div>
          <h1>Conducteurs</h1>
          <p>Gestion et affectation des conducteurs.</p>
        </div>
        <div className="resource-actions">
          <button type="button" className="btn-primary" onClick={openCreate}>
            Nouveau conducteur
          </button>
        </div>
      </div>
      {loading ? <p className="loading-row">Chargement…</p> : null}
      <div className="resource-table-wrapper">
        <table className="resource-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Téléphone</th>
              <th>Permis</th>
              <th>Disponible</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver) => (
              <tr key={driver.id}>
                <td>{driver.fullName}</td>
                <td>{driver.phone}</td>
                <td>{driver.licenseNumber}</td>
                <td>
                  <StatusBadge
                    status={driver.isAvailable ? 'ACTIVE' : 'INACTIVE'}
                    label={driver.isAvailable ? 'Disponible' : 'Indisponible'}
                  />
                </td>
                <td>
                  <div className="table-actions">
                    <button type="button" className="icon-button icon-button-edit" onClick={() => openEdit(driver)}>
                      Editer
                    </button>
                    <button type="button" className="icon-button icon-button-assign" onClick={() => handleAssign(driver.id)}>
                      Affecter
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <Modal title={form.id ? 'Modifier un conducteur' : 'Créer un conducteur'} onClose={() => setModalOpen(false)}>
          <form className="resource-form" onSubmit={handleSubmit}>
            <input className="input-glass" placeholder="Nom complet" value={form.fullName} onChange={(event) => setForm({ ...form, fullName: event.target.value })} />
            <input className="input-glass" placeholder="Téléphone" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            <input className="input-glass" placeholder="Numéro de permis" value={form.licenseNumber} onChange={(event) => setForm({ ...form, licenseNumber: event.target.value })} />
            <div className="modal-footer">
              <button type="button" className="btn-ghost" onClick={() => setModalOpen(false)}>
                Annuler
              </button>
              <button className="btn-primary" type="submit">
                Enregistrer
              </button>
            </div>
          </form>
          <div className="assign-panel">
            <span className="assign-panel-label">Affecter un véhicule</span>
            <input
              className="input-glass"
              placeholder="Vehicle ID"
              value={form.vehicleId}
              onChange={(event) => setForm({ ...form, vehicleId: event.target.value })}
            />
          </div>
        </Modal>
      ) : null}
    </section>
  );
};

export default DriversPage;
