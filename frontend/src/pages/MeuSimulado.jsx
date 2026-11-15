
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  buscarCarrinho,
  removerQuestao,
  limparCarrinho,
  exportarSimulado,
  PERFIL_ATUAL,
} from '../services/carrinhoService'

function MeuSimulado() {
  const [questoes, setQuestoes] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [operando, setOperando] = useState(false)
  const [erro, setErro] = useState('')
  const [mensagem, setMensagem] = useState('')

  const ehProfessor =
    PERFIL_ATUAL.trim().toLowerCase() === 'professor'

  async function carregarCarrinho() {
    try {
      setCarregando(true)
      setErro('')

      const dados = await buscarCarrinho()
      setQuestoes(dados.questoes || [])
    } catch (error) {
      setErro(error.message)
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarCarrinho()
  }, [])

  async function remover(id) {
    try {
      setOperando(true)
      setErro('')
      setMensagem('')

      await removerQuestao(id)
      setMensagem('Questão removida do simulado.')

      await carregarCarrinho()
    } catch (error) {
      setErro(error.message)
    } finally {
      setOperando(false)
    }
  }

  async function limpar() {
    if (!window.confirm('Deseja realmente remover todas as questões?')) {
      return
    }

    try {
      setOperando(true)
      setErro('')
      setMensagem('')

      await limparCarrinho()
      setQuestoes([])
      setMensagem('Simulado limpo com sucesso.')
    } catch (error) {
      setErro(error.message)
    } finally {
      setOperando(false)
    }
  }

  async function exportar(formato) {
    try {
      setOperando(true)
      setErro('')
      setMensagem('')

      await exportarSimulado(formato)
      setMensagem(`Arquivo ${formato.toUpperCase()} gerado com sucesso.`)
    } catch (error) {
      setErro(error.message)
    } finally {
      setOperando(false)
    }
  }

  if (carregando) {
    return (
      <main className="page-container">
        <p>Carregando seu simulado...</p>
      </main>
    )
  }

  return (
    <main className="page-container">
      <section className="page-heading">
        <span className="eyebrow">ÁREA DO ESTUDANTE</span>
        <h1>Meu Simulado</h1>
        <p>
          Organize as questões selecionadas e prepare seu simulado personalizado.
        </p>
      </section>

      <section className="simulado-summary">
        <div>
          <span className="summary-label">Questões selecionadas</span>
          <strong>{questoes.length}</strong>
        </div>

        <Link to="/buscar" className="simulado-add-link">
          + Adicionar questões
        </Link>
      </section>

      {mensagem && (
        <p className="feedback-success">{mensagem}</p>
      )}

      {erro && (
        <p className="feedback-error" role="alert">{erro}</p>
      )}

      {questoes.length === 0 ? (
        <section className="empty-simulado">
          <h2>Seu simulado está vazio</h2>
          <p>
            Explore o acervo ENADE e adicione questões para montar seu simulado.
          </p>
          <Link to="/buscar">Explorar questões</Link>
        </section>
      ) : (
        <>
          <section className="simulado-list">
            <div className="simulado-list-header">
              <h2>Questões do simulado</h2>

              <button
                type="button"
                className="button-danger"
                onClick={limpar}
                disabled={operando}
              >
                Limpar simulado
              </button>
            </div>

            {questoes.map((questao, indice) => (
              <article className="simulado-item" key={questao.id}>
                <div className="simulado-item-number">
                  {String(indice + 1).padStart(2, '0')}
                </div>

                <div className="simulado-item-content">
                  <strong>
                    {questao.curso} — {questao.ano}
                  </strong>

                  <p>
                    {questao.tipo_questao === 'discursiva'
                      ? 'Discursiva'
                      : 'Objetiva'}
                    {' · '}
                    Seção {questao.secao}
                  </p>

                  <Link
                    to={`/questoes/${encodeURIComponent(questao.id)}`}
                  >
                    Visualizar questão →
                  </Link>
                </div>

                <button
                  type="button"
                  className="button-remove"
                  onClick={() => remover(questao.id)}
                  disabled={operando}
                >
                  Remover
                </button>
              </article>
            ))}
          </section>

          <section className="export-section">
            <h2>Exportar simulado</h2>

            {ehProfessor ? (
              <>
                <p>Escolha o formato para gerar seu arquivo.</p>

                <div className="export-actions">
                  <button
                    type="button"
                    onClick={() => exportar('pdf')}
                    disabled={operando}
                  >
                    Exportar PDF
                  </button>

                  <button
                    type="button"
                    onClick={() => exportar('json')}
                    disabled={operando}
                  >
                    Exportar JSON
                  </button>
                </div>
              </>
            ) : (
              <p>
                A exportação de simulados está disponível exclusivamente
                para usuários com perfil de professor.
              </p>
            )}
          </section>
        </>
      )}
    </main>
  )
}

export default MeuSimulado
