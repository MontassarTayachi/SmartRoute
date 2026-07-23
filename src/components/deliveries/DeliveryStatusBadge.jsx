const STATUS_META = {
	pending: { label: 'Pending', className: 'badge-warning' },
	assigned: { label: 'Assigned', className: 'badge-info' },
	in_progress: { label: 'In progress', className: 'badge-info' },
	delivered: { label: 'Delivered', className: 'badge-success' },
	cancelled: { label: 'Cancelled', className: 'badge-danger' },
};

const normalizeStatus = (status) => String(status ?? 'pending').toLowerCase();

const DeliveryStatusBadge = ({ status, onChange, editable = false }) => {
	const value = normalizeStatus(status);
	const meta = STATUS_META[value] ?? STATUS_META.pending;

	if (!editable) {
		return <span className={`badge ${meta.className}`}>{meta.label}</span>;
	}

	return (
		<select
			className={`badge ${meta.className}`}
			value={value}
			onChange={(event) => onChange?.(event.target.value)}
			aria-label="Modifier le statut"
		>
			{Object.entries(STATUS_META).map(([key, option]) => (
				<option key={key} value={key}>
					{option.label}
				</option>
			))}
		</select>
	);
};

export default DeliveryStatusBadge;
