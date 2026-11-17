
import { Routes, Route, NavLink, Link } from 'react-router-dom'
import './App.css'

import Inicio from './pages/Inicio'
import Buscar from './pages/Buscar'
import DetalhesQuestao from './pages/DetalhesQuestao'
import MeuSimulado from './pages/MeuSimulado'
import Login from './pages/Login'
import { sair, useAuth } from './services/authService'

function App() {
  const { logado, usuario, perfil } = useAuth()

  return (
    <div className="app">
      <header className="header">
        <Link to="/" className="brand">
          <div className="brand-icon">E</div>
          <span>ENADE <strong>HUB</strong></span>
        </Link>

        <nav className="navigation">
          <NavLink to="/" end>Início</NavLink>
          <NavLink to="/buscar">Buscar questões</NavLink>
          <NavLink to="/simulado">Meu Simulado</NavLink>

          {logado ? (
            <div className="user-area">
              <span className="user-chip">{usuario} · {perfil}</span>
              <button type="button" className="logout-button" onClick={sair}>
                Sair
              </button>
            </div>
          ) : (
            <NavLink to="/login">Entrar</NavLink>
          )}
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/buscar" element={<Buscar />} />
        <Route path="/questoes/:id" element={<DetalhesQuestao />} />
        <Route path="/simulado" element={<MeuSimulado />} />
        <Route path="/login" element={<Login />} />
      </Routes>

      <footer className="footer">
        <strong>ENADE HUB</strong>
        <span>
          Plataforma distribuída de busca e indexação do ENADE.
        </span>
      </footer>
    </div>
  )
}

export default App
