import { useAuth } from '@clerk/clerk-react'
import { useCallback } from 'react'
import { API_BASE_URL, API_VERSION } from '@/config/config'

export type ApiClient = {
  get: <T>(path: string) => Promise<T>
  post: <T>(path: string, body: unknown) => Promise<T>
  put: <T>(path: string, body: unknown) => Promise<T>
  del: (path: string) => Promise<void>
}

export function useApiClient(): ApiClient {
  const { getToken } = useAuth()

  const request = useCallback(
    async <T>(method: string, path: string, body?: unknown): Promise<T> => {
      const token = await getToken()
      const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`
      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
      })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(`${method} ${path} failed: ${res.status} ${text}`)
      }
      if (res.status === 204) return undefined as T
      return (await res.json()) as T
    },
    [getToken]
  )

  return {
    get: (path) => request('GET', path),
    post: (path, body) => request('POST', path, body),
    put: (path, body) => request('PUT', path, body),
    del: async (path) => {
      await request<void>('DELETE', path)
    },
  }
}

/** Convenience: prefixed paths into the v1 API. Usage: api.get(v1('/contacts')) */
export function v1(path: string): string {
  return `/${API_VERSION.v1}${path.startsWith('/') ? path : `/${path}`}`
}
