# DESIGN — como a Petricor deve parecer

## 1. Personalidade
Manuscrita, calorosa e legível. Maiúsculas **de forma** (bastão) e minúsculas **cursivas conectadas**, como na escrita do Mário. A harmonização é **leve**: corrige o que atrapalha a leitura e mantém a irregularidade que dá vida.

## 2. Métricas (UPM 1000; medidas na Fase 2, fonte: `design/metrics.py`)
Medido na escrita (linha central): maiúsculas 18→690 · altura-x ~370 (variando de 273 a 434) · ascendentes ~678 · descendentes ~−200 · algarismos com base em +76 · caneta ~20 un.

| Métrica (borda visual) | Alvo |
|---|---|
| Altura das maiúsculas | 700 |
| Altura-x | 430 (sobe ~16% para ganhar legibilidade) |
| Ascendentes (b, d, h, k, l, f) | 720 |
| Descendentes (g, j, p, q, y, f) | −230 |
| Altura do t | 600 |
| Algarismos | 680, assentados na base |
| Altura de junção cursiva (baixa) | ~120 |
| Altura de junção cursiva (alta, `.hi`) | ~430 |
| Overshoot de curvas (O, o, S) | ±10 |

## 3. Pesos (monolinear: espessura do traço em unidades)
| Instância | wght | Traço | Alargamento horizontal |
|---|---|---|---|
| Thin | 100 | 16 | 0% |
| ExtraLight | 200 | 28 | 1% |
| Light | 300 | 42 | 2% |
| Regular | 400 | 60 | 3% |
| Medium | 500 | 76 | 4,5% |
| SemiBold | 600 | 94 | 6% |
| Bold | 700 | 112 | 8% |
| ExtraBold | 800 | 131 | 10% |
| Black | 900 | 150 | 12% |
Masters: Thin (100), Regular (400) e Black (900). Pontas e junções **redondas** (caneta esferográfica). A caneta original do Mário tem ~20 un (próximo do ExtraLight). O Black foi limitado a 150 para que os laços do e, a e o não fechem com a altura-x de 430. Pontos (pingos, ponto final) usam caneta × 1,25 + 30.

**Compensação por zonas:** em cada peso, a linha central é empurrada para dentro em meia caneta (para cima na base e no fundo das descendentes, para baixo na altura-x, nas maiúsculas e nas ascendentes). Assim a borda do traço fica nas linhas-alvo em todos os pesos (`outline/weight_profile.py`).

## 4. Regras de harmonização (leve)
1. Linha de base, altura-x e altura das maiúsculas alinhadas aos alvos.
2. Inclinação média uniformizada (letras levemente inclinadas ficam com o mesmo ângulo médio).
3. Tremidos maiores que ~6 unidades são suavizados; ondulações menores ficam.
4. Traços duplicados (caneta que passou duas vezes) viram um só.
5. Laços pequenos demais para o Black são abertos ou alargados.

## 5. Cursiva conectada
- Toda minúscula entra pela esquerda e sai pela direita na **junção baixa**.
- Letras que terminam no alto (`o`, `v`, `w`, `b`, `r`) saem na **junção alta**; a letra seguinte usa a variante `.hi`.
- Primeira letra da palavra: mantém o traço de entrada (autenticidade). A remoção via `calt` só entra se a prova 3 mostrar ganho.
- Maiúsculas não se conectam.

## 6. Glifos desenhados no estilo do Mário
Acentos com o mesmo traço monolinear e a mesma inclinação. O til deriva do `~` escrito; o trema, dos pontos do `i`/`:`; o anel, do `°`. Aspas curvas derivam da vírgula.

## 7. Provas (o que o Mário revisa)
1. Original × vetorizado. 2. Alfabeto harmonizado (Regular). 3. Palavras conectadas em PT. 4. Pangramas PT/ES/FR/DE. 5. Cascata de 9 pesos.
Página `proofs/index.html` com controle deslizante de peso (100–900), boa legibilidade e contraste AA.
