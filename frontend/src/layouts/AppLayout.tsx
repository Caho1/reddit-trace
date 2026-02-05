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

function getTitle(pathname: string) {
  if (pathname === '/' || pathname === '') return '仪表盘'
  if (pathname.startsWith('/crawler')) return '抓取'
  if (pathname.startsWith('/subreddits')) return '板块监控'
  if (pathname.startsWith('/posts')) return '帖子'
  if (pathname.startsWith('/analyses')) return '分析结果'
  if (pathname.startsWith('/tags')) return '标签'
  return 'Reddit Trace'
}

function getSelectedKey(pathname: string) {
  if (pathname === '/' || pathname === '') return '/'
  const first = '/' + pathname.split('/').filter(Boolean)[0]
  return first
}

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { themeMode, toggleThemeMode } = useTheme()

  const title = useMemo(() => getTitle(location.pathname), [location.pathname])
  const selectedKey = useMemo(
    () => getSelectedKey(location.pathname),
    [location.pathname],
  )

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 border-r bg-card flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold tracking-wider">
              RT
            </div>
            <div>
              <div className="font-semibold text-sm">Reddit Trace</div>
              <div className="text-xs text-muted-foreground">数据挖掘看板</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => navigate(item.key)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors',
                selectedKey === item.key
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t text-xs text-muted-foreground">
          代理：/api → localhost:8000
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b bg-card flex items-center justify-between px-6">
          <h1 className="font-semibold">{title}</h1>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleThemeMode}
              aria-label={themeMode === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
            >
              {themeMode === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
                <BookOpen className="w-4 h-4 mr-1" />
                API Docs
              </a>
            </Button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
