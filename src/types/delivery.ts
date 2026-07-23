export type DeliveryPriority = 'low' | 'medium' | 'high' | 'urgent';

export type DeliveryStatus = 'pending' | 'assigned' | 'in_progress' | 'delivered' | 'cancelled';

export interface DeliveryCoordinates {
	latitude: number | null;
	longitude: number | null;
}

export interface DeliveryVehicle {
	id: string;
	registration?: string | null;
}

export interface DeliveryDriver {
	id: string;
	fullName?: string | null;
}

export interface Delivery {
	id: string;
	reference: string;
	customer: string;
	pickupAddress: string;
	dropoffAddress: string;
	weightKg: number | string;
	priority: DeliveryPriority;
	status: DeliveryStatus;
	vehicleId?: string | null;
	driverId?: string | null;
	vehicle?: DeliveryVehicle | null;
	driver?: DeliveryDriver | null;
	scheduledAt: string;
	pickupLatitude: number | null;
	pickupLongitude: number | null;
	dropoffLatitude: number | null;
	dropoffLongitude: number | null;
	createdAt?: string;
	updatedAt?: string;
}

export interface DeliveryPayload {
	customer: string;
	pickupAddress: string;
	dropoffAddress: string;
	pickupLatitude: number | null;
	pickupLongitude: number | null;
	dropoffLatitude: number | null;
	dropoffLongitude: number | null;
	weightKg: number | string;
	priority: DeliveryPriority;
	scheduledAt: string;
}

export interface DeliveryAssignmentPayload {
	vehicleId: string;
	driverId: string;
}
