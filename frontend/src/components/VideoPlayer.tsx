import React, { useRef, useState, useCallback, useEffect } from 'react'

interface VideoPlayerProps {
  src: string
  poster?: string
  className?: string
}

export default function VideoPlayer({ src, poster, className = '' }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const timelineRef = useRef<HTMLDivElement>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [buffered, setBuffered] = useState(0)

  const controlsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Helpers ─────────────────────────────────────────────────────────────────

  const formatTime = (secs: number) => {
    if (!isFinite(secs)) return '0:00'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const resetControlsTimer = useCallback(() => {
    setShowControls(true)
    if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current)
    controlsTimerRef.current = setTimeout(() => {
      if (isPlaying) setShowControls(false)
    }, 3000)
  }, [isPlaying])

  // ── Video events ─────────────────────────────────────────────────────────────

  const handleCanPlay = useCallback(() => setIsLoading(false), [])
  const handleError = useCallback(() => { setIsLoading(false); setHasError(true) }, [])

  const handleTimeUpdate = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    setCurrentTime(v.currentTime)
    if (v.buffered.length) setBuffered(v.buffered.end(v.buffered.length - 1))
  }, [])

  const handleLoadedMetadata = useCallback(() => {
    setDuration(videoRef.current?.duration ?? 0)
  }, [])

  const handlePlay = useCallback(() => setIsPlaying(true), [])
  const handlePause = useCallback(() => { setIsPlaying(false); setShowControls(true) }, [])
  const handleEnded = useCallback(() => { setIsPlaying(false); setShowControls(true) }, [])

  // ── Controls ─────────────────────────────────────────────────────────────────

  const togglePlay = useCallback(() => {
    const v = videoRef.current
    if (!v) return
    v.paused ? v.play() : v.pause()
    resetControlsTimer()
  }, [resetControlsTimer])

  const toggleFullscreen = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    if (!document.fullscreenElement) {
      el.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  }, [])

  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const tl = timelineRef.current
    const v = videoRef.current
    if (!tl || !v || !duration) return
    const rect = tl.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    v.currentTime = ratio * duration
    resetControlsTimer()
  }, [duration, resetControlsTimer])

  // ── Fullscreen sync ───────────────────────────────────────────────────────────

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', handler)
    return () => document.removeEventListener('fullscreenchange', handler)
  }, [])

  // ── Cleanup ───────────────────────────────────────────────────────────────────

  useEffect(() => () => {
    if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current)
  }, [])

  // ── Derived ───────────────────────────────────────────────────────────────────

  const progressPct = duration ? (currentTime / duration) * 100 : 0
  const bufferedPct = duration ? (buffered / duration) * 100 : 0

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    /**
     * Outer wrapper: relative + padding-bottom 56.25% = 16:9 lock.
     * Container has a defined height of 0 before video loads → zero layout shift.
     */
    <div className={`relative w-full ${className}`} style={{ paddingBottom: '56.25%' }}>
      {/* ── Actual player (fills the padding trick) ── */}
      <div
        ref={containerRef}
        className="absolute inset-0 rounded-xl overflow-hidden bg-black/90 border border-white/10 backdrop-blur-sm"
        onMouseMove={resetControlsTimer}
        onMouseEnter={resetControlsTimer}
        onMouseLeave={() => isPlaying && setShowControls(false)}
        style={{ boxShadow: '0 8px 32px rgba(0,0,0,0.6)' }}
      >
        {/* ── Skeleton / loading overlay ── */}
        {isLoading && !hasError && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-zinc-900 animate-pulse">
            <div className="flex flex-col items-center gap-3">
              {/* Play icon shimmer */}
              <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-white/20" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <div className="h-1.5 w-24 rounded-full bg-white/10" />
            </div>
            {/* Bottom timeline skeleton */}
            <div className="absolute bottom-0 inset-x-0 h-1 bg-white/5" />
          </div>
        )}

        {/* ── Error state ── */}
        {hasError && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-zinc-950">
            <svg className="w-10 h-10 text-red-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p className="text-sm text-white/50">Failed to load video</p>
          </div>
        )}

        {/* ── Native video ── */}
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          className={`absolute inset-0 w-full h-full object-contain cursor-pointer transition-opacity duration-500 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
          preload="metadata"
          playsInline
          onClick={togglePlay}
          onCanPlay={handleCanPlay}
          onError={handleError}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={handlePlay}
          onPause={handlePause}
          onEnded={handleEnded}
        />

        {/* ── Controls overlay ── */}
        {!hasError && (
          <div
            className={`absolute inset-0 flex flex-col justify-end transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
            style={{
              background: 'linear-gradient(to top, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.1) 40%, transparent 100%)'
            }}
          >
            {/* ── Timeline ── */}
            <div className="px-3 pb-1">
              <div
                ref={timelineRef}
                className="relative h-1 rounded-full bg-white/20 cursor-pointer group"
                onClick={handleTimelineClick}
              >
                {/* Buffered */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-white/25 transition-all duration-300"
                  style={{ width: `${bufferedPct}%` }}
                />
                {/* Played */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-white transition-all duration-100"
                  style={{ width: `${progressPct}%` }}
                />
                {/* Thumb — visible on hover */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ left: `calc(${progressPct}% - 6px)` }}
                />
              </div>
            </div>

            {/* ── Bottom bar ── */}
            <div className="flex items-center gap-2 px-3 pb-2.5">
              {/* Play/Pause */}
              <button
                onClick={togglePlay}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-sm"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>

              {/* Time */}
              <span className="text-white/70 text-xs tabular-nums select-none">
                {formatTime(currentTime)}
                <span className="text-white/30 mx-1">/</span>
                {formatTime(duration)}
              </span>

              {/* Spacer */}
              <div className="flex-1" />

              {/* Fullscreen */}
              <button
                onClick={toggleFullscreen}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-sm"
                aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
              >
                {isFullscreen ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9 3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5 5.25 5.25" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
