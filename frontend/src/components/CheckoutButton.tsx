'use client'

import { useState } from 'react'
import { createCheckoutUrl } from '../lib/api'
import { useAuth } from '@clerk/nextjs'

interface CheckoutButtonProps {
  productId: number
}

export default function CheckoutButton({ productId }: CheckoutButtonProps) {
  const [isLoading, setIsLoading] = useState(false)
  const { getToken } = useAuth()

  const handleCheckout = async () => {
    setIsLoading(true)
    try {
      const token = await getToken()
      if (!token) {
        throw new Error('You must be signed in to create a checkout session.')
      }
      const { checkout_url } = await createCheckoutUrl(productId, token)
      window.location.href = checkout_url
    } catch (error) {
      console.error('Checkout failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <button
      onClick={handleCheckout}
      disabled={isLoading}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold text-lg disabled:opacity-50"
    >
      {isLoading ? 'Processing...' : 'Get Started'}
    </button>
  )
}
