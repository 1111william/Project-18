export class ApiError extends Error {
  constructor(message, status, fields = []) {
    super(message)
    this.status = status
    this.fields = fields
  }
}

export async function accountApi(path, { method = 'GET', body } = {}) {
  let response
  try {
    const isBinaryBody = typeof Blob !== 'undefined' && body instanceof Blob
    response = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: { 'Content-Type': isBinaryBody ? body.type : 'application/json' },
      ...(body !== undefined ? { body: isBinaryBody ? body : JSON.stringify(body) } : {}),
      signal: AbortSignal.timeout(20000),
    })
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0)
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.error ?? data?.detail
    const message = Array.isArray(detail)
      ? detail.map(item => item.msg).join(' ')
      : detail || 'The server could not complete your request. Please try again.'
    throw new ApiError(message, response.status, data?.fields ?? [])
  }
  return data?.success === true ? data.data : data
}
