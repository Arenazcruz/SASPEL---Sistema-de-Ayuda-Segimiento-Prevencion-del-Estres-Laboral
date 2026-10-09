export interface InstrumentData {
  codigo: string;
  nombre: string;
  version: string;
  descripcion: string;
  instrucciones: string;
  es_inicial: boolean;
}

export interface Instrument extends InstrumentData {
  id: number;
  activo: boolean;
  creado_en: string;
  actualizado_en: string;
}

export interface InstrumentPage {
  count: number;
  page: number;
  page_size: number;
  results: Instrument[];
}

export type InstrumentMode = 'create' | 'edit' | 'detail';
