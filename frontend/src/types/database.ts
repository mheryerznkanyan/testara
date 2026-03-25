export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export interface Database {
  public: {
    Tables: {
      suites: {
        Row: {
          id: string
          name: string
          description: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          updated_at?: string
        }
      }
      test_runs: {
        Row: {
          id: string
          test_name: string
          suite_id: string | null
          suite_name: string | null
          status: 'passed' | 'failed' | 'running' | 'queued'
          device: string | null
          os_version: string | null
          duration: number | null
          logs: string | null
          error_message: string | null
          screenshot_url: string | null
          execution_mode: 'local' | 'cloud'
          created_at: string
        }
        Insert: {
          id?: string
          test_name: string
          suite_id?: string | null
          suite_name?: string | null
          status: 'passed' | 'failed' | 'running' | 'queued'
          device?: string | null
          os_version?: string | null
          duration?: number | null
          logs?: string | null
          error_message?: string | null
          screenshot_url?: string | null
          execution_mode?: 'local' | 'cloud'
          created_at?: string
        }
        Update: {
          status?: 'passed' | 'failed' | 'running' | 'queued'
          duration?: number | null
          logs?: string | null
          error_message?: string | null
          screenshot_url?: string | null
        }
      }
      apps: {
        Row: {
          id: string
          name: string
          bundle_id: string | null
          ipa_url: string | null
          created_at: string
        }
        Insert: {
          id?: string
          name: string
          bundle_id?: string | null
          ipa_url?: string | null
          created_at?: string
        }
        Update: {
          name?: string
          bundle_id?: string | null
          ipa_url?: string | null
        }
      }
    }
    Views: {
      run_stats: {
        Row: {
          total: number
          passed: number
          failed: number
          running: number
          last_run_at: string | null
        }
      }
    }
  }
}
