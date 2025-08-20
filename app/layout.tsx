import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AutoCrate Web - AI-Enhanced Crate Design System',
  description: 'Professional automated crate design with ASTM compliance, material optimization, and Siemens NX integration. Built with AI-enhanced algorithms for engineering excellence.',
  keywords: ['autocrate', 'crate design', 'engineering', 'automation', 'ASTM', 'Siemens NX', 'AI-enhanced'],
  authors: [{ name: 'AutoCrate Team' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: 'AutoCrate Web - Automated Crate Design System',
    description: 'Professional crate design automation with AI-enhanced engineering calculations',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AutoCrate Web - AI-Enhanced Engineering Software',
    description: 'Automated crate design with ASTM compliance and NX integration',
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 antialiased`}>
        <div className="min-h-full flex flex-col">
          {children}
        </div>
      </body>
    </html>
  )
}