import { fetchAutenticado } from './authService'

export async function buscarQuestoes(filtros = {}) {
  const parametros = new URLSearchParams()

  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor !== undefined && valor !== null && valor !== '') {
      parametros.append(chave, valor)
    }
  })

  const resposta = await fetchAutenticado(
    `/api/v1/questoes/busca?${parametros.toString()}`,
    {},
    { tentarAnonimo: true }
  )

  if (!resposta.ok) {
    throw new Error('Não foi possível buscar as questões.')
  }

  return resposta.json()
}

export async function obterOpcoesFiltros() {
  const resposta = await fetchAutenticado(
    '/api/v1/questoes/filtros',
    {},
    { tentarAnonimo: true }
  )

  if (!resposta.ok) {
    throw new Error('Não foi possível carregar as opções de filtro.')
  }

  return resposta.json()
}

export async function obterEstatisticas() {
  const resposta = await fetchAutenticado('/api/v1/questoes/agregacoes/estatisticas')

  if (resposta.status === 403) {
    throw new Error('Acesso negado: esta área é restrita ao perfil Professor.')
  }

  if (!resposta.ok) {
    throw new Error('Não foi possível carregar as estatísticas.')
  }

  return resposta.json()
}

export async function buscarQuestaoPorId(id) {
  const resposta = await fetchAutenticado(
    `/api/v1/questoes/${encodeURIComponent(id)}`,
    {},
    { tentarAnonimo: true }
  )

  if (!resposta.ok) {
    if (resposta.status === 404) {
      throw new Error('Questão não encontrada.')
    }

    throw new Error('Não foi possível carregar a questão.')
  }

  return resposta.json()
}
