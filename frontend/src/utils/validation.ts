interface MovementInput {
  fecha: string
  descripcion: string
  valor: string
}

export function validateMovementInput(input: MovementInput): string | null {
  if (!input.fecha) {
    return 'La fecha es obligatoria.'
  }

  const descripcion = input.descripcion.trim()
  if (!descripcion) {
    return 'La descripción es obligatoria.'
  }

  if (descripcion.length > 200) {
    return 'La descripción no puede superar los 200 caracteres.'
  }

  if (!input.valor.trim()) {
    return 'El valor es obligatorio.'
  }

  const amount = Number(input.valor)
  if (!Number.isFinite(amount) || amount <= 0) {
    return 'El valor debe ser mayor que 0.'
  }

  const decimals = input.valor.split('.')[1]?.length ?? 0
  if (decimals > 2) {
    return 'El valor admite como máximo 2 decimales.'
  }

  if (input.valor.replace('.', '').length > 12) {
    return 'El valor admite como máximo 12 dígitos.'
  }

  return null
}
