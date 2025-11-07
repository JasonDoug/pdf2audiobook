import axios from 'axios'
import { Job, Product, User } from './types'

/**
 * API base URL strategy:
 * - In production, set NEXT_PUBLIC_API_URL to your backend origin, e.g. https://pdf2audiobook.xyz
 * - In development, set it to http://localhost:8000
 * - We normalize to always target the versioned API under /api/v1.
 */
const getApiBaseUrl = () => {
  const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const url = new URL(raw)
    // If the path already ends with /api/v1, respect it as-is
    if (url.pathname.replace(/\/+$/, '') === '/api/v1') {
      return url.toString().replace(/\/+$/, '')
    }

    // Otherwise, ensure /api/v1 is appended
    url.pathname = '/api/v1'
    return url.toString().replace(/\/+$/, '')
  } catch {
    // Fallback: assume the raw value is already a correct base
    return raw.replace(/\/+$/, '')
  }
}

export const API_BASE_URL = getApiBaseUrl()

const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

const getHeaders = (token: string) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
})

export const createJob = async (
  formData: FormData,
  token: string
): Promise<Job> => {
  const response = await apiClient.post('/jobs/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      Authorization: `Bearer ${token}`,
    },
  })
  return response.data
}

export const getJobs = async (token: string): Promise<Job[]> => {
  const response = await apiClient.get('/jobs/', getHeaders(token))
  return response.data
}

export const getJob = async (jobId: number, token: string): Promise<Job> => {
  const response = await apiClient.get(`/jobs/${jobId}`, getHeaders(token))
  return response.data
}

export const getJobStatus = async (
  jobId: number,
  token: string
): Promise<any> => {
  const response = await apiClient.get(
    `/jobs/${jobId}/status`,
    getHeaders(token)
  )
  return response.data
}

export const getCurrentUser = async (token: string): Promise<User> => {
  const response = await apiClient.get('/auth/me', getHeaders(token))
  return response.data
}

export const updateUser = async (
  userUpdate: any,
  token: string
): Promise<User> => {
  const response = await apiClient.put(
    '/auth/me',
    userUpdate,
    getHeaders(token)
  )
  return response.data
}

export const verifyToken = async (token: string): Promise<any> => {
  const response = await apiClient.post(
    '/auth/verify',
    { token },
    getHeaders(token)
  )
  return response.data
}

/**
 * Retrieve public products.
 * - If a token is provided, it will be sent (useful for authenticated pricing/entitlements).
 * - If no token is provided, falls back to an unauthenticated public request (for marketing/preview).
 * - When NEXT_PUBLIC_DEV_BYPASS_PAYMENTS === 'true', frontend can call this freely in tests.
 */
export const getProducts = async (token?: string): Promise<Product[]> => {
  const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_PAYMENTS === 'true'

  if (token) {
    const response = await apiClient.get(
      '/payments/products',
      getHeaders(token)
    )
    return response.data
  }

  // No token: allow public access or dev bypass
  const response = await apiClient.get('/payments/products', {
    headers: devBypass ? { 'X-Dev-Bypass-Payments': 'true' } : {},
  })
  return response.data
}

/**
 * Create a Paddle checkout URL.
 * - Requires a valid user token in normal operation.
 * - When NEXT_PUBLIC_DEV_BYPASS_PAYMENTS === 'true', a developer can call this
 *   without a token; an identifying header is sent so the backend can treat it
 *   as a non-billable test flow if implemented.
 */
export const createCheckoutUrl = async (
  productId: number,
  token?: string
): Promise<any> => {
  const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_PAYMENTS === 'true'

  if (!token && !devBypass) {
    throw new Error('You must be signed in to create a checkout session.')
  }

  const headers = token
    ? getHeaders(token).headers
    : { 'X-Dev-Bypass-Payments': 'true' }

  const response = await apiClient.post(
    '/payments/checkout-url',
    { productId },
    { headers }
  )
  return response.data
}
