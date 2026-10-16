export interface TrabajadorAsignado {
  id: string;
  nombre_completo: string;
  email: string;
  area: string;
  cargo: string;
  fecha_asignacion: string;
  estado: 'ACTIVA';
}

export interface MisTrabajadores {
  cantidad: number;
  trabajadores: TrabajadorAsignado[];
}
