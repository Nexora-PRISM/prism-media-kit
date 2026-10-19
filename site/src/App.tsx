import { useEffect, useMemo, useState } from 'react'
import { zipStore } from './zip'

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

function nomeDe(arquivo: string) {
  return arquivo.split('/').pop() ?? 'peca.png'
}

function salvar(blob: Blob, nome: string) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = nome
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}

async function baixar(url: string, nome: string) {
  const resposta = await fetch(url)
  if (!resposta.ok) throw new Error('download')
  salvar(await resposta.blob(), nome)
}

async function baixarZip(arquivos: { url: string; nome: string }[], nome: string) {
  const entradas = []
  for (const arquivo of arquivos) {
    const resposta = await fetch(arquivo.url)
    if (!resposta.ok) throw new Error('download')
    entradas.push({ nome: arquivo.nome, dados: new Uint8Array(await resposta.arrayBuffer()) })
  }
  const zip = zipStore(entradas)
  salvar(new Blob([zip.buffer as ArrayBuffer], { type: 'application/zip' }), nome)
}

function arquivosDaPeca(peca: Peca) {
  const nome = nomeDe(peca.arquivo)
  const png = srcOf(peca.arquivo)
  const lista = [{ url: png, nome }]
  if (peca.formato.includes('jpg')) {
    lista.push({ url: png.replace(/\.png$/, '.jpg'), nome: nome.replace(/\.png$/, '.jpg') })
  }
  return lista
}

export default function App() {
  const [pecas, setPecas] = useState<Peca[] | null>(null)
  const [erro, setErro] = useState('')
  const [aberta, setAberta] = useState<Peca | null>(null)
  const [baixando, setBaixando] = useState<string | null>(null)
  const [aviso, setAviso] = useState('')

  async function executar(chave: string, acao: () => Promise<void>) {
    if (baixando) return
    setBaixando(chave)
    setAviso('')
    try {
      await acao()
    } catch {
      setAviso('Não foi possível baixar. Tente de novo.')
    } finally {
      setBaixando(null)
    }
  }

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
        <div className="section-head">
          <h2>Logo sem fundo</h2>
          <button
            className="button quiet"
            type="button"
            disabled={baixando === 'secao:sem-fundo'}
            onClick={() => executar('secao:sem-fundo', () => baixarZip(
              LOGO_SEM_FUNDO.map((logo) => ({ url: srcOf(logo.arquivo), nome: nomeDe(logo.arquivo) })),
              'sem-fundo.zip',
            ))}
          >
            {baixando === 'secao:sem-fundo' ? 'Baixando…' : 'Baixar seção'}
          </button>
        </div>
        <p className="lede">
          PNG com fundo transparente, para colocar no site por cima de qualquer cor.
          O arquivo principal é a logo horizontal.
        </p>
        <div className="grid">
          {LOGO_SEM_FUNDO.map((logo) => {
            const nome = nomeDe(logo.arquivo)
            const chave = `arquivo:${logo.arquivo}`
            return (
              <article className="card" key={logo.arquivo}>
                <div className="frame">
                  <div className="preview checker">
                    <img src={srcOf(logo.arquivo)} alt={logo.nome} />
                  </div>
                  <button
                    className="baixar"
                    type="button"
                    disabled={baixando === chave}
                    onClick={() => executar(chave, () => baixar(srcOf(logo.arquivo), nome))}
                  >
                    {baixando === chave ? 'Baixando…' : 'Baixar'}
                  </button>
                </div>
                <div className="meta">
                  <h3>{logo.nome}</h3>
                  <p>{logo.nota}</p>
                </div>
              </article>
            )
          })}
        </div>
      </section>

      {erro && <p className="status">{erro}</p>}
      {aviso && <p className="status">{aviso}</p>}
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
          <div className="section-head">
            <h2>{grupo.titulo}</h2>
            <button
              className="button quiet"
              type="button"
              disabled={baixando === `secao:${grupo.id}`}
              onClick={() => executar(`secao:${grupo.id}`, () => baixarZip(
                grupo.itens.flatMap(arquivosDaPeca),
                `${grupo.id}.zip`,
              ))}
            >
              {baixando === `secao:${grupo.id}` ? 'Baixando…' : 'Baixar seção'}
            </button>
          </div>
          <div className="grid">
            {grupo.itens.map((peca) => {
              const png = srcOf(peca.arquivo)
              const nome = nomeDe(peca.arquivo)
              const jpg = peca.formato.includes('jpg') ? png.replace(/\.png$/, '.jpg') : null
              const chave = `arquivo:${peca.arquivo}`
              return (
                <article className="card" key={peca.arquivo}>
                  <div className="frame">
                    <button className="preview" type="button" onClick={() => setAberta(peca)}>
                      <img src={png} alt="" />
                    </button>
                    <button
                      className="baixar"
                      type="button"
                      disabled={baixando === chave}
                      onClick={() => executar(chave, () => baixar(png, nome))}
                    >
                      {baixando === chave ? 'Baixando…' : 'Baixar'}
                    </button>
                  </div>
                  <div className="meta">
                    <h3>{nome}</h3>
                    <div className="size">{peca.largura} × {peca.altura}</div>
                    <p>{peca.uso}</p>
                    {jpg && (
                      <div className="links">
                        <button type="button" onClick={() => executar(`jpg:${peca.arquivo}`, () => baixar(jpg, nome.replace(/\.png$/, '.jpg')))}>
                          {baixando === `jpg:${peca.arquivo}` ? 'Baixando…' : 'JPG'}
                        </button>
                      </div>
                    )}
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
              <span>{nomeDe(aberta.arquivo)} · {aberta.largura} × {aberta.altura}</span>
              <button
                className="baixar"
                type="button"
                disabled={baixando === `arquivo:${aberta.arquivo}`}
                onClick={() => executar(`arquivo:${aberta.arquivo}`, () => baixar(srcOf(aberta.arquivo), nomeDe(aberta.arquivo)))}
              >
                {baixando === `arquivo:${aberta.arquivo}` ? 'Baixando…' : 'Baixar'}
              </button>
            </figcaption>
          </figure>
        </div>
      )}
    </main>
  )
}
