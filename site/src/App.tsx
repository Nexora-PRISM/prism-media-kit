import { useEffect, useMemo, useState } from 'react'

type Peca = {
  grupo: string
  titulo: string
  arquivo: string
  largura: number
  altura: number
  uso: string
  formato: string
}

const ORDEM = ['marca', 'avatares', 'linkedin', 'instagram', 'outras-redes', 'web']

const LOGO_SEM_FUNDO = [
  {
    arquivo: 'marca/sem-fundo/assinatura-horizontal-1200.png',
    nome: 'Logo horizontal',
    nota: 'Prisma e nome, sem fundo. É a peça para o cabeçalho do site.',
  },
  {
    arquivo: 'marca/sem-fundo/assinatura-vertical-800.png',
    nome: 'Logo vertical',
    nota: 'A mesma marca empilhada, para espaços altos.',
  },
  {
    arquivo: 'marca/sem-fundo/prisma-512.png',
    nome: 'Só o prisma',
    nota: 'Ícone sem texto, fundo transparente.',
  },
  {
    arquivo: 'marca/sem-fundo/wordmark-800.png',
    nome: 'Só o nome',
    nota: 'Lettering NEXORA PRISM, sem o prisma.',
  },
]

function srcOf(arquivo: string) {
  return `/kit/${arquivo}`
}

async function baixar(url: string, nome: string) {
  const resposta = await fetch(url)
  if (!resposta.ok) throw new Error('download')
  const blob = await resposta.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = nome
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}

export default function App() {
  const [pecas, setPecas] = useState<Peca[] | null>(null)
  const [erro, setErro] = useState('')
  const [aberta, setAberta] = useState<Peca | null>(null)

  useEffect(() => {
    let ativo = true
    fetch('/kit/manifesto.json')
      .then((resposta) => {
        if (!resposta.ok) throw new Error('manifesto')
        return resposta.json() as Promise<Peca[]>
      })
      .then((dados) => {
        if (ativo) setPecas(dados)
      })
      .catch(() => {
        if (ativo) setErro('Não foi possível carregar as peças. Confira se a pasta divulgacao está no ar.')
      })
    return () => {
      ativo = false
    }
  }, [])

  useEffect(() => {
    if (!aberta) return
    const fechar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') setAberta(null)
    }
    window.addEventListener('keydown', fechar)
    return () => window.removeEventListener('keydown', fechar)
  }, [aberta])

  const grupos = useMemo(() => {
    if (!pecas) return []
    return ORDEM.map((id) => {
      const itens = pecas.filter((peca) => peca.grupo === id)
      return { id, titulo: itens[0]?.titulo ?? id, itens }
    }).filter((grupo) => grupo.itens.length > 0)
  }, [pecas])

  return (
    <main className="app">
      <header className="hero">
        <img className="mark" src="/kit/marca/assinatura-horizontal.png" alt="Nexora Prism" />
        <p className="lede">
          Peças prontas para publicar. A logo definitiva foi mantida: o prisma e o lettering
          metálico são os originais, recolocados no tamanho de cada rede.
        </p>
        <ul className="contacts">
          <li><span>Site</span><a href="https://nexoraprism.com.br">nexoraprism.com.br</a></li>
          <li><span>Instagram</span><a href="https://instagram.com/nexoraprism_">@nexoraprism_</a></li>
          <li><span>E-mail</span><a href="mailto:contato@nexoraprism.com.br">contato@nexoraprism.com.br</a></li>
        </ul>
        <div className="actions">
          <a className="button" href="/baixar/logo-sem-fundo.zip">Baixar logos sem fundo</a>
          <button className="button quiet" type="button" onClick={() => baixar('/kit/logo-sem-fundo.zip', 'logo-sem-fundo.zip')}>
            Se o link não baixar, clique aqui
          </button>
        </div>
      </header>

      <section className="section" id="sem-fundo">
        <h2>Logo sem fundo</h2>
        <p className="lede">
          PNG com fundo transparente, para colocar no site por cima de qualquer cor.
          O arquivo principal é a logo horizontal.
        </p>
        <div className="grid">
          {LOGO_SEM_FUNDO.map((logo) => {
            const nome = logo.arquivo.split('/').pop() ?? 'logo.png'
            return (
              <article className="card" key={logo.arquivo}>
                <div className="preview checker">
                  <img src={srcOf(logo.arquivo)} alt={logo.nome} />
                </div>
                <div className="meta">
                  <h3>{logo.nome}</h3>
                  <p>{logo.nota}</p>
                  <div className="links">
                    <a href={`/baixar/${nome}`}>Baixar PNG</a>
                    <button type="button" onClick={() => baixar(srcOf(logo.arquivo), nome)}>Baixar de novo</button>
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      </section>

      {erro && <p className="status">{erro}</p>}
      {!pecas && !erro && <p className="status">Carregando as peças…</p>}
      {pecas && pecas.length === 0 && <p className="status">Nenhuma peça encontrada.</p>}

      {grupos.length > 0 && (
        <nav className="nav" aria-label="Seções do kit">
          {grupos.map((grupo) => (
            <a key={grupo.id} href={`#${grupo.id}`}>{grupo.titulo}</a>
          ))}
        </nav>
      )}

      {grupos.map((grupo) => (
        <section className="section" id={grupo.id} key={grupo.id}>
          <h2>{grupo.titulo}</h2>
          <div className="grid">
            {grupo.itens.map((peca) => {
              const png = srcOf(peca.arquivo)
              const jpg = peca.formato.includes('jpg') ? png.replace(/\.png$/, '.jpg') : null
              return (
                <article className="card" key={peca.arquivo}>
                  <button className="preview" type="button" onClick={() => setAberta(peca)}>
                    <img src={png} alt="" />
                  </button>
                  <div className="meta">
                    <h3>{peca.arquivo.split('/').pop()}</h3>
                    <div className="size">{peca.largura} × {peca.altura}</div>
                    <p>{peca.uso}</p>
                    <div className="links">
                      <a href={png} download>PNG</a>
                      {jpg && <a href={jpg} download>JPG</a>}
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        </section>
      ))}

      {aberta && (
        <div className="overlay" role="dialog" aria-modal="true" aria-label={aberta.arquivo} onClick={() => setAberta(null)}>
          <button className="close" type="button" onClick={() => setAberta(null)}>Fechar</button>
          <figure onClick={(evento) => evento.stopPropagation()}>
            <img src={srcOf(aberta.arquivo)} alt={aberta.uso} />
            <figcaption>
              {aberta.arquivo.split('/').pop()} · {aberta.largura} × {aberta.altura}
            </figcaption>
          </figure>
        </div>
      )}
    </main>
  )
}
