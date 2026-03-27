export type RunStatus = 'Passed' | 'Failed' | 'Running'
export type SuiteStatus = RunStatus | 'Not Run'

export interface TestRun {
  id: string
  testName: string
  suite: string
  status: RunStatus
  device: string
  os: string
  duration: string
  date: string
  logs: string
  errorMessage?: string
}

export interface Suite {
  id: string
  name: string
  testCount: number
  lastStatus: SuiteStatus
  createdAt: string
  description: string
}

export interface SuiteTest {
  id: string
  suite_id: string
  name: string
  description: string | null
  test_code: string
  class_name: string | null
  quality_score: number | null
  quality_grade: string | null
  last_status: 'passed' | 'failed' | 'running' | 'not_run' | null
  last_run_at: string | null
  last_run_id: string | null
  position: number
  created_at: string
  updated_at: string
}

export interface SuiteWithStats {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  test_count: number
  passed_count: number
  failed_count: number
  not_run_count: number
}

export interface TestResult {
  test_code: string
  test_type: string
  class_name: string
  metadata?: {
    quality_report?: {
      overall_score: number
      grade: string
      confidence: string
      recommendations: string[]
    }
    enrichment?: {
      original_description: string
      enriched_description: string
    }
    langsmith_run_id?: string
  }
}

export interface ExecutionResult {
  success: boolean
  test_id: string
  execution_mode?: string
  video_url: string | null
  screenshot: string | null
  logs: string
  duration: number
  device: string | null
  os_version: string | null
  ios_version?: string
  error?: string
  session_id?: string | null
  browserstack_url?: string | null
}

export interface SimulatorDevice {
  name: string
  udid: string
  ios_version: string
  state: string
}
