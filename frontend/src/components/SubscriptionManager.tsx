'use client'

import { useEffect, useState } from 'react'
import { getCurrentUser } from '../lib/api'
import { User } from '../lib/types'
import { useAuth } from '@clerk/nextjs'

export default function SubscriptionManager() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { getToken } = useAuth()

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = await getToken()
        if (!token) {
          return
        }
        const fetchedUser = await getCurrentUser(token)
        setUser(fetchedUser)
      } catch (error) {
        console.error('Failed to fetch user:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchUser()
  }, [getToken])

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h3 className="text-2xl font-bold mb-4">Subscription</h3>
      {isLoading ? (
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4">Loading subscription...</p>
        </div>
      ) : user ? (
        <div>
          <p className="text-lg">
            You are currently on the{' '}
            <span className="font-bold">{user.subscription_tier}</span> plan.
          </p>
          <p className="text-gray-600 mt-2">
            Subscription management is coming soon.
          </p>
        </div>
      ) : (
        <p>Could not load subscription information.</p>
      )}
    </div>
  )
}
