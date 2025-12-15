'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { saveAs } from 'file-saver'
import Sidebar from '@/components/Sidebar'
import FileUpload from '@/components/FileUpload'
import ReportViewer from '@/components/ReportViewer'
import SentenceGenerator from '@/components/SentenceGenerator'
import SentenceViewer from '@/components/SentenceViewer'

// API URL - usar variável de ambiente ou padrão
const API_URL = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010')
  : 'http://localhost:8010'

interface ReportData {
  relatorio: string
  numero_processo?: string
}

interface SentenceData {
  sentenca: string
  sentenca_url?: string
  referencias_url?: string
  numero_processo?: string
  documentos?: Array<{
    id: string
    relatorio: string
    fundamentacao: string
    dispositivo: string
    score: number
    rerank_score: number
  }>
}

export default function Home() {
  const [report, setReport] = useState<string | null>(null)
  const [reportProcessed, setReportProcessed] = useState(false)
  const [processNumber, setProcessNumber] = useState<string | null>(null)
  const [sentence, setSentence] = useState<string | null>(null)
  const [sentenceProcessed, setSentenceProcessed] = useState(false)
  const [systemStatus, setSystemStatus] = useState<'online' | 'offline' | 'warning'>('offline')

  // Verificar status do sistema
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/health`)
        if (response.status === 200) {
          setSystemStatus('online')
        }
      } catch (error) {
        setSystemStatus('offline')
      }
    }
    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Verifica a cada 30s
    return () => clearInterval(interval)
  }, [])

  const handleReportExtracted = (data: ReportData) => {
    setReport(data.relatorio)
    setProcessNumber(data.numero_processo || null)
    setReportProcessed(true)
  }

  const handleSentenceGenerated = (data: SentenceData) => {
    setSentence(data.sentenca)
    setSentenceProcessed(true)
    
    // Baixar arquivos se URLs disponíveis
    if (data.sentenca_url) {
      axios.get(`${API_URL}${data.sentenca_url}`, { responseType: 'blob' })
        .then(response => {
          const fileName = data.numero_processo 
            ? `sentenca_${data.numero_processo.replace(/[^0-9]/g, '')}.docx`
            : `sentenca_${new Date().toISOString().split('T')[0]}.docx`
          saveAs(response.data, fileName)
        })
        .catch(err => console.error('Erro ao baixar sentença:', err))
    }
  }

  return (
    <div style={{ display: 'flex' }}>
      <div className="main-content" style={{ flex: 1, padding: '2rem' }}>
        <div className="container">
          <div className="header">
            <h1>⚖️ SDJ - Sistema Distribuído Jurídico</h1>
            <p>Projeto Acadêmico - Sistemas Distribuídos</p>
          </div>

          {/* Seção 1: Extração do Relatório */}
          <section className="section">
            <h2>1. Extração do Relatório</h2>
            {!reportProcessed ? (
              <FileUpload
                apiUrl={API_URL}
                onSuccess={handleReportExtracted}
              />
            ) : (
              <ReportViewer
                report={report!}
                processNumber={processNumber}
                onReset={() => {
                  setReport(null)
                  setReportProcessed(false)
                  setProcessNumber(null)
                  setSentence(null)
                  setSentenceProcessed(false)
                }}
              />
            )}
          </section>

          {/* Seção 2: Geração da Sentença */}
          {reportProcessed && (
            <section className="section">
              <h2>2. Geração da Sentença</h2>
              {!sentenceProcessed ? (
                <SentenceGenerator
                  apiUrl={API_URL}
                  report={report!}
                  processNumber={processNumber}
                  onSuccess={handleSentenceGenerated}
                />
              ) : (
                <SentenceViewer
                  sentence={sentence!}
                  processNumber={processNumber}
                  onReset={() => {
                    setSentence(null)
                    setSentenceProcessed(false)
                  }}
                />
              )}
            </section>
          )}

          {/* Rodapé */}
          <footer style={{ 
            textAlign: 'center', 
            color: '#6b7280', 
            fontSize: '0.9rem', 
            marginTop: '3rem',
            paddingTop: '2rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            <p><strong>⚖️ SDJ - Sistema Distribuído Jurídico</strong></p>
            <p>Projeto Acadêmico - Sistemas Distribuídos | Versão 1.0 | 02/12/2024</p>
            <p style={{ marginTop: '1rem', fontStyle: 'italic' }}>
              ⚠️ Sempre revise o conteúdo gerado antes do uso
            </p>
          </footer>
        </div>
      </div>

      <Sidebar systemStatus={systemStatus} />
    </div>
  )
}

