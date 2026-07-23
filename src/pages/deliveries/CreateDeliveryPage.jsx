import { useNavigate } from 'react-router-dom';
import DeliveryForm from '../../components/deliveries/DeliveryForm';
import { useToast } from '../../context/ToastContext';
import { createDelivery } from '../../services/deliveryService';
import { getApiErrorMessage } from '../../utils/apiError';

const CreateDeliveryPage = () => {
	const navigate = useNavigate();
	const toast = useToast();

	const handleSubmit = async (payload) => {
		try {
			const delivery = await createDelivery(payload);
			toast.success('Livraison créée');
			navigate(`/manager/deliveries/${delivery.id}`);
		} catch (error) {
			toast.error(getApiErrorMessage(error, 'Création impossible'));
		}
	};

	return (
		<section className="resource-page">
			<div className="resource-header">
				<div>
					<h1>Nouvelle livraison</h1>
					<p>Créez une livraison et positionnez les points sur la carte.</p>
				</div>
				<div className="resource-actions">
					<button type="button" className="btn-secondary" onClick={() => navigate('/manager/deliveries')}>Retour</button>
					</div>
			</div>
			<DeliveryForm onSubmit={handleSubmit} submitLabel="Créer et ouvrir le détail" />
		</section>
	);
};

export default CreateDeliveryPage;
