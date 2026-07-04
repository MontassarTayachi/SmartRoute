import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';
import { createVehicle, deleteVehicle, getVehicles, updateVehicle } from '../services/vehicleService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', registration: '', type: '', capacityKg: '', avgFuelConsumption: '' };

const VehiclesPage = () => {
  const toast = useToast();
  const [vehicles, setVehicles] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const data = await getVehicles({ page: 1 });
      setVehicles(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les véhicules'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openEdit = (vehicle) => {
    setForm({
      id: vehicle.id,
      registration: vehicle.registration ?? '',
      type: vehicle.type ?? '',
      capacityKg: vehicle.capacityKg ?? '',
      avgFuelConsumption: vehicle.avgFuelConsumption ?? '',
    });
    setModalOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const payload = {
      registration: form.registration,
      type: form.type,
      capacityKg: Number(form.capacityKg),
      avgFuelConsumption: Number(form.avgFuelConsumption),
    };

    try {
      if (form.id) {
        await updateVehicle(form.id, payload);
        toast.success('Véhicule mis à jour');
      } else {
        await createVehicle(payload);
        toast.success('Véhicule créé');
      }
      setModalOpen(false);
      setForm(emptyForm);
      await loadVehicles();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Opération véhicule impossible'));
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteVehicle(id);
      toast.success('Véhicule supprimé');
      await loadVehicles();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Suppression impossible'));
    }
  };

  return (
    <section className="resource-page">
      <div className="resource-header">
        <div>
          <h1>Véhicules</h1>
          <p>Gestion du parc roulant.</p>
        </div>
        <div className="resource-actions">
          <button type="button" className="btn-primary" onClick={openCreate}>
            Nouveau véhicule
          </button>
        </div>
      </div>
      {loading ? <p className="loading-row">Chargement…</p> : null}
      <div className="resource-table-wrapper">
        <table className="resource-table">
          <thead>
            <tr>
              <th>Immatriculation</th>
              <th>Type</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((vehicle) => (
              <tr key={vehicle.id}>
                <td>{vehicle.registration}</td>
                <td>{vehicle.type}</td>
                <td>
                  <StatusBadge status={vehicle.status} label={vehicle.status ?? 'N/A'} />
                </td>
                <td>
                  <div className="table-actions">
                    <button type="button" className="icon-button icon-button-edit" onClick={() => openEdit(vehicle)}>
                      Editer
                    </button>
                    <button type="button" className="icon-button icon-button-delete" onClick={() => handleDelete(vehicle.id)}>
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
        <Modal title={form.id ? 'Modifier un véhicule' : 'Créer un véhicule'} onClose={() => setModalOpen(false)}>
          <form className="resource-form" onSubmit={handleSubmit}>
            <input className="input-glass" placeholder="Immatriculation" value={form.registration} onChange={(event) => setForm({ ...form, registration: event.target.value })} />
            <input className="input-glass" placeholder="Type" value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })} />
            <input className="input-glass" placeholder="Capacité (kg)" type="number" value={form.capacityKg} onChange={(event) => setForm({ ...form, capacityKg: event.target.value })} />
            <input className="input-glass" placeholder="Conso moyenne" type="number" value={form.avgFuelConsumption} onChange={(event) => setForm({ ...form, avgFuelConsumption: event.target.value })} />
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

export default VehiclesPage;
