import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import Header from '../components/Header'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PDF2AudioBook - Convert PDFs to Audiobooks',
  description:
    'A modern SaaS platform for converting scientific PDFs and novels into high-quality audiobooks or AI-powered summaries.',
  keywords: [
    'PDF',
    'audiobook',
    'text-to-speech',
    'OCR',
    'AI summaries',
    'research papers',
    'scientific articles',
    'novels',
  ],
  authors: [{ name: 'PDF2AudioBook Team' }],
  openGraph: {
    title: 'PDF2AudioBook - Convert PDFs to Audiobooks',
    description:
      'Transform your research papers and novels into immersive listening experiences or concise AI summaries.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PDF2AudioBook - Convert PDFs to Audiobooks',
    description:
      'Transform your research papers and novels into immersive listening experiences or concise AI summaries.',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const devBypassPayments =
    process.env.NEXT_PUBLIC_DEV_BYPASS_PAYMENTS === 'true'

  return (
    <ClerkProvider>
      <html lang="en">
        <body
          className={`${inter.className} bg-slate-50 text-slate-900 antialiased`}
        >
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">
              {devBypassPayments && (
                <div className="bg-amber-50 border-b border-amber-200 text-amber-800 text-xs sm:text-sm px-4 py-2 flex items-center justify-center">
                  <span className="font-semibold mr-1">Developer mode:</span>
                  Payments and gating are bypassed for testing. Do not use in
                  production.
                </div>
              )}
              {children}
            </main>
            <footer className="border-t border-slate-200 bg-white/70 backdrop-blur-sm">
              <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs sm:text-sm text-slate-500">
                <div>
                  © {new Date().getFullYear()} PDF2AudioBook. Designed for
                  researchers, students, and readers.
                </div>
                <div className="flex gap-4">
                  <span className="hidden sm:inline">
                    AI summaries for scientific PDFs · Word-for-word narration
                    for books
                  </span>
                  <a
                    href="https://pdf2audiobook.xyz/docs"
                    className="hover:text-slate-800 transition-colors"
                  >
                    API Docs
                  </a>
                </div>
              </div>
            </footer>
          </div>
        </body>
      </html>
    </ClerkProvider>
  )
}
