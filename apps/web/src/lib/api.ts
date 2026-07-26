/**
 * apiFetch — thin wrapper around fetch() that automatically adds the
 * Authorization: Bearer <token> header from localStorage so callers don't
 * have to repeat that boilerplate everywhere.
 *
 * Drop-in replacement for `fetch()` — same signature, same return type.
 *
 * Usage:
 *   import { apiFetch } from "@/lib/api"
 *   const res = await apiFetch("/api/v1/devices/")
 */
export async function apiFetch(
  input: string,
  init: RequestInit = {},
): Promise<Response> {
  const token = localStorage.getItem("access_token")
  const headers = new Headers(init.headers)
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`)
  }
  return fetch(input, { ...init, headers })
}
