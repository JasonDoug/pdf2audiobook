'use client'

import { Product } from '../lib/types'
import { CheckCircle } from 'lucide-react'

interface PricingCardProps {
  product: Product
}

export default function PricingCard({ product }: PricingCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-8 flex flex-col">
      <h3 className="text-2xl font-bold text-center mb-4">{product.name}</h3>
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
        <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold text-lg">
          Get Started
        </button>
      </div>
    </div>
  )
}
