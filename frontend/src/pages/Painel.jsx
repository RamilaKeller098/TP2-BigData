import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../services/authService'
import { obterEstatisticas } from '../services/questoesService'

function Distribuicao({ titulo, itens }) {
  const maximo = Math.max(1, ...itens.map((item) => item.quantidade))

  return (
    <section className="panel-card">
      <h2>{titulo}</h2>

      {itens.length === 0 ? (
        <p className="panel-empty">Nenhum dado indexado ainda.</p>
      ) : (
        <ul className="bar-list">
          {itens.map((item) => (
            <li key={item.rotulo}>
              <span className="bar-label">{item.rotulo}</span>
              <span className="bar-track">
                <span
                  className="bar-fill"
                  style={{ width: `${(item.quantidade / maximo) * 100}%` }}
                />
              </span>
              <span className="bar-value">{item.quantidade}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

const ROTULO_TIPO = { objetiva: 'Objetiva', discursiva: 'Discursiva' }
const ROTULO_SECAO = { FG: 'Formação Geral (FG)', CE: 'Componente Específico (CE)' }

function Painel() {
  const { logado, ehProfessor, usuario } = useAuth()
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  useEffect(() => {
    if (!logado) return

    let ativo = true
    setCarregando(true)
    setErro('')

    obterEstatisticas()
      .then((resposta) => ativo && setDados(resposta))
      .catch((error) => ativo && setErro(error.message))
      .finally(() => ativo && setCarregando(false))

    return () => {
      ativo = false
    }
  }, [logado, usuario])

  if (!logado) {
    return (
      <main className="page-container">
        <section className="page-heading">
          <span className="eyebrow">ÁREA DO PROFESSOR</span>
          <h1>Painel analítico</h1>
          <p>
            É necessário entrar para ver esta área.{' '}
            <Link to="/login" state={{ de: '/painel' }}>Entre com sua conta</Link>.
          </p>
        </section>
      </main>
    )
  }

  const total = dados ? dados.por_curso.reduce((soma, item) => soma + item.quantidade, 0) : 0
  const competencias = dados
    ? dados.por_ano.flatMap((ano) => ano.competencias)
    : []

  return (
    <main className="page-container">
      <section className="page-heading">
        <span className="eyebrow">ÁREA DO PROFESSOR</span>
        <h1>Painel analítico</h1>
        <p>Distribuição das questões indexadas no acervo ENADE.</p>
      </section>

      {carregando && <p>Carregando estatísticas...</p>}

      {erro && (
        <p className="feedback-error" role="alert">
          {erro}
          {!ehProfessor && ' Seu perfil atual é Estudante.'}
        </p>
      )}

      {dados && (
        <>
          <section className="panel-kpis">
            <div className="panel-kpi">
              <span>Questões indexadas</span>
              <strong>{total}</strong>
            </div>
            <div className="panel-kpi">
              <span>Cursos</span>
              <strong>{dados.por_curso.length}</strong>
            </div>
            <div className="panel-kpi">
              <span>Áreas</span>
              <strong>{dados.por_area.length}</strong>
            </div>
            <div className="panel-kpi">
              <span>Anos</span>
              <strong>{dados.por_ano.length}</strong>
            </div>
          </section>

          <div className="panel-grid">
            <Distribuicao
              titulo="Questões por curso"
              itens={dados.por_curso.map((i) => ({ rotulo: i.curso, quantidade: i.quantidade }))}
            />
            <Distribuicao
              titulo="Questões por área"
              itens={dados.por_area.map((i) => ({ rotulo: i.area, quantidade: i.quantidade }))}
            />
            <Distribuicao
              titulo="Questões por ano"
              itens={dados.por_ano.map((i) => ({ rotulo: String(i.ano), quantidade: i.quantidade }))}
            />
            <Distribuicao
              titulo="Tipo de questão"
              itens={dados.por_tipo.map((i) => ({
                rotulo: ROTULO_TIPO[i.tipo] || i.tipo,
                quantidade: i.quantidade,
              }))}
            />
            <Distribuicao
              titulo="Seção da prova"
              itens={dados.por_secao.map((i) => ({
                rotulo: ROTULO_SECAO[i.secao] || i.secao,
                quantidade: i.quantidade,
              }))}
            />
            <Distribuicao
              titulo="Competências"
              itens={competencias.map((i) => ({ rotulo: i.competencia, quantidade: i.quantidade }))}
            />
          </div>

          <p className="panel-note">
            Dados calculados no Elasticsearch{dados.cache_hit ? ' (resposta do cache Redis)' : ''}.
          </p>
        </>
      )}
    </main>
  )
}

export default Painel
