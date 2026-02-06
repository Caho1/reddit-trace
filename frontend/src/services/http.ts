import axios from 'axios'

export const http = axios.create({
  baseURL: '/api',
  timeout: 60_000, // 增加到 60 秒，因为后端请求 Reddit 可能需要较长时间
})

// 响应拦截器：处理错误
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请检查后端服务是否运行'
    } else if (error.code === 'ERR_NETWORK') {
      error.message = '网络错误，请检查后端服务是否运行在 localhost:8000'
    } else if (error.response?.data?.detail) {
      // 后端返回的结构化错误
      const detail = error.response.data.detail
      if (typeof detail === 'object') {
        error.message = `[${detail.step || '未知'}] ${detail.message}`
      } else {
        error.message = detail
      }
    }
    return Promise.reject(error)
  }
)

