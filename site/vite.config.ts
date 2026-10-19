import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function forcarDownload(): Plugin {
  const atender = (req: { url?: string }, res: { setHeader: (nome: string, valor: string) => void; statusCode?: number }, next: () => void) => {
    const url = req.url?.split('?')[0] ?? ''
    if (!url.startsWith('/baixar/')) return next()
    const nome = path.basename(url)
    const candidatos = [
      path.resolve(raiz, 'divulgacao/marca/sem-fundo', nome),
      path.resolve(raiz, 'divulgacao', nome),
      path.resolve(raiz, 'site/public', nome),
    ]
    const arquivo = candidatos.find((candidato) => fs.existsSync(candidato))
    if (!arquivo) return next()
    const tipo = nome.endsWith('.zip') ? 'application/zip' : 'image/png'
    res.setHeader('Content-Type', tipo)
    res.setHeader('Content-Disposition', `attachment; filename="${nome}"`)
    res.setHeader('Content-Length', String(fs.statSync(arquivo).size))
    fs.createReadStream(arquivo).pipe(res as unknown as NodeJS.WritableStream)
  }

  return {
    name: 'forcar-download',
    configureServer(server) {
      server.middlewares.use(atender)
    },
    configurePreviewServer(server) {
      server.middlewares.use(atender)
    },
    closeBundle() {
      const origem = path.resolve(raiz, 'divulgacao/logo-sem-fundo.zip')
      if (!fs.existsSync(origem)) return
      const destino = path.resolve(raiz, 'site/dist/baixar')
      fs.mkdirSync(destino, { recursive: true })
      fs.copyFileSync(origem, path.join(destino, 'logo-sem-fundo.zip'))
    },
  }
}

export default defineConfig({
  plugins: [forcarDownload(), react()],
  server: {
    host: '0.0.0.0',
    port: 4317,
    strictPort: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 4317,
    strictPort: true,
  },
})
