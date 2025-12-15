import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SDJ - Sistema Distribuído Jurídico',
  description: 'Sistema distribuído para processamento de documentos jurídicos e geração automática de sentenças',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}

