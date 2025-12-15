'use client'

import { useState } from 'react'
import axios from 'axios'
import { pollTaskStatus, TaskStatus } from '@/lib/taskPolling'

interface SentenceGeneratorProps {
  apiUrl: string
  report: string
  processNumber: string | null
  onSuccess: (data: {
    sentenca: string
    sentenca_url?: string
    referencias_url?: string
    numero_processo?: string
  }) => void
}

export default function SentenceGenerator({ apiUrl, report, processNumber, onSuccess }: SentenceGeneratorProps) {
  const [instructions, setInstructions] = useState('')
  const [topK, setTopK] = useState(10)
  const [rerankTopK, setRerankTopK] = useState(5)
  const [referenceFiles, setReferenceFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).filter(f => f.name.endsWith('.docx'))
      setReferenceFiles(files)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    setProgressMessage('Enfileirando tarefa...')

    try {
      // 1. Enfileira a tarefa
      const formData = new FormData()
      formData.append('relatorio', report)
      formData.append('instrucoes_usuario', instructions)
      formData.append('top_k', topK.toString())
      formData.append('rerank_top_k', rerankTopK.toString())
      formData.append('buscar_na_base', 'true')
      if (processNumber) {
        formData.append('numero_processo', processNumber)
      }

      referenceFiles.forEach(file => {
        formData.append('arquivos_referencia', file)
      })

      const queueResponse = await axios.post(`${apiUrl}/queue/gerar-sentenca`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const taskId = queueResponse.data.task_id
      setProgressMessage('Tarefa enfileirada. Aguardando processamento...')

      // 2. Faz polling do status
      await pollTaskStatus(apiUrl, taskId, {
        interval: 2000, // 2 segundos
        timeout: 30 * 60 * 1000, // 30 minutos
        onUpdate: (status: TaskStatus) => {
          if (status.progress) {
            setProgressMessage(status.progress)
          } else if (status.status === 'PROCESSING') {
            setProgressMessage('Gerando sentença...')
          }
        },
        onComplete: (result) => {
          if (result && result.sentenca && result.sentenca.length > 50) {
            setProgressMessage('Geração concluída!')
            onSuccess(result)
          } else {
            setError('Sentença muito pequena ou inválida')
          }
        },
        onError: (errorMsg) => {
          setError(errorMsg)
        },
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao gerar sentença')
    } finally {
      setLoading(false)
      setTimeout(() => setProgressMessage(null), 2000)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          📝 Instruções Adicionais (opcional)
        </label>
        <textarea
          className="textarea"
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Ex: enfatizar danos morais, valor específico de indenização, etc."
          disabled={loading}
        />
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
          📄 Documentos de Referência (DOCX) - opcional
        </label>
        <input
          type="file"
          accept=".docx"
          multiple
          onChange={handleFileChange}
          disabled={loading}
          style={{ marginBottom: '0.5rem' }}
        />
        {referenceFiles.length > 0 && (
          <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
            {referenceFiles.length} arquivo(s) selecionado(s)
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
            Top K (busca semântica)
          </label>
          <input
            type="number"
            min="1"
            max="20"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value))}
            className="input"
            disabled={loading}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
            Rerank Top K
          </label>
          <input
            type="number"
            min="1"
            max="10"
            value={rerankTopK}
            onChange={(e) => setRerankTopK(parseInt(e.target.value))}
            className="input"
            disabled={loading}
          />
        </div>
      </div>

      <button
        className="button"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? '🔄 Gerando Sentença...' : '⚖️ Gerar Sentença'}
      </button>

      {loading && progressMessage && (
        <div className="alert alert-info" style={{ marginTop: '1rem' }}>
          🔄 {progressMessage}
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginTop: '1rem' }}>
          ❌ {error}
        </div>
      )}
    </div>
  )
}

