import { NavLink } from 'react-router-dom'
import { Users, PlusCircle, FolderOpen } from 'lucide-react'
import type { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header with glassmorphism */}
      <header className="sticky top-0 z-50 glass-card border-b border-white/10 mx-4 mt-4 rounded-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Aiinflu
            </h1>
            
            <nav className="flex gap-2">
              <NavLink
                to="/bloggers"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-5 py-2.5 rounded-xl transition-smooth ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                <Users size={20} />
                <span className="font-medium">Блогеры</span>
              </NavLink>
              
              <NavLink
                to="/create"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-5 py-2.5 rounded-xl transition-smooth ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                <PlusCircle size={20} />
                <span className="font-medium">Создание</span>
              </NavLink>
              
              <NavLink
                to="/projects"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-5 py-2.5 rounded-xl transition-smooth ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-white/70 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                <FolderOpen size={20} />
                <span className="font-medium">Проекты</span>
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="glass-card border-t border-white/10 mx-4 mb-4 rounded-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-white/50 text-sm">
          © 2025 Aiinflu - AI Content Automation
        </div>
      </footer>
    </div>
  )
}
