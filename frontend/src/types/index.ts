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
  video_url: string | null
  screenshot: string | null
  logs: string
  duration: number
  device: string
  ios_version: string
  error?: string
}

export interface SimulatorDevice {
  name: string
  udid: string
  ios_version: string
  state: string
}
