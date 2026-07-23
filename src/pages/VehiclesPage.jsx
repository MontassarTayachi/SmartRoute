import { useEffect, useState } from 'react';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';
import { createVehicle, deleteVehicle, getVehicleLists, getVehicles, updateVehicle } from '../services/vehicleService';
import { getApiErrorMessage } from '../utils/apiError';

const emptyForm = { id: '', registration: '', vehicleListId: '', status: 'available', capacityKg: '', avgFuelConsumption: '' };

const PLATE_REGEX = /^(\d{1,4})\s*TUN\s*(\d{1,4})$/;

const splitPlate = (value) => {
  const match = PLATE_REGEX.exec((value ?? '').trim());
  return match ? { left: match[1], right: match[2] } : { left: '', right: '' };
};

const joinPlate = (left, right) => {
  if (!left && !right) return '';
  return `${left} TUN ${right}`;
};

const onlyDigits = (value) => value.replace(/\D/g, '').slice(0, 4);

const VehiclesPage = () => {
  const toast = useToast();
  const [vehicles, setVehicles] = useState([]);
  const [vehicleLists, setVehicleLists] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [plate, setPlate] = useState({ left: '', right: '' });
  const [loading, setLoading] = useState(false);
  const [loadingVehicleLists, setLoadingVehicleLists] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [filters, setFilters] = useState({ status: '', vehicleListId: '' });

  const mapVehicleListById = vehicleLists.reduce((acc, item) => {
    if (item?.id) {
      acc[item.id] = {
        name: item.name ?? item.id,
        imageUrl: `${import.meta.env.VITE_IMAGE_BASE_URL}` + (item.imageUrl ?? item.image_url ?? ''),
      };
      console.log(acc)
    }
    return acc;
  }, {});

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const params = { page: 1, size: 25 };
      if (filters.status) {
        params.status = filters.status;
      }
      if (filters.vehicleListId) {
        params.vehicle_list_id = filters.vehicleListId;
      }

      const data = await getVehicles(params);
      setVehicles(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les véhicules'));
    } finally {
      setLoading(false);
    }
  };

  const loadVehicleLists = async () => {
    setLoadingVehicleLists(true);
    try {
      const data = await getVehicleLists({ page: 1, size: 50 });
      setVehicleLists(Array.isArray(data) ? data : data?.items ?? data?.results ?? data?.data ?? []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Impossible de charger les types de véhicules'));
    } finally {
      setLoadingVehicleLists(false);
    }
  };

  useEffect(() => {
    loadVehicleLists();
  }, []);

  useEffect(() => {
    loadVehicles();
  }, [filters]);

  const openCreate = () => {
    setForm(emptyForm);
    setPlate({ left: '', right: '' });
    setModalOpen(true);
  };

  const openEdit = (vehicle) => {
    setForm({
      id: vehicle.id,
      registration: vehicle.registration ?? '',
      vehicleListId: vehicle.vehicleListId ?? '',
      status: vehicle.status ?? 'available',
      capacityKg: vehicle.capacityKg ?? '',
      avgFuelConsumption: vehicle.avgFuelConsumption ?? '',
    });
    setPlate(splitPlate(vehicle.registration));
    setModalOpen(true);
  };

  const handlePlateChange = (side, rawValue) => {
    const digits = onlyDigits(rawValue);
    const nextPlate = { ...plate, [side]: digits };
    setPlate(nextPlate);
    setForm({ ...form, registration: joinPlate(nextPlate.left, nextPlate.right) });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const payload = {
      registration: form.registration,
      vehicleListId: form.vehicleListId,
      status: form.status,
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
      setPlate({ left: '', right: '' });
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
      <style>{`
        .plate-input-group {
          display: flex;
          align-items: center;
          gap: 0;
          border-radius: 8px;
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: rgba(255, 255, 255, 0.03);
        }
        .plate-input-group input {
          border: none;
          background: transparent;
          text-align: center;
          font-weight: 600;
          letter-spacing: 2px;
          width: 100%;
          padding: 10px 8px;
          color: inherit;
          font-size: 15px;
        }
        .plate-input-group input:focus {
          outline: none;
          background: rgba(255, 255, 255, 0.06);
        }
        .plate-input-segment {
          flex: 1 1 0;
          min-width: 0;
        }
        .plate-input-tun {
          flex: 0 0 auto;
          padding: 10px 12px;
          font-weight: 700;
          letter-spacing: 1px;
          background: rgba(79, 140, 255, 0.15);
          border-left: 1px solid rgba(255, 255, 255, 0.15);
          border-right: 1px solid rgba(255, 255, 255, 0.15);
        }
      `}</style>
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
                <td>
                  <div className="vehicle-type-cell">
                    {mapVehicleListById[vehicle.vehicleListId]?.imageUrl ? (
                      <img
                        src={mapVehicleListById[vehicle.vehicleListId].imageUrl}
                        alt=""
                        className="vehicle-type-icon"
                        onError={(event) => {
                          event.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : null}
                    <span>{mapVehicleListById[vehicle.vehicleListId]?.name ?? vehicle.vehicleListId ?? '-'}</span>
                  </div>
                </td>
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
            <div className="plate-input-group">
              <span className="plate-input-segment">
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="****"
                  maxLength={4}
                  value={plate.left}
                  onChange={(event) => handlePlateChange('left', event.target.value)}
                  required
                />
              </span>
              <span className="plate-input-tun">TUN</span>
              <span className="plate-input-segment">
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="****"
                  maxLength={4}
                  value={plate.right}
                  onChange={(event) => handlePlateChange('right', event.target.value)}
                  required
                />
              </span>
            </div>
            <div className="select-with-icon">
              {mapVehicleListById[form.vehicleListId]?.imageUrl ? (
                <img
                  src={mapVehicleListById[form.vehicleListId].imageUrl}
                  alt=""
                  className="vehicle-type-icon"
                  onError={(event) => {
                    event.currentTarget.style.display = 'none';
                  }}
                />
              ) : null}
              <select className="input-glass" value={form.vehicleListId} onChange={(event) => setForm({ ...form, vehicleListId: event.target.value })} required>
                <option value="">Sélectionner un type de véhicule</option>
                {vehicleLists.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name ?? item.id}
                  </option>
                ))}
              </select>
            </div>
            <select className="input-glass" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
              <option value="available">Disponible</option>
              <option value="in_use">En utilisation</option>
              <option value="maintenance">Maintenance</option>
              <option value="out_of_service">Inactif</option>
            </select>
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