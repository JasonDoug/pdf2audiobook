'use client'

import { useEffect, useState } from 'react'
import { getProducts } from '../../lib/api'
import { Product } from '../../lib/types'
import { CheckCircle } from 'lucide-react'
import CheckoutButton from '../../components/CheckoutButton'
import { useAuth } from '@clerk/nextjs'

export default function PricingPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { getToken } = useAuth()

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const token = await getToken()
        if (!token) {
          return
        }
        const fetchedProducts = await getProducts(token)
        setProducts(fetchedProducts)
      } catch (error) {
        console.error('Failed to fetch products:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchProducts()
  }, [getToken])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
          Pricing Plans
        </h1>
        <p className="text-xl text-gray-600">
          Choose the plan that's right for you.
        </p>
      </div>

      {isLoading ? (
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4">Loading plans...</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-3 gap-8">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-white rounded-lg shadow-lg p-8 flex flex-col"
            >
              <h3 className="text-2xl font-bold text-center mb-4">
                {product.name}
              </h3>
              <p className="text-center text-gray-600 mb-8 h-16">
                {product.description}
              </p>
              <div className="text-center text-4xl font-bold mb-8">
                ${product.price}
                {product.type === 'subscription' && (
                  <span className="text-lg font-normal">/mo</span>
                )}
              </div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center">
                  <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                  <span>{product.credits_included} conversions</span>
                </li>
                {product.type === 'subscription' && (
                  <li className="flex items-center">
                    <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                    <span>Billed monthly</span>
                  </li>
                )}
              </ul>
              <div className="mt-auto">
                <CheckoutButton productId={product.id} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
