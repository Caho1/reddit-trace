import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'

import { useLocalStorageState } from './hooks/useLocalStorageState'
import { ThemeProvider, type ThemeMode } from './state/theme'
import { router } from './router'
import './styles/global.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

function getPreferredTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function App() {
  const [themeMode, setThemeMode] = useLocalStorageState<ThemeMode>('rt.theme', () =>
    getPreferredTheme(),
  )

  useEffect(() => {
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(themeMode)
  }, [themeMode])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider themeMode={themeMode} setThemeMode={setThemeMode}>
        <RouterProvider router={router} />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
