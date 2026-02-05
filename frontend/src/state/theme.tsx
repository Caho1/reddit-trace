import { createContext, useContext, type ReactNode } from 'react'

export type ThemeMode = 'light' | 'dark'

type ThemeContextValue = {
  themeMode: ThemeMode
  setThemeMode: (value: ThemeMode) => void
  toggleThemeMode: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({
  children,
  themeMode,
  setThemeMode,
}: {
  children: ReactNode
  themeMode: ThemeMode
  setThemeMode: (value: ThemeMode) => void
}) {
  return (
    <ThemeContext.Provider
      value={{
        themeMode,
        setThemeMode,
        toggleThemeMode: () => setThemeMode(themeMode === 'dark' ? 'light' : 'dark'),
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('ThemeProvider missing')
  return ctx
}

