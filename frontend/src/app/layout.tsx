import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from '@clerk/nextjs';
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PDF2AudioBook - Convert PDFs to Audiobooks",
  description:
    "A SaaS platform for converting PDF documents to audiobooks using OCR and text-to-speech technology.",
  keywords: ["PDF", "audiobook", "text-to-speech", "OCR", "conversion"],
  authors: [{ name: "PDF2AudioBook Team" }],
  openGraph: {
    title: "PDF2AudioBook - Convert PDFs to Audiobooks",
    description: "Transform your PDF documents into high-quality audiobooks with advanced AI technology.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PDF2AudioBook - Convert PDFs to Audiobooks",
    description: "Transform your PDF documents into high-quality audiobooks with advanced AI technology.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
