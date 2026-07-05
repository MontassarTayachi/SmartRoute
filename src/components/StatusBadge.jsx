const statusToClass = (status) => {
  const value = String(status ?? '').toUpperCase();

  if (['ACTIVE', 'AVAILABLE', 'LIVRE', 'LIVREE', 'DELIVERED', 'TRUE'].includes(value)) {
    return 'badge-success';
  }

  if (['IN_TRANSIT', 'EN_TRANSIT', 'IN_PROGRESS', 'EN_COURS', 'MAINTENANCE'].includes(value)) {
    return 'badge-info';
  }

  if (['PENDING', 'EN_ATTENTE', 'INFO', 'WAITING'].includes(value)) {
    return 'badge-warning';
  }

  if (['OUT_OF_SERVICE', 'ERROR', 'FAILED', 'CANCELLED', 'ANNULE', 'FALSE'].includes(value)) {
    return 'badge-danger';
  }

  return 'badge-info';
};

const StatusBadge = ({ status, label }) => (
  <span className={`badge ${statusToClass(status)}`}>{label ?? status ?? 'N/A'}</span>
);

export default StatusBadge;
