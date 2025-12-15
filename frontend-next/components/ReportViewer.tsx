'use client'

import { useState } from 'react'
import { saveAs } from 'file-saver'

interface ReportViewerProps {
  report: string
  processNumber: string | null
  onReset: () => void
}

export default function ReportViewer({ report, processNumber, onReset }: ReportViewerProps) {
  const [expanded, setExpanded] = useState(true)

  const handleDownload = () => {
    // Criar DOCX simples (em produção, usar biblioteca como docx)
    const blob = new Blob([report], { type: 'text/plain' })
    const fileName = processNumber
      ? `relatorio_${processNumber.replace(/[^0-9]/g, '')}.txt`
      : `relatorio_${new Date().toISOString().split('T')[0]}.txt`
    saveAs(blob, fileName)
  }

  return (
    <div>
      <div className="alert alert-success">
        {processNumber 
          ? `📄 Relatório extraído com sucesso! Processo nº ${processNumber}`
          : '📄 Relatório extraído com sucesso!'
        }
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <button
          className="button"
          onClick={() => setExpanded(!expanded)}
          style={{ marginRight: '1rem' }}
        >
          {expanded ? '📄 Ocultar Relatório' : '📄 Visualizar Relatório'}
        </button>
        <button
          className="button"
          onClick={handleDownload}
          style={{ background: '#10b981', marginRight: '1rem' }}
        >
          📥 Baixar Relatório
        </button>
        <button
          className="button"
          onClick={onReset}
          style={{ background: '#6b7280' }}
        >
          🔄 Novo Processo
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
            <span>Tamanho: {report.length} caracteres</span>
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
            {report}
          </pre>
        </div>
      )}
    </div>
  )
}

