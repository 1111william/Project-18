export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status }
}

export async function accountApi(path, { method = 'GET', body } = {}) {
  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      signal: AbortSignal.timeout(20000),
    })
  } catch {
    throw new ApiError('Cannot reach the server. Check your connection and try again.', 0)
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    throw new ApiError(Array.isArray(detail) ? detail.map(item => item.msg).join(' ') : detail || 'The server could not complete your request. Please try again.', response.status)
  }
  return data
}
