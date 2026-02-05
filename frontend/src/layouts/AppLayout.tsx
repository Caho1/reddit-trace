import { useMemo } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Download,
  Grid3X3,
  FileText,
  Lightbulb,
  Tags,
  Moon,
  Sun,
  BookOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useTheme } from '../state/theme'

const NAV_ITEMS = [
  { key: '/', icon: LayoutDashboard, label: '仪表盘' },
  { key: '/crawler', icon: Download, label: '抓取' },
  { key: '/subreddits', icon: Grid3X3, label: '板块监控' },
  { key: '/posts', icon: FileText, label: '帖子' },
  { key: '/analyses', icon: Lightbulb, label: '分析结果' },
  { key: '/tags', icon: Tags, label: '标签' },
]

function getSelectedKey(pathname: string) {
  if (pathname === '/' || pathname === '') return '/'
  const first = '/' + pathname.split('/').filter(Boolean)[0]
  return first
}

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { themeMode, toggleThemeMode } = useTheme()

  const selectedKey = useMemo(
    () => getSelectedKey(location.pathname),
    [location.pathname],
  )

  return (
    <div className="min-h-screen">
      {/* Floating Header */}
      <header className="fixed top-5 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-5xl">
        <div className="flex items-center justify-between gap-4 px-4 py-2.5 rounded-2xl border border-border/50 bg-background/60 backdrop-blur-xl shadow-lg">
          {/* Logo */}
          <div
            className="flex items-center gap-2 px-3 py-1.5 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-7 h-7 rounded-lg bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
              RT
            </div>
            <span className="font-semibold hidden sm:block">Reddit Trace</span>
          </div>

          {/* Divider */}
          <div className="w-px h-6 bg-border/50" />

          {/* Navigation */}
          <nav className="flex items-center gap-0.5">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                onClick={() => navigate(item.key)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-xl transition-all',
                  selectedKey === item.key
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="w-4 h-4" />
                <span className="hidden lg:inline">{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Divider */}
          <div className="w-px h-6 bg-border/50" />

          {/* Actions */}
          <div className="flex items-center gap-0.5">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-xl h-8 w-8"
              onClick={toggleThemeMode}
            >
              {themeMode === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="sm" className="rounded-xl" asChild>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
                <BookOpen className="w-4 h-4" />
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="pt-24 pb-8 px-6">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
