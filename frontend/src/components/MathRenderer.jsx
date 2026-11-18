import React from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'


export default function MathRenderer({ text, className = '' }) {
  if (!text) return null

  const regex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)/g
  const partes = text.split(regex)

  return (
    <span className={`math-renderer ${className}`}>
      {partes.map((parte, index) => {
        if (!parte) return null

        if (parte.startsWith('$$') && parte.endsWith('$$')) {
          const formula = parte.slice(2, -2).trim()
          try {
            const html = katex.renderToString(formula, {
              displayMode: true,
              throwOnError: false,
            })
            return (
              <span
                key={index}
                className="math-block"
                dangerouslySetInnerHTML={{ __html: html }}
              />
            )
          } catch {
            return <code key={index}>{parte}</code>
          }
        }

        if (parte.startsWith('$') && parte.endsWith('$')) {
          const formula = parte.slice(1, -1).trim()
          try {
            const html = katex.renderToString(formula, {
              displayMode: false,
              throwOnError: false,
            })
            return (
              <span
                key={index}
                className="math-inline"
                dangerouslySetInnerHTML={{ __html: html }}
              />
            )
          } catch {
            return <code key={index}>{parte}</code>
          }
        }

        if (parte.includes('<mark>')) {
          const formatado = parte.replace(/\n/g, '<br />')
          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: formatado }}
            />
          )
        }

        // texto padrão
        return (
          <span key={index} style={{ whiteSpace: 'pre-line' }}>
            {parte}
          </span>
        )
      })}
    </span>
  )
}

