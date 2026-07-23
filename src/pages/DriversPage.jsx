import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';
import {
  assignVehicle,
  unassignVehicle,
  createDriver,
  getDrivers,
  updateDriver,
} from '../services/driverService';
import { getAvailableVehicles } from '../services/vehicleService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', fullName: '', phone: '', licenseNumber: '' };

const DriversPage = () => {
  const toast = useToast();
  const [drivers, setDrivers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [dispoVehicles, setDispoVehicles] = useState([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [activeDriverId, setActiveDriverId] = useState(null);

  const loadDrivers = async () => {
    setLoading(true);
    try {
      const data = await getDrivers({ page: 1 });
      setDrivers(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
      console.log('Drivers loaded:', data);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les conducteurs'));
    } finally {
      setLoading(false);
    }
  };

  const loadDispoVehicles = async () => {
    try {
      const dispoData = await getAvailableVehicles({ page: 1, status: 'available' });
      setDispoVehicles(
        Array.isArray(dispoData) ? dispoData : dispoData?.items ?? dispoData?.results ?? dispoData?.data ?? []
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les véhicules disponibles'));
    }
  };

  useEffect(() => {
    loadDrivers();
    loadDispoVehicles();
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
    });
    setModalOpen(true);
  };

  const openAssign = (driver) => {
    setActiveDriverId(driver.id);
    setSelectedVehicleId(driver.vehicle?._id ?? '');
    setAssignModalOpen(true);
  };

  const closeAssign = () => {
    setAssignModalOpen(false);
    setActiveDriverId(null);
    setSelectedVehicleId('');
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
    if (!selectedVehicleId) {
      toast.error('Sélectionnez un véhicule disponible');
      return;
    }

    try {
      await assignVehicle(driverId, selectedVehicleId);
      toast.success('Véhicule affecté');
      closeAssign();
      await Promise.all([loadDrivers(), loadDispoVehicles()]);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Affectation impossible'));
    }
  };

  const handleUnassign = async (driverId) => {
    try {
      await unassignVehicle(driverId);
      toast.success('Véhicule désaffecté');
      closeAssign();
      await Promise.all([loadDrivers(), loadDispoVehicles()]);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Désaffectation impossible'));
    }
  };

  const activeDriver = drivers.find((driver) => driver.id === activeDriverId);

  return (
    <section className="resource-page">
      <style>{`
        .vehicle-dispo-scroller {
          display: flex;
          gap: 10px;
          overflow-x: auto;
          padding: 6px 2px 10px;
          scroll-snap-type: x proximity;
        }
        .vehicle-dispo-scroller::-webkit-scrollbar {
          height: 6px;
        }
        .vehicle-dispo-scroller::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.18);
          border-radius: 999px;
        }
        .vehicle-dispo-scroller::-webkit-scrollbar-track {
          background: transparent;
        }
        .vehicle-icon-card {
          flex: 0 0 auto;
          scroll-snap-align: start;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          width: 64px;
          padding: 6px 4px;
          background: transparent;
          border: 2px solid transparent;
          border-radius: 12px;
          cursor: pointer;
          transition: border-color 0.15s ease, background 0.15s ease;
        }
        .vehicle-icon-card:hover {
          background: rgba(255, 255, 255, 0.06);
        }
        .vehicle-icon-card-selected {
          border-color: var(--accent, #4f8cff);
          background: rgba(79, 140, 255, 0.1);
        }
        .vehicle-icon-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.08);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .vehicle-icon-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .vehicle-icon-plate {
          font-size: 11px;
          line-height: 1.2;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 60px;
          opacity: 0.85;
        }
        .vehicle-selected-summary {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: 10px;
          padding: 10px;
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.04);
        }
        .vehicle-selected-summary img {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          object-fit: cover;
          flex-shrink: 0;
        }
        .vehicle-selected-summary div {
          display: flex;
          flex-direction: column;
          gap: 2px;
          font-size: 13px;
        }
      `}</style>
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
              <th>Affectation</th>
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
                  {driver.assigned_vehicle_id != null ? (
                    <StatusBadge status="ACTIVE" label={`Affecté`} />
                  ) : (
                    <StatusBadge status="INACTIVE" label="Non affecté" />
                  )}
                </td>
                <td>
                  <div className="table-actions">
                    <button type="button" className="icon-button icon-button-edit" onClick={() => openEdit(driver)}>
                      Editer
                    </button>
                    <button
                      type="button"
                      className="icon-button icon-button-assign"
                      onClick={() => openAssign(driver)}
                    >
                      {driver.vehicle ? 'Modifier affectation' : 'Affecter'}
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
            <input
              className="input-glass"
              placeholder="Nom complet"
              value={form.fullName}
              onChange={(event) => setForm({ ...form, fullName: event.target.value })}
            />
            <input
              className="input-glass"
              placeholder="Téléphone"
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
            />
            <input
              className="input-glass"
              placeholder="Numéro de permis"
              value={form.licenseNumber}
              onChange={(event) => setForm({ ...form, licenseNumber: event.target.value })}
            />
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

      {assignModalOpen ? (
        <Modal title={`Affecter un véhicule · ${activeDriver?.fullName ?? ''}`} onClose={closeAssign}>
          <div className="assign-panel">
            <span className="assign-panel-label">
              {activeDriver?.assigned_vehicle_id != null ? (
                <StatusBadge status="ACTIVE" label={`Actuellement : ${activeDriver.assigned_vehicle?.registration ?? ''}`} />
              ) : (
                <StatusBadge status="INACTIVE" label="Aucun véhicule affecté" />
              )}
            </span>

            <div className="vehicle-dispo-scroller">
              {dispoVehicles.length === 0 ? (
                <p className="loading-row">Aucun véhicule disponible</p>
              ) : (
                dispoVehicles.map((vehicle) => {
                  const isSelected = selectedVehicleId === vehicle._id;
                  return (
                    <button
                      type="button"
                      key={vehicle._id}
                      className={`vehicle-icon-card${isSelected ? ' vehicle-icon-card-selected' : ''}`}
                      onClick={() => setSelectedVehicleId(vehicle._id)}
                      title={`${vehicle.nom} · ${vehicle.registration} · ${vehicle.capacity_kg} kg`}
                    >
                      <span className="vehicle-icon-avatar">
                        <img src={`${import.meta.env.VITE_IMAGE_BASE_URL}${vehicle.image_url}`} alt={vehicle.nom} />
                      </span>
                      <span className="vehicle-icon-plate">{vehicle.registration}</span>
                    </button>
                  );
                })
              )}
            </div>

            {selectedVehicleId ? (
              (() => {
                const picked = dispoVehicles.find((vehicle) => vehicle._id === selectedVehicleId);
                if (!picked) return null;
                return (
                  <div className="vehicle-selected-summary">
                    <img src={`${import.meta.env.VITE_IMAGE_BASE_URL}${picked.image_url}`} alt={picked.nom} />
                    <div>
                      <strong>{picked.nom}</strong>
                      <span>Immatriculation : {picked.registration}</span>
                      <span>Capacité : {picked.capacity_kg} kg</span>
                      <span>Consommation moy. : {picked.avg_fuel_consumption} L/100km</span>
                    </div>
                  </div>
                );
              })()
            ) : null}

            <div className="modal-footer">
              <button type="button" className="btn-ghost" onClick={closeAssign}>
                Annuler
              </button>
              {activeDriver?.assigned_vehicle_id != null ? (
                <button type="button" className="btn-ghost" onClick={() => handleUnassign(activeDriverId)}>
                  Désaffecter
                </button>
              ) : null}
              <button type="button" className="btn-primary" onClick={() => handleAssign(activeDriverId)}>
                Affecter le véhicule
              </button>
            </div>
          </div>
        </Modal>
      ) : null}
    </section>
  );
};

export default DriversPage;