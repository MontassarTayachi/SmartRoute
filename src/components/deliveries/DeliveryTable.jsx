import { useEffect, useRef, useState } from 'react';
import DeliveryStatusBadge from './DeliveryStatusBadge';

const ActionsMenu = ({ delivery, onView, onEdit, onAssign, onStatus }) => {
	const [open, setOpen] = useState(false);
	const menuRef = useRef(null);

	useEffect(() => {
		if (!open) return;
		const handleClickOutside = (event) => {
			if (menuRef.current && !menuRef.current.contains(event.target)) {
				setOpen(false);
			}
		};
		document.addEventListener('mousedown', handleClickOutside);
		return () => document.removeEventListener('mousedown', handleClickOutside);
	}, [open]);

	const handleSelect = (action) => {
		setOpen(false);
		action?.(delivery);
	};

	return (
		<div className="table-actions-menu" ref={menuRef}>
			<button
				type="button"
				className="icon-button icon-button-menu"
				onClick={() => setOpen((prev) => !prev)}
				aria-haspopup="true"
				aria-expanded={open}
			>
				Actions ▾
			</button>
			{open && (
				<div className="table-actions-dropdown" role="menu">
					<button type="button" role="menuitem" onClick={() => handleSelect(onView)}>Voir</button>
					<button type="button" role="menuitem" onClick={() => handleSelect(onEdit)}>Modifier</button>
					<button type="button" role="menuitem" onClick={() => handleSelect(onAssign)}>Assigner</button>
					<button type="button" role="menuitem" onClick={() => handleSelect(onStatus)}>Statut</button>
				</div>
			)}
		</div>
	);
};

const DeliveryTable = ({ deliveries = [], loading = false, onView, onEdit, onAssign, onStatus }) => (
	<div className="resource-table-wrapper">
		<table className="resource-table deliveries-table">
			<thead>
				<tr>
					<th>Reference</th>
					<th>Customer</th>
					<th>Pickup</th>
					<th>Dropoff</th>
					<th>Weight</th>
					<th>Priority</th>
					<th>Status</th>
					<th>Vehicle</th>
					<th>Driver</th>
					<th>Date</th>
					<th>Actions</th>
				</tr>
			</thead>
			<tbody>
				{loading ? (
					<tr><td colSpan="11" className="loading-row">Chargement…</td></tr>
				) : deliveries.length === 0 ? (
					<tr><td colSpan="11" className="loading-row">Aucune livraison trouvée</td></tr>
				) : deliveries.map((delivery) => (
					<tr key={delivery.id}>
						<td>{delivery.reference || '-'}</td>
						<td>{delivery.customer || '-'}</td>
						<td>{delivery.pickupAddress || '-'}</td>
						<td>{delivery.dropoffAddress || '-'}</td>
						<td>{delivery.weightKg ? `${delivery.weightKg} kg` : '-'}</td>
						<td>{delivery.priority || '-'}</td>
						<td><DeliveryStatusBadge status={delivery.status} /></td>
						<td>{delivery.vehicle?.registration || delivery.vehicleId || '-'}</td>
						<td>{delivery.driver?.fullName || delivery.driverId || '-'}</td>
						<td>{delivery.scheduledAt ? new Date(delivery.scheduledAt).toLocaleString() : '-'}</td>
						<td>
							<ActionsMenu
								delivery={delivery}
								onView={onView}
								onEdit={onEdit}
								onAssign={onAssign}
								onStatus={onStatus}
							/>
						</td>
					</tr>
				))}
			</tbody>
		</table>
	</div>
);

export default DeliveryTable;