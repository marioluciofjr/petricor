# DESIGN — como a Petricor deve parecer

## 1. Personalidade
Manuscrita, calorosa e legível. Maiúsculas **de forma** (bastão) e minúsculas **cursivas conectadas**, como na escrita do Mário. A harmonização é **leve**: corrige o que atrapalha a leitura e mantém a irregularidade que dá vida.

## 2. Métricas (UPM 1000; valores confirmados na Fase 2)
| Métrica | Alvo |
|---|---|
| Altura das maiúsculas | 700 |
| Altura-x | 450 |
| Ascendentes (b, d, h, k, l, f) | ~760 |
| Descendentes (g, j, p, q, y, f) | ~−260 |
| Altura de junção cursiva (baixa) | ~120 |
| Altura de junção cursiva (alta, `.hi`) | ~430 |
| Overshoot de curvas (O, o, S) | ±10 |

## 3. Pesos (monolinear: espessura do traço em unidades)
| Instância | wght | Traço (aprox.) |
|---|---|---|
| Thin | 100 | 18 |
| ExtraLight | 200 | 30 |
| Light | 300 | 46 |
| Regular | 400 | 64 |
| Medium | 500 | 82 |
| SemiBold | 600 | 102 |
| Bold | 700 | 124 |
| ExtraBold | 800 | 150 |
| Black | 900 | 180 |
Masters: Thin (100), Regular (400) e Black (900). Pontas e junções **redondas** (caneta esferográfica).

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
