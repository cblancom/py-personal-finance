import type { ExpenseType } from './expense'

export type ImportFileType = 'CSV' | 'XLSX'
export type ImportMovementType = 'INGRESO' | 'GASTO'
export type ImportRowStatus = 'PENDIENTE' | 'IMPORTADO' | 'DESCARTADO'

export interface ImportRowError {
  campo: string
  mensaje: string
}

export interface ImportBatch {
  id: number
  nombre_archivo: string
  tipo_archivo: ImportFileType
  tipo_movimiento: ImportMovementType
  tamano_bytes: number
  total_filas: number
  filas_importadas: number
  filas_pendientes: number
  filas_descartadas: number
  created_at: string
}

export interface ImportPendingRow {
  id: number
  lote_id: number
  numero_fila: number
  tipo_movimiento: ImportMovementType
  fecha: string | null
  descripcion: string | null
  valor: string | null
  categoria: string | null
  tipo_gasto: ExpenseType | null
  estado: ImportRowStatus
  errores: ImportRowError[]
  posible_duplicado: boolean
  duplicado_de_id: number | null
}

export interface ImportPendingCount {
  pendientes: number
}

export interface ImportPendingUpdate {
  fecha?: string | null
  descripcion?: string | null
  valor?: string | null
  categoria?: string | null
  tipo_gasto?: ExpenseType | null
}
