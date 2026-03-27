import Sidebar from '@/components/Sidebar'
import { Header } from '@/components/layout/header'
import { AuthGuard } from '@/components/auth-guard'
import { MobileNav } from '@/components/mobile-nav'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden bg-void">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-auto bg-void scroll-smooth">
            {children}
          </main>
        </div>
        <MobileNav />
      </div>
    </AuthGuard>
  )
}
