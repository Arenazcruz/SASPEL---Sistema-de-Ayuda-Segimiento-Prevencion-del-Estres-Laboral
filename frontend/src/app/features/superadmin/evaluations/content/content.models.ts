export type ContentKind = 'questions' | 'scales' | 'options' | 'ranges';
export type ContentMode = 'create' | 'edit' | 'detail';
export interface ContentScope {
  kind: ContentKind;
  parentId?: string;
}
export interface ContentRow {
  id: string;
  activo: boolean;
  creado_en: string;
  actualizado_en: string;
  instrumento_id?: string;
  escala_id?: string | null;
  texto?: string;
  nombre?: string;
  descripcion?: string;
  etiqueta?: string;
  valor?: number;
  orden?: number;
  tipo_respuesta?: string;
  obligatoria?: boolean;
  invertida?: boolean;
  puntaje_minimo?: number;
  puntaje_maximo?: number;
  interpretacion?: string;
}
export interface ContentPage<T = ContentRow> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
}
export type ContentValue = string | number | boolean | null;
export interface ContentField {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'checkbox' | 'type' | 'scale';
  required?: boolean;
  maxLength?: number;
  min?: number;
  max?: number;
  initial: ContentValue;
}
const order: ContentField = {
  name: 'orden',
  label: 'Orden',
  type: 'number',
  required: true,
  min: 1,
  max: 32767,
  initial: 1,
};
const name: ContentField = {
  name: 'nombre',
  label: 'Nombre',
  type: 'text',
  required: true,
  maxLength: 150,
  initial: '',
};
export const CONTENT_CONFIG: Record<
  ContentKind,
  { title: string; singular: string; description: string; fields: ContentField[] }
> = {
  questions: {
    title: 'Preguntas',
    singular: 'pregunta',
    description: 'Contenido y orden de las preguntas de cada instrumento.',
    fields: [
      { name: 'texto', label: 'Pregunta', type: 'textarea', required: true, initial: '' },
      order,
      {
        name: 'tipo_respuesta',
        label: 'Tipo de respuesta',
        type: 'type',
        required: true,
        initial: 'TEXTO',
      },
      { name: 'escala_id', label: 'Escala de respuesta', type: 'scale', initial: null },
      { name: 'obligatoria', label: 'Respuesta obligatoria', type: 'checkbox', initial: true },
      { name: 'invertida', label: 'Pregunta invertida', type: 'checkbox', initial: false },
    ],
  },
  scales: {
    title: 'Escalas de respuesta',
    singular: 'escala',
    description: 'Catálogo de escalas y sus opciones de respuesta.',
    fields: [name, { name: 'descripcion', label: 'Descripción', type: 'textarea', initial: '' }],
  },
  options: {
    title: 'Opciones de respuesta',
    singular: 'opción',
    description: 'Opciones que pertenecen a la escala seleccionada.',
    fields: [
      {
        name: 'etiqueta',
        label: 'Etiqueta',
        type: 'text',
        required: true,
        maxLength: 150,
        initial: '',
      },
      {
        name: 'valor',
        label: 'Valor',
        type: 'number',
        required: true,
        min: -32768,
        max: 32767,
        initial: 0,
      },
      order,
    ],
  },
  ranges: {
    title: 'Rangos de interpretación',
    singular: 'rango',
    description: 'Intervalos y descripciones de cada instrumento.',
    fields: [
      name,
      {
        name: 'puntaje_minimo',
        label: 'Puntaje mínimo',
        type: 'number',
        required: true,
        min: -2147483648,
        max: 2147483647,
        initial: 0,
      },
      {
        name: 'puntaje_maximo',
        label: 'Puntaje máximo',
        type: 'number',
        required: true,
        min: -2147483648,
        max: 2147483647,
        initial: 0,
      },
      order,
      { name: 'interpretacion', label: 'Interpretación', type: 'textarea', initial: '' },
    ],
  },
};
