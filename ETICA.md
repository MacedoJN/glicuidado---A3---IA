# Ética e Reflexão Crítica — Glicuidado

> *"Um modelo de IA em saúde que ignora seus vieses pode prejudicar exatamente as
> populações que pretende ajudar."* — Enunciado do A3

Este documento atende ao critério **Reflexão Ética e Senso Crítico** da rubrica do A3.
Analisa os vieses, riscos e limitações do modelo de predição de risco de diabetes do
Glicuidado e propõe **ações concretas de mitigação**.

O modelo é treinado com dados **reais brasileiros** da **Pesquisa Nacional de Saúde (PNS)
2019**, do IBGE em parceria com o Ministério da Saúde — uma amostra probabilística de
abrangência nacional.

---

## 1. Vieses no dataset

A PNS 2019 é representativa da população brasileira adulta, o que **reduz** os vieses de
representatividade da versão anterior (que usava o Pima — só mulheres de uma única etnia
indígena dos EUA). Ainda assim, restam limitações importantes:

| Viés / limitação | Descrição | Impacto |
|---|---|---|
| **Diagnóstico autorrelatado** | O alvo é "algum médico já lhe deu o diagnóstico de diabetes?". Quem tem diabetes **não diagnosticado** aparece como negativo. | Subestima o risco em populações com **menor acesso à saúde**, justamente as mais vulneráveis. |
| **Subamostra de antropometria** | Peso e altura **medidos** (para o IMC) existem só para uma subamostra (~6 mil adultos). | Reduz o tamanho efetivo e pode sub-representar subgrupos. |
| **Sem variáveis laboratoriais** | O modelo usa estilo de vida/perfil (idade, IMC, hipertensão, etc.), não glicemia/HbA1c. | Teto de desempenho menor (ROC-AUC ~0.76); é **triagem**, não diagnóstico. |
| **Desbalanceamento** | ~9% de casos positivos (reflete a prevalência real). | Sem tratamento, o modelo ignora a classe positiva; mitigado com `class_weight="balanced"`. |

## 2. Fairness (justiça entre grupos)

Diferentemente do Pima, a PNS **permite auditar fairness**, pois traz sexo, idade, cor/raça
e região. Decisões tomadas:

- **Cor/raça foi deliberadamente excluída** das variáveis preditoras, para o modelo não
  aprender a discriminar por etnia.
- **Mitigação proposta / próximos passos:**
  - Medir recall e precisão **por subgrupo** (sexo, faixa etária, região) e reportar
    diferenças de desempenho.
  - Reamostrar/reponderar caso algum subgrupo fique sistematicamente pior.

## 3. Uso responsável

- O Glicuidado é uma **ferramenta de apoio à decisão**, que **nunca substitui** o
  profissional de saúde. A interface exibe esse aviso na tela de predição.
- A decisão clínica final é **sempre humana**. O modelo fornece uma estimativa de
  probabilidade, não um diagnóstico.
- **Risco de falsos negativos:** deixar de sinalizar alguém em risco é mais grave do que
  um falso alarme. Por isso priorizamos o **recall** (≈0.69 na classe positiva), aceitando
  mais falsos positivos em troca de não deixar passar casos.

## 4. Transparência e explicabilidade

- O modelo escolhido (Regressão Logística) é **interpretável**.
- Calculamos **importância das features por permutação**
  (`reports/figures/importancia_features.png`); os fatores de maior peso são coerentes com
  a literatura (**idade** e **hipertensão** à frente), e a tela de predição mostra ao
  usuário quais fatores mais pesam.
- Evolução futura: incorporar **SHAP values** para explicar predições **individuais**.
- O paciente tem o **direito de entender** como foi classificado.

## 5. Limitações técnicas reconhecidas

- Desempenho moderado (ROC-AUC ≈ 0.76): **adequado para triagem**, não para diagnóstico.
- Baseado em **autorrelato** e em features sem exames laboratoriais.
- Não há dados longitudinais (evolução do paciente ao longo do tempo).
- Não considera fatores genéticos detalhados nem histórico familiar (ausente na PNS).

## 6. Resumo das ações de mitigação

1. ✅ **Usar dados brasileiros reais (PNS 2019/IBGE)** — feito (substituiu o Pima).
2. ✅ **Priorizar recall** com balanceamento de classes, reduzindo falsos negativos.
3. ✅ **Excluir cor/raça** das variáveis preditoras.
4. Auditar **métricas por subgrupo** (sexo, idade, região) antes de qualquer uso real.
5. Comunicar que diagnósticos **não detectados** não são capturados pelo autorrelato.
6. Manter o **aviso de apoio à decisão** visível e evoluir a explicabilidade com **SHAP**.
