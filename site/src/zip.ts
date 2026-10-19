const CRC_TABLE = new Uint32Array(256)
for (let n = 0; n < 256; n++) {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  CRC_TABLE[n] = c >>> 0
}

function crc32(dados: Uint8Array): number {
  let crc = 0xffffffff
  for (let i = 0; i < dados.length; i++) {
    crc = CRC_TABLE[(crc ^ dados[i]) & 0xff] ^ (crc >>> 8)
  }
  return (crc ^ 0xffffffff) >>> 0
}

function u16(n: number) {
  return [n & 0xff, (n >>> 8) & 0xff]
}

function u32(n: number) {
  return [n & 0xff, (n >>> 8) & 0xff, (n >>> 16) & 0xff, (n >>> 24) & 0xff]
}

function juntar(partes: Uint8Array[]) {
  const total = partes.reduce((soma, parte) => soma + parte.length, 0)
  const saida = new Uint8Array(total)
  let offset = 0
  for (const parte of partes) {
    saida.set(parte, offset)
    offset += parte.length
  }
  return saida
}

export function zipStore(entradas: { nome: string; dados: Uint8Array }[]) {
  const agora = new Date()
  const hora = (agora.getHours() << 11) | (agora.getMinutes() << 5) | Math.floor(agora.getSeconds() / 2)
  const dia = ((agora.getFullYear() - 1980) << 9) | ((agora.getMonth() + 1) << 5) | agora.getDate()
  const locais: Uint8Array[] = []
  const centrais: Uint8Array[] = []
  let offset = 0

  for (const entrada of entradas) {
    const nome = new TextEncoder().encode(entrada.nome)
    const crc = crc32(entrada.dados)
    const tamanho = entrada.dados.length
    const local = juntar([
      new Uint8Array([
        ...u32(0x04034b50),
        ...u16(20),
        ...u16(0),
        ...u16(0),
        ...u16(hora),
        ...u16(dia),
        ...u32(crc),
        ...u32(tamanho),
        ...u32(tamanho),
        ...u16(nome.length),
        ...u16(0),
      ]),
      nome,
      entrada.dados,
    ])
    const central = juntar([
      new Uint8Array([
        ...u32(0x02014b50),
        ...u16(20),
        ...u16(20),
        ...u16(0),
        ...u16(0),
        ...u16(hora),
        ...u16(dia),
        ...u32(crc),
        ...u32(tamanho),
        ...u32(tamanho),
        ...u16(nome.length),
        ...u16(0),
        ...u16(0),
        ...u16(0),
        ...u16(0),
        ...u32(0),
        ...u32(offset),
      ]),
      nome,
    ])
    locais.push(local)
    centrais.push(central)
    offset += local.length
  }

  const diretorio = juntar(centrais)
  const fim = new Uint8Array([
    ...u32(0x06054b50),
    ...u16(0),
    ...u16(0),
    ...u16(entradas.length),
    ...u16(entradas.length),
    ...u32(diretorio.length),
    ...u32(offset),
    ...u16(0),
  ])
  return juntar([...locais, diretorio, fim])
}
