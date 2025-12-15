'use client'

interface SidebarProps {
  systemStatus: 'online' | 'offline' | 'warning'
}

export default function Sidebar({ systemStatus }: SidebarProps) {
  return (
    <div className="sidebar">
      <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem' }}>📋 Instruções de Uso</h2>
      
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>🚀 Como usar o SDJ</h3>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>1. Extração do Relatório</h4>
          <ul style={{ paddingLeft: '1.5rem', color: '#6b7280', fontSize: '0.9rem' }}>
            <li>Faça o upload do processo em PDF (máx. 200MB)</li>
            <li>Clique em "Extrair Relatório"</li>
            <li>Aguarde o processamento completo</li>
            <li>Baixe o relatório em formato DOCX</li>
          </ul>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>2. Geração da Sentença</h4>
          <ul style={{ paddingLeft: '1.5rem', color: '#6b7280', fontSize: '0.9rem' }}>
            <li><strong>Instruções Adicionais</strong> (opcional): Orientações específicas</li>
            <li><strong>Documentos de Referência</strong> (opcional): Sentenças similares em DOCX</li>
            <li><strong>Parâmetros de Busca</strong>: Top K e Rerank Top K</li>
          </ul>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>📁 Formatos Suportados</h4>
          <ul style={{ paddingLeft: '1.5rem', color: '#6b7280', fontSize: '0.9rem' }}>
            <li><strong>Upload</strong>: PDF (processos)</li>
            <li><strong>Referências</strong>: DOCX (sentenças)</li>
            <li><strong>Download</strong>: DOCX (relatórios e sentenças)</li>
          </ul>
        </div>

        <div style={{ 
          padding: '1rem', 
          background: '#dbeafe', 
          borderRadius: '6px',
          border: '1px solid #93c5fd',
          marginBottom: '1.5rem'
        }}>
          <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>⚠️ Dicas Importantes</h4>
          <ul style={{ paddingLeft: '1.5rem', fontSize: '0.9rem', color: '#1e40af' }}>
            <li>Certifique-se de que o PDF seja legível</li>
            <li>Inclua sentenças similares para melhor fundamentação</li>
            <li>Sempre revise a sentença gerada antes do uso</li>
          </ul>
        </div>
      </div>

      <div style={{ 
        padding: '1rem', 
        background: '#f9fafb', 
        borderRadius: '6px',
        border: '1px solid #e5e7eb'
      }}>
        <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>📊 Status do Sistema</h4>
        <div style={{ marginTop: '0.5rem' }}>
          {systemStatus === 'online' && (
            <span className="status-badge status-online">🟢 Sistema Online</span>
          )}
          {systemStatus === 'offline' && (
            <span className="status-badge status-offline">🔴 Sistema Offline</span>
          )}
          {systemStatus === 'warning' && (
            <span className="status-badge status-warning">🟡 Sistema com Problemas</span>
          )}
        </div>
      </div>

      <div style={{ 
        marginTop: '2rem', 
        padding: '1rem', 
        background: '#f9fafb', 
        borderRadius: '6px',
        fontSize: '0.85rem',
        color: '#6b7280'
      }}>
        <h4 style={{ marginBottom: '0.5rem', fontWeight: 600 }}>📞 Informações do Projeto</h4>
        <p><strong>SDJ - Sistema Distribuído Jurídico</strong></p>
        <p>Projeto acadêmico para Sistemas Distribuídos</p>
        <p>Versão: 1.0 (Protótipo)</p>
        <p>Data: 02/12/2024</p>
      </div>
    </div>
  )
}

