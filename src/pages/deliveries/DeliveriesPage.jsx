import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AssignDeliveryModal from '../../components/deliveries/AssignDeliveryModal';
import DeliveryStatusBadge from '../../components/deliveries/DeliveryStatusBadge';
import DeliveryTable from '../../components/deliveries/DeliveryTable';
import Modal from '../../components/Modal';
import { useToast } from '../../context/ToastContext';
import { getDrivers } from '../../services/driverService';
import { assignDelivery, getDeliveries, updateDelivery, updateDeliveryStatus } from '../../services/deliveryService';
import { getAvailableVehicles } from '../../services/vehicleService';
import { getApiErrorMessage } from '../../utils/apiError';

const DeliveriesPage = () => {
	const navigate = useNavigate();
	const toast = useToast();
	const [deliveries, setDeliveries] = useState([]);
	const [vehicles, setVehicles] = useState([]);
	const [drivers, setDrivers] = useState([]);
	const [loading, setLoading] = useState(false);
	const [assignOpen, setAssignOpen] = useState(false);
	const [statusOpen, setStatusOpen] = useState(false);
	const [editOpen, setEditOpen] = useState(false);
	const [activeDelivery, setActiveDelivery] = useState(null);
	const [search, setSearch] = useState('');
	const [page, setPage] = useState(1);
	const [editForm, setEditForm] = useState({ weightKg: '', priority: 'medium' });

	const loadData = async () => {
		setLoading(true);
		try {
			const [deliveryData, vehicleData, driverData] = await Promise.all([
				getDeliveries({ page, size: 20 }),
				getAvailableVehicles({ page: 1, status: 'available' }),
				getDrivers({ page: 1 }),
			]);
			setDeliveries(Array.isArray(deliveryData) ? deliveryData : deliveryData?.items ?? []);
			setVehicles(Array.isArray(vehicleData) ? vehicleData : vehicleData?.items ?? []);
			setDrivers(Array.isArray(driverData) ? driverData : driverData?.items ?? []);
		} catch (error) {
			toast.error(getApiErrorMessage(error, 'Impossible de charger les livraisons'));
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [page]);

	const filteredDeliveries = useMemo(() => {
		const term = search.trim().toLowerCase();
		if (!term) return deliveries;
		return deliveries.filter((delivery) => [delivery.reference, delivery.customer, delivery.pickupAddress, delivery.dropoffAddress, delivery.status]
			.filter(Boolean)
			.some((value) => String(value).toLowerCase().includes(term)));
	}, [deliveries, search]);

	const openAssign = (delivery) => {
		setActiveDelivery(delivery);
		setAssignOpen(true);
	};

	const openStatus = (delivery) => {
		setActiveDelivery(delivery);
		setStatusOpen(true);
	};

	const openEdit = (delivery) => {
		setActiveDelivery(delivery);
		setEditForm({ weightKg: delivery.weightKg ?? '', priority: delivery.priority ?? 'medium' });
		setEditOpen(true);
	};

	const handleAssign = async (payload) => {
		try {
			await assignDelivery(activeDelivery.id, payload);
			toast.success('Livraison assignée');
			setAssignOpen(false);
			await loadData();
		} catch (error) {
			toast.error(getApiErrorMessage(error, 'Affectation impossible'));
		}
	};

	const handleStatusChange = async (status) => {
		try {
			await updateDeliveryStatus(activeDelivery.id, status);
			toast.success('Statut mis à jour');
			setStatusOpen(false);
			await loadData();
		} catch (error) {
			toast.error(getApiErrorMessage(error, 'Mise à jour du statut impossible'));
		}
	};

	const handleEditSubmit = async (event) => {
		event.preventDefault();
		try {
			await updateDelivery(activeDelivery.id, {
				customer: activeDelivery.customer,
				pickupAddress: activeDelivery.pickupAddress,
				dropoffAddress: activeDelivery.dropoffAddress,
				pickupLatitude: activeDelivery.pickupLatitude,
				pickupLongitude: activeDelivery.pickupLongitude,
				dropoffLatitude: activeDelivery.dropoffLatitude,
				dropoffLongitude: activeDelivery.dropoffLongitude,
				weightKg: editForm.weightKg,
				priority: editForm.priority,
				scheduledAt: activeDelivery.scheduledAt,
			});
			toast.success('Livraison mise à jour');
			setEditOpen(false);
			await loadData();
		} catch (error) {
			toast.error(getApiErrorMessage(error, 'Modification impossible'));
		}
	};

	return (
		<section className="resource-page deliveries-page">
			<div className="resource-header">
				<div>
					<h1>Livraisons</h1>
					<p>Gestion des livraisons, affectations et statuts.</p>
				</div>
				<div className="resource-actions">
					
					<button type="button" className="btn-primary" onClick={() => navigate('/manager/deliveries/new')}>Nouvelle livraison</button>
				</div>
			</div>
		<input className="input-glass" placeholder="Rechercher..." value={search} onChange={(event) => setSearch(event.target.value)} />
			<DeliveryTable
				deliveries={filteredDeliveries}
				loading={loading}
				onView={(delivery) => navigate(`/manager/deliveries/${delivery.id}`)}
				onEdit={openEdit}
				onAssign={openAssign}
				onStatus={openStatus}
			/>

			<div className="pagination-bar">
				<button type="button" className="btn-secondary" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>Précédent</button>
				<span>Page {page}</span>
				<button type="button" className="btn-secondary" onClick={() => setPage((current) => current + 1)}>Suivant</button>
			</div>

			<AssignDeliveryModal open={assignOpen} delivery={activeDelivery} vehicles={vehicles} drivers={drivers} onClose={() => setAssignOpen(false)} onSubmit={handleAssign} />

			{statusOpen && activeDelivery ? (
				<Modal title="Changer le statut" onClose={() => setStatusOpen(false)}>
					<div className="resource-form">
						<DeliveryStatusBadge status={activeDelivery.status} editable onChange={handleStatusChange} />
					</div>
				</Modal>
			) : null}

			{editOpen && activeDelivery ? (
				<Modal title="Modifier la livraison" onClose={() => setEditOpen(false)}>
					<form className="resource-form" onSubmit={handleEditSubmit}>
						<label className="field-label">
							Poids (kg)
							<input type="number" min="0.1" step="0.1" value={editForm.weightKg} onChange={(event) => setEditForm({ ...editForm, weightKg: event.target.value })} />
						</label>
						<label className="field-label">
							Priorité
							<select value={editForm.priority} onChange={(event) => setEditForm({ ...editForm, priority: event.target.value })}>
								<option value="low">Low</option>
								<option value="medium">Medium</option>
								<option value="high">High</option>
								<option value="urgent">Urgent</option>
							</select>
						</label>
						<div className="modal-actions">
							<button type="button" className="btn-secondary" onClick={() => setEditOpen(false)}>Annuler</button>
							<button type="submit" className="btn-primary">Enregistrer</button>
						</div>
					</form>
				</Modal>
			) : null}
		</section>
	);
};

export default DeliveriesPage;
