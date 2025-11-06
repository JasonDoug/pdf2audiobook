'use client';

import { UserButton, useUser } from '@clerk/nextjs';
import Link from 'next/link';
import { FileText, Upload, History, CreditCard } from 'lucide-react';

export default function Header() {
  const { isSignedIn } = useUser();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">PDF2AudioBook</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            {isSignedIn ? (
              <>
                <Link
                  href="/upload"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-1"
                >
                  <Upload className="h-4 w-4" />
                  <span>Upload</span>
                </Link>
                <Link
                  href="/jobs"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-1"
                >
                  <History className="h-4 w-4" />
                  <span>My Jobs</span>
                </Link>
                <Link
                  href="/pricing"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-1"
                >
                  <CreditCard className="h-4 w-4" />
                  <span>Pricing</span>
                </Link>
              </>
            ) : (
              <Link
                href="/pricing"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Pricing
              </Link>
            )}
          </nav>

          {/* User Button */}
          <div className="flex items-center space-x-4">
            {isSignedIn ? (
              <UserButton afterSignOutUrl="/" />
            ) : (
              <div className="flex space-x-2">
                <Link
                  href="/sign-in"
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sign In
                </Link>
                <Link
                  href="/sign-up"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}