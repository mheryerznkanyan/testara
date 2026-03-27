'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { Loader2 } from 'lucide-react'

function CallbackHandler() {
  const { handleOAuthTokens } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        let accessToken: string | null = null
        let refreshToken: string | null = null
        let errorMsg: string | null = null

        // Try hash fragment first (#access_token=...&refresh_token=...)
        const hash = window.location.hash.substring(1)
        if (hash) {
          const hashParams = new URLSearchParams(hash)
          accessToken = hashParams.get('access_token')
          refreshToken = hashParams.get('refresh_token')
          errorMsg = hashParams.get('error_description') || hashParams.get('error')
        }

        // Try query params (?access_token=...)
        if (!accessToken) {
          accessToken = searchParams.get('access_token')
          refreshToken = searchParams.get('refresh_token')
          errorMsg = errorMsg || searchParams.get('error_description') || searchParams.get('error')
        }

        // Try PKCE code exchange (?code=...)
        const code = searchParams.get('code')

        if (errorMsg) {
          setError(errorMsg)
          return
        }

        if (accessToken && refreshToken) {
          handleOAuthTokens(accessToken, refreshToken)
            .then(() => router.replace('/dashboard'))
            .catch(() => setError('Failed to complete sign-in'))
          return
        }

        if (code) {
          fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/google/callback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
          })
            .then((res) => {
              if (!res.ok) throw new Error('Code exchange failed')
              return res.json()
            })
            .then((data) => {
              if (data.session?.access_token) {
                return handleOAuthTokens(data.session.access_token, data.session.refresh_token)
              }
              throw new Error('No session returned')
            })
            .then(() => router.replace('/dashboard'))
            .catch(() => setError('Failed to exchange authorization code'))
          return
        }

        setError('No authentication tokens received. Please try signing in again.')
      } catch {
        setError('An unexpected error occurred during sign-in')
      }
    }, 100)

    return () => clearTimeout(timer)
  }, [handleOAuthTokens, router, searchParams])

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 text-center max-w-sm">
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
        <a href="/login" className="text-sm text-blue-400 hover:underline">
          Back to sign in
        </a>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      <p className="text-sm text-muted-foreground">Completing sign-in...</p>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  )
}
