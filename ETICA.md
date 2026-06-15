# Ética e Reflexão Crítica — Glicuidado

> *"Um modelo de IA em saúde que ignora seus vieses pode prejudicar exatamente as
> populações que pretende ajudar."* — Enunciado do A3

Este documento atende ao critério **Reflexão Ética e Senso Crítico** da rubrica do A3.
Analisa os vieses, riscos e limitações do modelo de predição de risco de diabetes do
Glicuidado e propõe **ações concretas de mitigação**.

---

## 1. Vieses no dataset

O modelo foi treinado com o **Pima Indians Diabetes Database** (UCI/Kaggle), que possui
limitações de representatividade importantes:

| Viés | Descrição | Impacto |
|---|---|---|
| **População restrita** | Todos os registros são de mulheres de etnia Pima (indígenas dos EUA), com **idade ≥ 21 anos**. | O modelo **não representa** homens, crianças, adolescentes nem outras etnias. Aplicá-lo à população brasileira geral é uma extrapolação indevida. |
| **Tamanho pequeno** | Apenas 768 registros. | Subgrupos (ex.: idosas, faixas de IMC extremas) ficam sub-representados, aumentando a incerteza nesses casos. |
| **Dados ausentes mascarados** | Glicemia, pressão, dobra cutânea, insulina e IMC tinham `0` representando valores ausentes (até 49% em insulina). | Imputação pela mediana reduz variância real e pode introduzir viés nas estimativas. |

## 2. Fairness (justiça entre grupos)

Como o dataset contém **apenas um grupo demográfico**, **não é possível auditar fairness**
entre gêneros ou etnias com estes dados. Isso é, em si, uma limitação ética: um sistema
de saúde deveria ter desempenho equivalente entre todos os grupos.

**Mitigação proposta:**
- Coletar/validar o modelo com dados brasileiros reais (ex.: **DATASUS / OpenDataSUS**)
  antes de qualquer uso real.
- Medir métricas (recall, precisão) **separadamente por subgrupo** (idade, sexo, região).
- Reportar abertamente os grupos para os quais o modelo **não** é validado.

## 3. Uso responsável

- O Glicuidado é uma **ferramenta de apoio à decisão**, que **nunca substitui** o
  profissional de saúde. A interface exibe explicitamente esse aviso na tela de predição.
- A decisão clínica final é **sempre humana**. O modelo fornece uma estimativa de
  probabilidade, não um diagnóstico.
- **Risco de falsos negativos:** no contexto clínico, deixar de sinalizar um paciente em
  risco (falso negativo) costuma ser mais grave do que um falso alarme. Por isso
  acompanhamos o **recall** da classe positiva, e não apenas a acurácia.

## 4. Transparência e explicabilidade

- O modelo escolhido (Regressão Logística / melhor por ROC-AUC) é **interpretável**.
- Calculamos **importância das features por permutação** (`reports/figures/importancia_features.png`),
  e a tela de predição mostra ao usuário **quais fatores mais pesam** na decisão.
- Evolução futura: incorporar **SHAP values** para explicar predições **individuais**
  (por que *este* paciente foi classificado como de risco).
- O paciente tem o **direito de entender** como foi classificado.

## 5. Limitações técnicas reconhecidas

- Desempenho moderado (ROC-AUC ≈ 0.81): **adequado para triagem**, não para diagnóstico.
- Não há dados longitudinais (evolução do paciente ao longo do tempo).
- O modelo não considera fatores socioeconômicos, alimentação ou genética detalhada.

## 6. Resumo das ações de mitigação

1. Validar com **dados brasileiros (DATASUS)** antes de uso real.
2. Auditar **métricas por subgrupo** demográfico.
3. Priorizar **recall** para reduzir falsos negativos clínicos.
4. Manter o **aviso de apoio à decisão** visível na interface.
5. Evoluir a explicabilidade com **SHAP** por predição individual.
6. Documentar claramente **para quem o modelo NÃO é validado**.
