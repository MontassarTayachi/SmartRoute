import { useEffect, useState } from 'react';
import { getCurrentDriver } from '../services/driverService';
import StatusBadge from '../components/StatusBadge';

const DriverProfilePage = () => {
  const [driverData, setDriverData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDriverData = async () => {
      try {
        setLoading(true);
        const data = await getCurrentDriver();
        setDriverData(data);
      } catch (err) {
        setError('Impossible de charger les informations du conducteur');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadDriverData();
  }, []);

  if (loading) {
    return (
      <div className="resource-page">
        <div className="resource-header">
          <h1>Profil conducteur</h1>
        </div>
        <p className="loading-row">Chargement…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="resource-page">
        <div className="resource-header">
          <h1>Profil conducteur</h1>
        </div>
        <div className="form-error">{error}</div>
      </div>
    );
  }

  const { driver, vehicle } = driverData || {};
  const isAvailable = driver?.availability === 'available';

  return (
    <section className="resource-page">
      <div className="resource-header">
        <h1>Profil conducteur</h1>
        <p>Informations personnelles et véhicule assigné</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Informations du conducteur */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-16 w-16 rounded-full bg-brand-muted border border-brand flex items-center justify-center font-display font-semibold text-2xl text-brand">
              {driver?.full_name?.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase() || '??'}
            </div>
            <div>
              <h2 className="text-xl font-display font-semibold">{driver?.full_name}</h2>
              <p className="text-secondary">{driver?.phone}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-border">
              <span className="text-secondary">Numéro de permis</span>
              <span className="font-mono">{driver?.license_number}</span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-border">
              <span className="text-secondary">Disponibilité</span>
              <StatusBadge
                status={isAvailable ? 'ACTIVE' : 'INACTIVE'}
                label={isAvailable ? 'Disponible' : 'Indisponible'}
              />
            </div>
            <div className="flex justify-between items-center py-3 border-b border-border">
              <span className="text-secondary">ID Conducteur</span>
              <span className="font-mono text-sm">{driver?._id?.slice(-8)}</span>
            </div>
          </div>
        </div>

        {/* Informations du véhicule */}
        {vehicle ? (
          <div className="glass-card p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-16 w-16 rounded-lg overflow-hidden bg-surface-muted">
                <img
                  src={`${import.meta.env.VITE_IMAGE_BASE_URL}${vehicle.image_url}`}
                  alt={vehicle.nom}
                  className="h-full w-full object-cover"
                />
              </div>
              <div>
                <h2 className="text-xl font-display font-semibold">{vehicle.nom}</h2>
                <p className="text-secondary">{vehicle.registration}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-secondary">Capacité</span>
                <span className="font-mono">{vehicle.capacity_kg} kg</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-secondary">Statut</span>
                <StatusBadge
                  status={vehicle.status === 'available' ? 'ACTIVE' : 'INACTIVE'}
                  label={vehicle.status === 'available' ? 'Disponible' : 'Indisponible'}
                />
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-secondary">Consommation moyenne</span>
                <span className="font-mono">{vehicle.avg_fuel_consumption} L/100km</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-secondary">ID Véhicule</span>
                <span className="font-mono text-sm">{vehicle._id?.slice(-8)}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-card p-6 flex items-center justify-center">
            <p className="text-secondary">Aucun véhicule assigné</p>
          </div>
        )}
      </div>
    </section>
  );
};

export default DriverProfilePage;
