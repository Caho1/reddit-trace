import { useEffect, useState } from 'react'

export function useLocalStorageState<T>(
  key: string,
  initialValue: T | (() => T),
) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key)
      if (raw != null) return JSON.parse(raw) as T
    } catch {
      // ignore
    }
    return typeof initialValue === 'function'
      ? (initialValue as () => T)()
      : initialValue
  })

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // ignore
    }
  }, [key, value])

  return [value, setValue] as const
}

