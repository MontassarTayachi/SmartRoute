import { useEffect, useMemo, useState } from 'react';
import Modal from '../Modal';

const AssignDeliveryModal = ({ open, delivery, vehicles = [], drivers = [], onClose, onSubmit, loading }) => {
	const [vehicleId, setVehicleId] = useState('');
	const [driverId, setDriverId] = useState('');

	useEffect(() => {
		setVehicleId(delivery?.vehicleId ?? '');
		setDriverId(delivery?.driverId ?? '');
	}, [delivery]);

	const canSubmit = useMemo(() => vehicleId && driverId, [vehicleId, driverId]);

	if (!open) {
		return null;
	}

	return (
		<Modal title="Affecter une livraison" onClose={onClose}>
			<div className="resource-form">
				<label className="field-label">
					Véhicule
					<select value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
						<option value="">Sélectionner</option>
						{vehicles.map((vehicle) => (
							<option key={vehicle.id} value={vehicle.id}>
								{vehicle.registration ?? vehicle.id}
							</option>
						))}
					</select>
				</label>
				<label className="field-label">
					Conducteur
					<select value={driverId} onChange={(event) => setDriverId(event.target.value)}>
						<option value="">Sélectionner</option>
						{drivers.map((driver) => (
							<option key={driver.id} value={driver.id}>
								{driver.fullName ?? driver.id}
							</option>
						))}
					</select>
				</label>
				<div className="modal-actions">
					<button type="button" className="btn-secondary" onClick={onClose}>
						Annuler
					</button>
					<button
						type="button"
						className="btn-primary"
						disabled={!canSubmit || loading}
						onClick={() => onSubmit?.({ vehicleId, driverId })}
					>
						{loading ? 'Affectation...' : 'Affecter'}
					</button>
				</div>
			</div>
		</Modal>
	);
};

export default AssignDeliveryModal;
