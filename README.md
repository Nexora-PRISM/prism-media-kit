# Nexora Prism — kit de divulgação

Peças prontas para LinkedIn, Instagram, avatares e outras redes. O prisma e o lettering metálico são os da logo definitiva, recortados e recolocados. O site, o @ e o e-mail entram só como texto, para não deformar a marca.

- Site: nexoraprism.com.br
- Instagram: [@nexoraprism_](https://instagram.com/nexoraprism_)
- E-mail: contato@nexoraprism.com.br

A pasta `divulgacao/` é o material para publicar. Cada peça fotográfica sai em PNG e em JPG. Os arquivos da marca, com fundo transparente, saem só em PNG.

## Ver as peças

```bash
cd site
npm install
npm run dev
```

Abre em [http://127.0.0.1:4317](http://127.0.0.1:4317).

## O que tem na pasta

| Pasta | Uso |
| --- | --- |
| `divulgacao/marca` | Prisma, lettering e assinatura com fundo transparente, mais os originais |
| `divulgacao/avatares` | Só o prisma, com folga para o recorte circular |
| `divulgacao/linkedin` | Capas de perfil e de empresa, post e artigo |
| `divulgacao/instagram` | Feed quadrado, retrato e stories |
| `divulgacao/outras-redes` | Capas de X, Facebook e YouTube |
| `divulgacao/web` | Imagem de compartilhamento do site e faixa de assinatura de e-mail |

O guia de cada arquivo, com medida e onde publicar, está em `divulgacao/LEIA-ME.md`.

## Regenerar

```bash
python3 scripts/build_kit.py
```

Depende de Pillow, NumPy e SciPy. Os originais ficam em `assets/`.
