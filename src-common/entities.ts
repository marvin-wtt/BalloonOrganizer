export type PersonRole = 'participant' | 'counselor';
export type VehicleKind = 'car' | 'balloon';

export interface Identifiable {
  id: string;
}

export interface Person extends Identifiable {
  role: PersonRole;
  name: string;
  nationality: string;
  weight?: number;
  firstTime?: boolean;
}

export interface VehicleBase extends Identifiable {
  type: VehicleKind;
  name: string;
  allowedOperatorIds: string[];
  maxCapacity: number;
}

export interface Car extends VehicleBase {
  type: 'car';
  hasTrailerClutch: boolean;
}

export interface Balloon extends VehicleBase {
  type: 'balloon';
  maxWeight?: number;
}

export type Vehicle = Car | Balloon;

export interface VehicleAssignment {
  id: string;
  operatorId: string | null;
  passengerIds: string[];
}

export interface VehicleGroup {
  balloon: VehicleAssignment;
  cars: VehicleAssignment[];
}

export interface Flight extends Identifiable {
  date?: string;
  vehicleGroups: VehicleGroup[];
  personIds: string[];
  balloonIds: string[];
  carIds: string[];
}

export interface ProjectSettings {
  showVehicleIndex?: boolean;
  showVehicleLabel?: boolean;
  showGroupLabel?: boolean;
  showNumberOfFlights?: boolean;
  showPersonWeight?: boolean;
  showVehicleWeight?: boolean;
  personDefaultWeight?: number;
  groupAlignment?: 'horizontal' | 'vertical';
  groupStyle?: 'dashed' | 'highlighted';
}

export interface Project extends Identifiable {
  name: string;
  description?: string;
  createdAt: string;

  people: Person[];
  cars: Car[];
  balloons: Balloon[];
  flights: Flight[];
  settings?: ProjectSettings;
}

export interface ProjectMeta {
  id: string;
  name: string;
  createdAt: string;
  description?: string;
  filePath: string;
}

export interface SmartFillPayload {
  people: (Person & { flights: number })[];
  cars: Car[];
  balloons: Balloon[];
  groups: VehicleGroup[];
  history: Flight[];
}

export interface SmartFillOptions {
  wPilotFairness?: number;
  wPassengerFairness?: number;
  wNationalityDiversity?: number;
  wVehicleRotation?: number;
  wSecondLegFairness?: number;
  timeLimit?: number;
  leg?: 'first' | 'second' | undefined;
}
