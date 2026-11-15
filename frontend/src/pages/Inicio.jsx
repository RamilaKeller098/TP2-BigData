
function Inicio() {
  return (
    <>
      <section className="hero-section" id="inicio">
        <div className="hero-content">
          <span className="eyebrow">
            PLATAFORMA DE ESTUDOS ENADE
          </span>

          <h1>
            Seu próximo desafio começa com
            <span> conhecimento.</span>
          </h1>

          <p>
            Explore o acervo histórico de provas do ENADE,
            encontre questões e prepare seus simulados
            em um só lugar.
          </p>

          <a href="/buscar" className="primary-button">
            Explorar questões <span>→</span>
          </a>
        </div>

        <div className="hero-card">
          <div className="hero-card-icon">📚</div>
          <h2>Conhecimento organizado.</h2>
          <p>
            Questões acadêmicas reunidas para facilitar
            sua preparação.
          </p>

          <div className="hero-card-footer">
            <span>ENADE HUB</span>
            <span>Aprenda. Pratique. Evolua.</span>
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="feature">
          <span>01</span>
          <h3>Busca inteligente</h3>
          <p>Localize questões por palavras-chave e filtros.</p>
        </div>

        <div className="feature">
          <span>02</span>
          <h3>Acervo histórico</h3>
          <p>Acesse questões de provas anteriores do ENADE.</p>
        </div>

        <div className="feature">
          <span>03</span>
          <h3>Monte simulados</h3>
          <p>Organize questões para praticar seus conhecimentos.</p>
        </div>
      </section>
    </>
  )
}

export default Inicio
