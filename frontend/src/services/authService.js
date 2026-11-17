import { useMemo, useSyncExternalStore } from 'react'

const CHAVE_SESSAO = 'enade-hub-auth'
const EVENTO = 'enade-hub-auth-changed'

// Se o navegador bloquear o sessionStorage, a sessão fica só em memória.
let memoria = null

function lerBruto() {
  try {
    return sessionStorage.getItem(CHAVE_SESSAO)
  } catch {
    return memoria
  }
}

function interpretar(bruto) {
  if (!bruto) return null

  try {
    const dados = JSON.parse(bruto)
    if (!dados.token || Date.now() >= dados.expiraEm) return null
    return dados
  } catch {
    return null
  }
}

function salvar(dados) {
  memoria = dados ? JSON.stringify(dados) : null

  try {
    if (memoria) sessionStorage.setItem(CHAVE_SESSAO, memoria)
    else sessionStorage.removeItem(CHAVE_SESSAO)
  } catch {
    // Mantém apenas em memória.
  }

  window.dispatchEvent(new Event(EVENTO))
}

export function obterToken() {
  return interpretar(lerBruto())?.token ?? null
}

export function cabecalhoAuth() {
  const token = obterToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function entrar(usuario, senha) {
  const resposta = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario, senha }),
  })

  if (!resposta.ok) {
    let mensagem = 'Não foi possível entrar. Tente novamente.'

    try {
      const dados = await resposta.json()
      if (typeof dados.detail === 'string') mensagem = dados.detail
    } catch {
      // Mantém a mensagem padrão.
    }

    throw new Error(mensagem)
  }

  const dados = await resposta.json()

  salvar({
    token: dados.access_token,
    usuario: dados.usuario,
    perfil: dados.perfil,
    expiraEm: Date.now() + dados.expira_em_segundos * 1000,
  })

  return dados
}

export function sair() {
  salvar(null)
}

/**
 * fetch que envia o token (se houver). Se a API responder 401:
 * - tentarAnonimo: limpa a sessão e repete a chamada sem token (rotas públicas);
 * - caso contrário, limpa a sessão e lança um erro para a tela exibir.
 */
export async function fetchAutenticado(url, opcoes = {}, { tentarAnonimo = false } = {}) {
  const tinhaToken = Boolean(obterToken())

  const resposta = await fetch(url, {
    ...opcoes,
    headers: { ...(opcoes.headers || {}), ...cabecalhoAuth() },
  })

  if (resposta.status !== 401) return resposta

  if (tinhaToken) sair()

  if (tentarAnonimo) return fetch(url, opcoes)

  throw new Error(
    tinhaToken
      ? 'Sua sessão expirou. Entre novamente.'
      : 'É necessário entrar para acessar este recurso.'
  )
}

function assinar(aoMudar) {
  window.addEventListener(EVENTO, aoMudar)
  window.addEventListener('storage', aoMudar)

  return () => {
    window.removeEventListener(EVENTO, aoMudar)
    window.removeEventListener('storage', aoMudar)
  }
}

export function useAuth() {
  const bruto = useSyncExternalStore(assinar, lerBruto, () => null)

  return useMemo(() => {
    const sessao = interpretar(bruto)

    return {
      logado: Boolean(sessao),
      usuario: sessao?.usuario ?? null,
      perfil: sessao?.perfil ?? 'Estudante',
      ehProfessor: sessao?.perfil === 'Professor',
    }
  }, [bruto])
}
