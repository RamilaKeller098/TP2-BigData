
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { buscarQuestaoPorId } from '../services/questoesService'
import { adicionarQuestao } from '../services/carrinhoService'

function DetalhesQuestao() {
  const { id } = useParams()

  const [questao, setQuestao] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [adicionando, setAdicionando] = useState(false)
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')

  useEffect(() => {
    async function carregarQuestao() {
      try {
        setCarregando(true)
        setErro('')

        const dados = await buscarQuestaoPorId(id)
        setQuestao(dados)
      } catch (error) {
        setErro(error.message)
      } finally {
        setCarregando(false)
      }
    }

    carregarQuestao()
  }, [id])

  async function adicionarAoSimulado() {
    try {
      setAdicionando(true)
      setErro('')
      setMensagem('')

      await adicionarQuestao(questao.id)

      setMensagem('Questão adicionada ao seu simulado!')
    } catch (error) {
      setErro(error.message)
    } finally {
      setAdicionando(false)
    }
  }

  if (carregando) {
    return (
      <main className="page-container">
        <p>Carregando questão...</p>
      </main>
    )
  }

  if (erro && !questao) {
    return (
      <main className="page-container">
        <h1>Não foi possível abrir a questão</h1>
        <p>{erro}</p>
        <Link to="/buscar">Voltar para a busca</Link>
      </main>
    )
  }

  if (!questao) return null

  const numero = questao.numero ?? questao.numero_discursiva

  return (
    <main className="page-container">
      <Link to="/buscar" className="back-link">
        ← Voltar para a busca
      </Link>

      <section className="question-detail">
        <div className="question-header">
          <span className="eyebrow">ACERVO ENADE</span>
          <h1>Questão {numero || '—'}</h1>

          <div className="question-metadata">
            <span>{questao.ano}</span>
            <span>{questao.curso}</span>
            <span>{questao.tipo_questao}</span>
            <span>Seção {questao.secao}</span>
          </div>
        </div>

        {mensagem && (
          <p className="feedback-success">{mensagem}</p>
        )}

        {erro && (
          <p className="feedback-error" role="alert">{erro}</p>
        )}

        <div className="question-actions detail-actions">
          <button
            type="button"
            onClick={adicionarAoSimulado}
            disabled={adicionando}
          >
            {adicionando ? 'Adicionando...' : '+ Adicionar ao meu simulado'}
          </button>

          <Link to="/simulado" className="view-question">
            Meu simulado →
          </Link>
        </div>

        <div className="question-content">
          <h2>Enunciado</h2>
          <p className="question-text">
            {questao.enunciado || questao.texto_completo}
          </p>
        </div>

        {questao.alternativas?.length > 0 && (
          <div className="question-content">
            <h2>Alternativas</h2>

            <div className="alternatives-list">
              {questao.alternativas.map((alternativa, indice) => (
                <div className="alternative-item" key={indice}>
                  {typeof alternativa === 'string'
                    ? alternativa
                    : (
                      <>
                        <strong>
                          {alternativa.letra || alternativa.alternativa || `${indice + 1}.`}
                        </strong>
                        {' '}
                        {alternativa.texto || alternativa.conteudo}
                      </>
                    )}
                </div>
              ))}
            </div>
          </div>
        )}

        {questao.gabarito != null && (
          <div className="answer-section">
            <h2>Gabarito</h2>
            <p>{String(questao.gabarito)}</p>
          </div>
        )}

        <div className="question-footer">
          <p><strong>Área:</strong> {questao.area || 'Não informada'}</p>
          <p><strong>Origem:</strong> {questao.pdf_origem || 'Não informada'}</p>
          <p><strong>Página:</strong> {questao.pagina_inicio || 'Não informada'}</p>
        </div>
      </section>
    </main>
  )
}

export default DetalhesQuestao
