import { fetchAutenticado } from './authService'

const API_CARRINHO = '/api/v1/carrinho'
const API_SIMULADOS = '/api/v1/simulados'

const CHAVE_SESSAO = 'enade-hub-session-id'

export function obterSessionId() {
  let sessionId = localStorage.getItem(CHAVE_SESSAO)

  if (!sessionId) {
    sessionId = `enade-${crypto.randomUUID()}`
    localStorage.setItem(CHAVE_SESSAO, sessionId)
  }

  return sessionId
}

async function tratarResposta(resposta) {
  if (!resposta.ok) {
    let mensagem = 'Não foi possível concluir a operação.'

    try {
      const dados = await resposta.json()
      mensagem = dados.detail || mensagem
    } catch {
      // Mantém a mensagem padrão.
    }

    throw new Error(mensagem)
  }

  return resposta.json()
}

export async function buscarCarrinho() {
  const sessionId = obterSessionId()

  const resposta = await fetch(
    `${API_CARRINHO}/${encodeURIComponent(sessionId)}`
  )

  return tratarResposta(resposta)
}

export async function adicionarQuestao(questaoId) {
  const sessionId = obterSessionId()

  const resposta = await fetch(
    `${API_CARRINHO}/${encodeURIComponent(sessionId)}/adicionar/${encodeURIComponent(questaoId)}`,
    { method: 'POST' }
  )

  return tratarResposta(resposta)
}

export async function removerQuestao(questaoId) {
  const sessionId = obterSessionId()

  const resposta = await fetch(
    `${API_CARRINHO}/${encodeURIComponent(sessionId)}/remover/${encodeURIComponent(questaoId)}`,
    { method: 'DELETE' }
  )

  return tratarResposta(resposta)
}

export async function limparCarrinho() {
  const sessionId = obterSessionId()

  const resposta = await fetch(
    `${API_CARRINHO}/${encodeURIComponent(sessionId)}`,
    { method: 'DELETE' }
  )

  return tratarResposta(resposta)
}

export async function exportarSimulado(formato) {
  if (!['pdf', 'json'].includes(formato)) {
    throw new Error('Formato de exportação inválido.')
  }

  const sessionId = obterSessionId()

  const resposta = await fetchAutenticado(
    `${API_SIMULADOS}/exportar/${formato}/${encodeURIComponent(sessionId)}`
  )

  if (!resposta.ok) {
    let mensagem = 'Erro ao exportar o simulado.'

    try {
      const dados = await resposta.json()
      mensagem = dados.detail || mensagem
    } catch {
      // Mantém a mensagem padrão.
    }

    throw new Error(mensagem)
  }

  const arquivo = await resposta.blob()
  const url = URL.createObjectURL(arquivo)
  const link = document.createElement('a')

  link.href = url
  link.download = `simulado_${sessionId}.${formato}`

  document.body.appendChild(link)
  link.click()
  link.remove()

  URL.revokeObjectURL(url)
}
