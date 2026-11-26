# PRD — Petricor

> **Porquê** do projeto. Versão 0.1 · 2026-11-25 · Dono: Mário

## 1. Problema
O Mário quer eternizar a própria caligrafia em uma fonte digital **pública e gratuita**, disponível para qualquer pessoa no Google Fonts. Hoje a letra existe só no papel, em duas folhas-modelo do fontmaker.co, com imperfeições naturais da escrita à mão: tamanhos, alinhamentos e espaçamentos irregulares.

## 2. Público
- Pessoas que criam peças gráficas, convites, posts, materiais educativos e interfaces e querem um toque manuscrito.
- Usuárias do Google Fonts (web, Google Docs/Slides, apps).
- O próprio Mário, como autor e mantenedor.

## 2.1 Duas famílias (decisão do Mário após a Prova 2, 2026-11-25)
| Família | Minúsculas | Uso principal |
|---|---|---|
| **Petricor** | De forma (não cursivas), derivadas do estilo do Mário (bojos do `O`, arcos do `n`, formas de `C`, `S`, `V`, `W`, `X`, `Z`, `K` reduzidas) | Blogs, textos corridos, interfaces |
| **Petricor Caligrafia** | Cursivas conectadas (entradas e saídas padronizadas + `calt`) | Títulos, convites, peças afetivas |
Maiúsculas, algarismos, pontuação e símbolos são compartilhados. As duas famílias têm 9 pesos e seguem juntas no mesmo repositório e na mesma issue do Google Fonts.

## 3. Objetivos e resultados esperados
| # | Objetivo | Critério de sucesso |
|---|---|---|
| O1 | Fonte fiel à letra do Mário | O Mário aprova as provas 1, 2 e 5 |
| O2 | Harmonização **leve** | Linha de base, altura-x e altura das maiúsculas uniformes (desvio ≤ 2% do UPM) |
| O3 | 9 pesos (Thin 100 → Black 900) | `Petricor[wght].ttf` e `PetricorCaligrafia[wght].ttf`, eixo `wght` 100–900 e 9 instâncias nomeadas |
| O4 | Minúsculas cursivas **conectadas** (Caligrafia) | Texto em português digitado sem quebras visíveis entre minúsculas (`calt`) |
| O4b | Minúsculas de forma (Petricor) | Legíveis em parágrafos de blog a 16–18 px |
| O5 | Cobertura **GF Latin Core** | 100% dos glifos da lista oficial |
| O6 | Pronta para o Google Fonts | Fontspector (perfil `googlefonts`) sem FAIL/FATAL; repositório público no padrão upstream; issue de submissão aberta |

## 4. Requisitos funcionais
- **RF01** Extrair automaticamente os caracteres das folhas digitalizadas.
- **RF02** Converter cada caractere em esqueleto vetorial (linha central) editável.
- **RF03** Harmonizar métricas e proporções (nível leve).
- **RF04** Gerar contornos monolineares para qualquer peso entre 100 e 900.
- **RF05** Conectar minúsculas cursivas por regras OpenType (`calt`).
- **RF06** Desenhar no estilo do Mário os acentos e sinais ausentes nas folhas e compor os acentuados.
- **RF07** Espaçamento e kerning coerentes.
- **RF08** Algarismos proporcionais por padrão e tabulares via `tnum`.
- **RF09** Build reprodutível em um comando (gftools builder).
- **RF10** Provas visuais (PNG/HTML) em cada fase.
- **RF11** Repositório público com estrutura upstream do Google Fonts e CI.
- **RF12** Abrir a issue "Add Petricor" no google/fonts (após confirmação).
- **RF13** Minúsculas de forma derivadas do estilo do Mário para a família Petricor.
- **RF14** Redesenhar `0`, `9` e `@` (tremidos na escrita original).
- **RF15** Build de duas famílias a partir das mesmas fontes (camadas de esqueleto compartilhadas).

## 5. Requisitos não funcionais
- **RNF01** Licença OFL 1.1 sem Reserved Font Name.
- **RNF02** Código Python em OOP, alta coesão e baixo acoplamento, com comentários didáticos em PT-BR.
- **RNF03** TDD: todo componente nasce com teste.
- **RNF04** Métricas verticais conforme o GF Guide (iguais em toda a família).
- **RNF05** Nome de família ASCII: `Petricor`.

## 6. Fora do escopo
- Itálico, versões condensadas, small caps, alfabetos não latinos (cirílico, grego, vietnamita).
- Hinting manual (a fonte variável vai sem hinting, como o Google recomenda).
- Versões estáticas para o Google Fonts (a API gera; elas ficam só no repositório).

## 7. Arquitetura e padrões (resumo; detalhes em ARCHITECTURE.md)
Pipeline em etapas (**Pipes and Filters**): folha → esqueleto → harmonização → contorno por peso → UFO/designspace → binários → QA.
Padrões: **Strategy** (pesos e expansão), **Repository** (`SkeletonStore`), **Builder** (`MasterBuilder`), **Facade** (`cli.py`), **Value Object** (`Metrics`, `Stroke`).

## 8. Riscos conhecidos
| Risco | Impacto | Mitigação |
|---|---|---|
| Autointerseção no Black em laços pequenos | Contorno quebrado | Ajuste do esqueleto + teste de validade por glifo |
| Cursiva conectada complexa | Retrabalho | Junção padronizada + variantes `.hi` + provas |
| Vetorização automática imperfeita | Glifos feios | Edição manual dos JSON + prova 1 |
| Google não aceitar / fila longa | Publicação atrasa | Cumprir 100% dos requisitos; fonte já fica pública no GitHub |
| Ferramentas sem wheel para Python 3.14 | Build falha | venv com Python 3.13 |
