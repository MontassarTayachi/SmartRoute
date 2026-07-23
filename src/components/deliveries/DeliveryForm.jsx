import { useMemo, useState } from 'react';
import DeliveryMap from './DeliveryMap';
import LocationPicker from './LocationPicker';

const emptyForm = {
	customer: '',
	pickupAddress: '',
	dropoffAddress: '',
	weightKg: '',
	priority: 'medium',
	scheduledAt: '',
	pickupLatitude: null,
	pickupLongitude: null,
	dropoffLatitude: null,
	dropoffLongitude: null,
};

const DeliveryForm = ({ initialValues = emptyForm, onSubmit, loading = false, submitLabel = 'Créer la livraison' }) => {
	const [form, setForm] = useState(initialValues);
	const [error, setError] = useState('');

	const isValid = useMemo(
		() =>
			form.customer && form.pickupAddress && form.dropoffAddress && form.weightKg > 0 && form.priority && form.scheduledAt &&
			form.pickupLatitude !== null && form.pickupLongitude !== null && form.dropoffLatitude !== null && form.dropoffLongitude !== null,
		[form],
	);

	const handleLocationPick = ({ type, latitude, longitude }) => {
		setForm((current) => ({
			...current,
			[type === 'pickup' ? 'pickupLatitude' : 'dropoffLatitude']: latitude,
			[type === 'pickup' ? 'pickupLongitude' : 'dropoffLongitude']: longitude,
		}));
	};

	const handleSubmit = async (event) => {
		event.preventDefault();
		if (!isValid) {
			setError('Tous les champs sont obligatoires.');
			return;
		}
		setError('');
		await onSubmit?.(form);
	};

	return (
		<form className="resource-form delivery-form" onSubmit={handleSubmit}>
			{error ? <div className="form-error">{error}</div> : null}
			<div className="form-grid-2">
				<label className="field-label">
					Client
					<input value={form.customer} onChange={(event) => setForm({ ...form, customer: event.target.value })} />
				</label>
				<label className="field-label">
					Poids (kg)
					<input type="number" min="0.1" step="0.1" value={form.weightKg} onChange={(event) => setForm({ ...form, weightKg: event.target.value })} />
				</label>
			</div>

			<div className="form-grid-2">
				<label className="field-label">
					Adresse pickup
					<input value={form.pickupAddress} onChange={(event) => setForm({ ...form, pickupAddress: event.target.value })} />
				</label>
				<label className="field-label">
					Adresse dropoff
					<input value={form.dropoffAddress} onChange={(event) => setForm({ ...form, dropoffAddress: event.target.value })} />
				</label>
			</div>

			<div className="form-grid-2">
				<label className="field-label">
					Priorité
					<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>
						<option value="low">Low</option>
						<option value="medium">Medium</option>
						<option value="high">High</option>
						<option value="urgent">Urgent</option>
					</select>
				</label>
				<label className="field-label">
					Date planifiée
					<input type="datetime-local" value={form.scheduledAt} onChange={(event) => setForm({ ...form, scheduledAt: event.target.value })} />
				</label>
			</div>

			<div className="delivery-pickers">
				<LocationPicker title="Pickup" value={form.pickupLatitude !== null ? `${form.pickupLatitude}, ${form.pickupLongitude}` : ''} color="blue" />
				<LocationPicker title="Dropoff" value={form.dropoffLatitude !== null ? `${form.dropoffLatitude}, ${form.dropoffLongitude}` : ''} color="red" />
			</div>

			<DeliveryMap
				mode="create"
				pickup={{ latitude: form.pickupLatitude, longitude: form.pickupLongitude }}
				dropoff={{ latitude: form.dropoffLatitude, longitude: form.dropoffLongitude }}
				onPickLocation={handleLocationPick}
			/>

			<div className="modal-actions">
				<button type="submit" className="btn-primary" disabled={loading || !isValid}>
					{loading ? 'Enregistrement...' : submitLabel}
				</button>
			</div>
		</form>
	);
};

export default DeliveryForm;
