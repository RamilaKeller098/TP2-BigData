import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { entrar, useAuth } from '../services/authService'

function Login() {
  const { logado } = useAuth()
  const location = useLocation()
  const destino = location.state?.de || '/'

  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (logado) {
    return <Navigate to={destino} replace />
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)

    try {
      await entrar(usuario.trim(), senha)
    } catch (error) {
      setErro(error.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="page-container">
      <section className="page-heading">
        <span className="eyebrow">ACESSO</span>
        <h1>Entrar</h1>
        <p>
          Entre com sua conta institucional. O seu perfil (estudante ou
          professor) define o que você pode acessar.
        </p>
      </section>

      <form className="login-card" onSubmit={enviar}>
        <label htmlFor="usuario">Usuário</label>
        <input
          id="usuario"
          name="usuario"
          type="text"
          autoComplete="username"
          value={usuario}
          onChange={(evento) => setUsuario(evento.target.value)}
          required
        />

        <label htmlFor="senha">Senha</label>
        <input
          id="senha"
          name="senha"
          type="password"
          autoComplete="current-password"
          value={senha}
          onChange={(evento) => setSenha(evento.target.value)}
          required
        />

        {erro && <p className="feedback-error" role="alert">{erro}</p>}

        <button type="submit" className="login-button" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </main>
  )
}

export default Login
