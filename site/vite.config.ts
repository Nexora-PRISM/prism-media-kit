import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

function forcarDownload(): Plugin {
  return {
    name: 'forcar-download',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split('?')[0] ?? ''
        if (!url.startsWith('/baixar/')) return next()
        const nome = path.basename(url)
        const candidatos = [
          path.resolve('/workspace/divulgacao/marca/sem-fundo', nome),
          path.resolve('/workspace/divulgacao', nome),
          path.resolve('/workspace/site/public', nome),
        ]
        const arquivo = candidatos.find((candidato) => fs.existsSync(candidato))
        if (!arquivo) return next()
        const tipo = nome.endsWith('.zip') ? 'application/zip' : 'image/png'
        res.setHeader('Content-Type', tipo)
        res.setHeader('Content-Disposition', `attachment; filename="${nome}"`)
        res.setHeader('Content-Length', String(fs.statSync(arquivo).size))
        fs.createReadStream(arquivo).pipe(res)
      })
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
