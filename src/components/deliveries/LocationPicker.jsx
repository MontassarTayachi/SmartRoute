const LocationPicker = ({ title, value, onChange, placeholder = 'Choisir sur la carte', color = 'blue' }) => (
	<div className="location-picker-card">
		<div className="location-picker-dot" data-color={color} />
		<div className="location-picker-content">
			<strong>{title}</strong>
			<span>{value || placeholder}</span>
		</div>
		{onChange ? (
			<button type="button" className="btn-ghost" onClick={onChange}>
				Utiliser la carte
			</button>
		) : null}
	</div>
);

export default LocationPicker;
