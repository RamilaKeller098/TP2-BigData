
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { buscarQuestoes } from '../services/questoesService'
import { adicionarQuestao } from '../services/carrinhoService'
import MathRenderer from '../components/MathRenderer'

function Buscar() {
  const [filtros, setFiltros] = useState({
    q: '',
    ano: '',
    tipo_questao: '',
  })

  const [resultado, setResultado] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [adicionandoId, setAdicionandoId] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')

  async function carregarQuestoes(pagina = 1) {
    try {
      setCarregando(true)
      setErro('')
      setMensagem('')

      const dados = await buscarQuestoes({
        ...filtros,
        page: pagina,
        size: 10,
      })

      setResultado(dados)
    } catch (error) {
      setErro(error.message)
    } finally {
      setCarregando(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    carregarQuestoes(1)
  }

  function atualizarFiltro(event) {
    const { name, value } = event.target

    setFiltros((estadoAnterior) => ({
      ...estadoAnterior,
      [name]: value,
    }))
  }

  async function adicionarAoSimulado(questaoId) {
    try {
      setAdicionandoId(questaoId)
      setErro('')
      setMensagem('')

      await adicionarQuestao(questaoId)

      setMensagem('Questão adicionada ao seu simulado!')
    } catch (error) {
      setErro(error.message)
    } finally {
      setAdicionandoId(null)
    }
  }

  return (
    <main className="page-container">
      <section className="page-heading">
        <span className="eyebrow">ACERVO ENADE</span>
        <h1>Buscar questões</h1>
        <p>
          Encontre questões de provas anteriores e organize seus
          estudos por assunto, ano e tipo de questão.
        </p>
      </section>

      <form className="search-card" onSubmit={handleSubmit}>
        <label htmlFor="search">Palavra-chave ou assunto</label>

        <input
          id="search"
          type="search"
          name="q"
          value={filtros.q}
          onChange={atualizarFiltro}
          placeholder="Ex.: Engenharia de Computação, algoritmos..."
        />

        <div className="filters">
          <div>
            <label htmlFor="year">Ano</label>
            <select
              id="year"
              name="ano"
              value={filtros.ano}
              onChange={atualizarFiltro}
            >
              <option value="">Todos os anos</option>
              <option value="2023">2023</option>
            </select>
          </div>

          <div>
            <label htmlFor="type">Tipo de questão</label>
            <select
              id="type"
              name="tipo_questao"
              value={filtros.tipo_questao}
              onChange={atualizarFiltro}
            >
              <option value="">Todos os tipos</option>
              <option value="objetiva">Objetiva</option>
              <option value="discursiva">Discursiva</option>
            </select>
          </div>

          <button type="submit" disabled={carregando}>
            {carregando ? 'Buscando...' : 'Buscar questões'}
          </button>
        </div>
      </form>

      {mensagem && <p className="feedback-success">{mensagem}</p>}
      {erro && <p className="feedback-error" role="alert">{erro}</p>}

      <section className="results-section">
        <h2>Resultados da pesquisa</h2>

        {carregando && <p>Carregando questões...</p>}

        {resultado && (
          <>
            <p>{resultado.total} questão(ões) encontrada(s).</p>

            {resultado.questoes.map((questao) => (
              <article className="search-card" key={questao.id}>
                <div>
                  <strong>
                    {questao.curso} — {questao.ano}
                  </strong>

                  <p>
                    {questao.tipo_questao === 'discursiva'
                      ? 'Questão discursiva'
                      : 'Questão objetiva'}
                    {' · '}
                    Seção {questao.secao}
                  </p>
                </div>

                <div className="question-excerpt">
                  <MathRenderer
                    text={
                      questao.highlights?.enunciado?.[0] ||
                      questao.highlights?.texto_completo?.[0] ||
                      questao.enunciado
                    }
                  />
                </div>

                <div className="question-actions">
                  <Link
                    to={`/questoes/${encodeURIComponent(questao.id)}`}
                    className="view-question"
                  >
                    Visualizar questão →
                  </Link>

                  <button
                    type="button"
                    disabled={adicionandoId === questao.id}
                    onClick={() => adicionarAoSimulado(questao.id)}
                  >
                    {adicionandoId === questao.id
                      ? 'Adicionando...'
                      : '+ Adicionar ao simulado'}
                  </button>
                </div>
              </article>
            ))}

            <div className="pagination">
              <button
                type="button"
                disabled={resultado.pagina_atual <= 1 || carregando}
                onClick={() => carregarQuestoes(resultado.pagina_atual - 1)}
              >
                Anterior
              </button>

              <span>
                Página {resultado.pagina_atual} de {resultado.total_paginas}
              </span>

              <button
                type="button"
                disabled={
                  resultado.pagina_atual >= resultado.total_paginas ||
                  carregando
                }
                onClick={() => carregarQuestoes(resultado.pagina_atual + 1)}
              >
                Próxima
              </button>
            </div>
          </>
        )}
      </section>
    </main>
  )
}

export default Buscar
