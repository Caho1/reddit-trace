import type { AxiosError } from 'axios'

type MaybeAxiosError = AxiosError<{ detail?: unknown }>

export function getErrorMessage(error: unknown): string {
  if (typeof error === 'string') return error
  if (error instanceof Error) return error.message

  const axiosError = error as MaybeAxiosError
  const detail = axiosError?.response?.data?.detail
  if (typeof detail === 'string') return detail

  const anyError = error as { message?: unknown }
  if (typeof anyError?.message === 'string') return anyError.message

  return '请求失败，请稍后重试'
}

