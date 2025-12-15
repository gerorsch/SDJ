'use client'

import { useState } from 'react'
import { saveAs } from 'file-saver'
import axios from 'axios'

interface SentenceViewerProps {
  sentence: string
  processNumber: string | null
  onReset: () => void
}

export default function SentenceViewer({ sentence, processNumber, onReset }: SentenceViewerProps) {
  const [expanded, setExpanded] = useState(true)
  const [downloading, setDownloading] = useState(false)

  const handleDownload = () => {
    // Criar arquivo de texto simples (em produção, usar biblioteca para DOCX)
    const blob = new Blob([sentence], { type: 'text/plain' })
    const fileName = processNumber
      ? `sentenca_${processNumber.replace(/[^0-9]/g, '')}_${new Date().toISOString().split('T')[0]}.txt`
      : `sentenca_${new Date().toISOString().split('T')[0]}.txt`
    saveAs(blob, fileName)
  }

  return (
    <div>
      <div className="alert alert-success">
        {processNumber
          ? `⚖️ Sentença gerada com sucesso! Processo nº ${processNumber}`
          : '⚖️ Sentença gerada com sucesso!'
        }
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <button
          className="button"
          onClick={() => setExpanded(!expanded)}
          style={{ marginRight: '1rem' }}
        >
          {expanded ? '📄 Ocultar Sentença' : '📄 Visualizar Sentença'}
        </button>
        <button
          className="button"
          onClick={handleDownload}
          disabled={downloading}
          style={{ background: '#10b981', marginRight: '1rem' }}
        >
          {downloading ? '📥 Baixando...' : '📥 Baixar Sentença'}
        </button>
        <button
          className="button"
          onClick={onReset}
          style={{ background: '#6b7280' }}
        >
          🔄 Gerar Nova Sentença
        </button>
      </div>

      {expanded && (
        <div style={{
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '6px',
          padding: '1.5rem',
          marginTop: '1rem',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '1rem',
            fontSize: '0.9rem',
            color: '#6b7280'
          }}>
            <span>Tamanho: {sentence.length} caracteres</span>
            {processNumber && <span>Processo: {processNumber}</span>}
          </div>
          <pre style={{
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            fontFamily: 'inherit',
            fontSize: '0.9rem',
            lineHeight: '1.6',
            color: '#1f2937'
          }}>
            {sentence}
          </pre>
        </div>
      )}
    </div>
  )
}

