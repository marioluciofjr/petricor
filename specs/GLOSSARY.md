# GLOSSARY — termos do projeto

| Termo | Explicação simples |
|---|---|
| **Glifo** | O desenho de um caractere dentro da fonte. "a" e "a.hi" são dois glifos do mesmo caractere. |
| **UPM** (units per em) | A "régua" da fonte. Aqui são 1000 unidades por em. |
| **Linha de base** (baseline) | Linha invisível onde as letras "pousam" (y = 0). |
| **Altura-x** (x-height) | Altura das minúsculas sem haste, como x, o, a. |
| **Altura das maiúsculas** (cap height) | Altura de letras como H e E. |
| **Ascendente / descendente** | Partes que sobem (b, d, h) ou descem (g, p, q) da altura-x / linha de base. |
| **Esqueleto** | Linha central do traço, com 1 px de largura, sem espessura. |
| **Expansão do traço** | Dar espessura ao esqueleto, como se fosse uma caneta de ponta redonda. |
| **Monolinear** | Traço com a mesma espessura em toda a letra. |
| **Bézier** | Curva matemática definida por pontos de controle; é como as fontes desenham curvas. |
| **Master** | Desenho-base de um peso extremo ou intermediário (Thin, Regular, Black). |
| **Interpolação** | Cálculo dos pesos intermediários a partir dos masters. Exige a mesma estrutura de pontos. |
| **Fonte variável (VF)** | Um único arquivo que contém todos os pesos por meio de um eixo contínuo. |
| **Eixo `wght`** | Eixo de peso da VF, de 100 (Thin) a 900 (Black). |
| **Instância nomeada** | Ponto do eixo com nome (ex.: Bold = 700). |
| **UFO** | Formato aberto de arquivo-fonte (pastas com XML). |
| **Designspace** | Arquivo que descreve os masters, eixos e instâncias. |
| **OpenType feature** | Regras dentro da fonte que trocam ou posicionam glifos (ex.: `calt`, `kern`, `tnum`). |
| **`calt`** (contextual alternates) | Troca um glifo por uma variante conforme os vizinhos; é o que conecta a cursiva. |
| **Kerning** | Ajuste de espaço entre pares específicos (ex.: "AV"). |
| **Espaçamento lateral** (sidebearing) | Espaço em branco à esquerda e à direita de cada glifo. |
| **Âncora** | Ponto marcado no glifo onde um acento se encaixa (`top`, `bottom`). |
| **Composto** | Glifo montado com referências a outros (ex.: `ã` = `a` + `tildecomb`). |
| **GF Latin Core** | Lista mínima de glifos exigida pelo Google Fonts (cobre as línguas latinas ocidentais). |
| **Fontspector** | Verificador oficial de qualidade do Google Fonts (sucessor do Fontbakery). |
| **gftools builder** | Ferramenta do Google que compila a fonte a partir de `config.yaml`. |
| **OFL** | SIL Open Font License: licença livre exigida pelo Google Fonts. |
| **CLA** | Contributor License Agreement: acordo que o Google exige de quem contribui. |
| **Marcas de registro** | Quadrados pretos nos cantos da folha usados para alinhar a digitalização. |
| **Prova** | Imagem ou página de teste para revisar visualmente a fonte. |
| **Autointerseção** | Quando o contorno cruza a si mesmo; gera falhas no desenho. |
