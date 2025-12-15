'use client'

import { useState } from 'react'
import axios from 'axios'
import { pollTaskStatus, TaskStatus } from '@/lib/taskPolling'

interface FileUploadProps {
  apiUrl: string
  onSuccess: (data: { relatorio: string; numero_processo?: string }) => void
}

export default function FileUpload({ apiUrl, onSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      if (selectedFile.size > 200 * 1024 * 1024) {
        setError('Arquivo muito grande. Máximo: 200MB')
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleSubmit = async () => {
    if (!file) {
      setError('Selecione um arquivo PDF')
      return
    }

    setLoading(true)
    setError(null)
    setProgressMessage('Enfileirando tarefa...')

    try {
      // 1. Enfileira a tarefa
      const formData = new FormData()
      formData.append('pdf', file)

      const queueResponse = await axios.post(`${apiUrl}/queue/processar`, formData, {
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
            setProgressMessage('Processando PDF...')
          }
        },
        onComplete: (result) => {
          if (result && result.relatorio && result.relatorio.length > 50) {
            setProgressMessage('Processamento concluído!')
            onSuccess(result)
          } else {
            setError('Relatório muito pequeno ou inválido')
          }
        },
        onError: (errorMsg) => {
          setError(errorMsg)
        },
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao processar PDF')
    } finally {
      setLoading(false)
      setTimeout(() => setProgressMessage(null), 2000)
    }
  }

  return (
    <div>
      <div className="file-upload">
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          disabled={loading}
          style={{ display: 'none' }}
          id="pdf-upload"
        />
        <label htmlFor="pdf-upload" style={{ cursor: 'pointer' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📎</div>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
            {file ? file.name : 'Clique para selecionar um PDF'}
          </div>
          <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
            Máximo: 200MB
          </div>
        </label>
      </div>

      {file && (
        <div style={{ marginTop: '1rem' }}>
          <button
            className="button"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? '🔄 Processando...' : '🔍 Extrair Relatório'}
          </button>
        </div>
      )}

      {loading && progressMessage && (
        <div className="alert alert-info" style={{ marginTop: '1rem' }}>
          🔄 {progressMessage}
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="alert alert-info">
          ⏱️ O processamento pode demorar alguns minutos dependendo do tamanho do arquivo. Aguarde...
        </div>
      )}
    </div>
  )
}

