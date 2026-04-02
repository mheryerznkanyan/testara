const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('testara_token')
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...getAuthHeaders(), ...options?.headers as Record<string, string> },
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
  cloud_device?: string
  cloud_os_version?: string
  langsmith_run_id?: string
  suite_id?: string
  suite_test_id?: string
}) => apiFetch<any>('/run-test', { method: 'POST', body: JSON.stringify(body) })

// Simulators
export const getSimulators = () => apiFetch<{ devices: any[] }>('/simulators')

// Cloud
export const getCloudStatus = () => apiFetch<{
  enabled: boolean
  credentials_valid?: boolean
  app_url?: string | null
  default_device?: string
  os_version?: string
}>('/cloud/status')

export const getCloudDevices = () => apiFetch<any[]>('/cloud/devices/recommended')
export const getMacSimulators = () => apiFetch<{ devices: any[]; total: number }>('/cloud/devices/simulators')

export const uploadApp = (ipaPath: string) =>
  apiFetch<{ app_url: string; message: string }>('/cloud/upload', {
    method: 'POST',
    body: JSON.stringify({ ipa_path: ipaPath }),
  })

// Cloud discovery
interface DiscoveryScreen {
  name: string
  element_count: number
  navigation_path?: string
}

interface DiscoveryResponse {
  success: boolean
  screen_count: number
  interactive_count: number
  screens?: DiscoveryScreen[]
  error?: string | null
}

export const getDiscoveryStatus = () => apiFetch<DiscoveryResponse>('/cloud/discover/status')

export const cloudDiscover = (body: {
  app_url?: string
  device_name?: string
  os_version?: string
}) => apiFetch<DiscoveryResponse>('/cloud/discover', { method: 'POST', body: JSON.stringify(body) })

export { API_BASE }
