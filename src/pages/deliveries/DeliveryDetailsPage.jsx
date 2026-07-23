import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import DeliveryMap from '../../components/deliveries/DeliveryMap';
import DeliveryStatusBadge from '../../components/deliveries/DeliveryStatusBadge';
import { useToast } from '../../context/ToastContext';
import { getDeliveryById } from '../../services/deliveryService';
import { getApiErrorMessage } from '../../utils/apiError';

const DeliveryDetailsPage = () => {
	const { id } = useParams();
	const toast = useToast();
	const [delivery, setDelivery] = useState(null);
	const [loading, setLoading] = useState(false);
	const navigate = useNavigate();
	useEffect(() => {
		const loadDelivery = async () => {
			setLoading(true);
			try {
				setDelivery(await getDeliveryById(id));
			} catch (error) {
				toast.error(getApiErrorMessage(error, 'Impossible de charger la livraison'));
			} finally {
				setLoading(false);
			}
		};

		loadDelivery();
	}, [id, toast]);

	if (loading) {
		return <section className="resource-page"><p className="loading-row">Chargement…</p></section>;
	}

	if (!delivery) {
		return <section className="resource-page"><p className="loading-row">Livraison introuvable</p></section>;
	}

	return (
		<section className="resource-page deliveries-details-page">
			<div className="resource-header">
				<div>
					<h1>{delivery.reference || 'Détail livraison'} <DeliveryStatusBadge status={delivery.status} /></h1>
					<p>{delivery.customer || 'Client non renseigné'} </p>
				</div>
				<button type="button" className="btn-secondary" onClick={() => navigate('/manager/deliveries')}>Retour</button>
			</div>

			<div className="info-grid">
				<div className="info-card"><strong>Client</strong><span>{delivery.customer || '-'}</span></div>
				<div className="info-card"><strong>Poids</strong><span>{delivery.weightKg ? `${delivery.weightKg} kg` : '-'}</span></div>
				<div className="info-card"><strong>Priorité</strong><span>{delivery.priority || '-'}</span></div>
				<div className="info-card"><strong>Conducteur</strong><span>{delivery.driver?.fullName || delivery.driverId || '-'}</span></div>
				<div className="info-card"><strong>Véhicule</strong><span>{delivery.vehicle?.registration || delivery.vehicleId || '-'}</span></div>
				<div className="info-card"><strong>Planifiée</strong><span>{delivery.scheduledAt ? new Date(delivery.scheduledAt).toLocaleString() : '-'}</span></div>
			</div>

			<div className="delivery-map-panel">
				<DeliveryMap
					mode="view"
					pickup={{ latitude: delivery.pickupLatitude, longitude: delivery.pickupLongitude }}
					dropoff={{ latitude: delivery.dropoffLatitude, longitude: delivery.dropoffLongitude }}
				/>
			</div>
		</section>
	);
};

export default DeliveryDetailsPage;
