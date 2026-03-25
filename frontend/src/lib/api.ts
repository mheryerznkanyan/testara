const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => null)
    throw new Error(err?.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

// Health
export const getHealth = () => apiFetch<{ status: string }>('/health')

// Test generation
export const generateTest = (body: {
  test_description: string
  test_type?: string
  include_comments?: boolean
  discovery_enabled?: boolean
  bundle_id?: string
  device_udid?: string
}) => apiFetch<any>('/generate-test-with-rag', { method: 'POST', body: JSON.stringify(body) })

// Test execution
export const runTest = (body: {
  test_code: string
  bundle_id?: string
  device_udid?: string
  execution_mode?: 'local' | 'cloud'
  langsmith_run_id?: string
}) => apiFetch<any>('/run-test', { method: 'POST', body: JSON.stringify(body) })

// Simulators
export const getSimulators = () => apiFetch<{ devices: any[] }>('/simulators')

// Cloud
export const getCloudStatus = () => apiFetch<{
  connected: boolean
  defaultDevice?: string
  osVersion?: string
}>('/cloud/status')

export const getCloudDevices = () => apiFetch<any[]>('/cloud/devices/recommended')

export const uploadApp = (ipaPath: string) =>
  apiFetch<{ app_url: string; message: string }>('/cloud/upload', {
    method: 'POST',
    body: JSON.stringify({ ipa_path: ipaPath }),
  })

export { API_BASE }
