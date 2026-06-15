# Glicuidado

Aplicação **Streamlit** para apoio ao cuidado de pacientes diabéticos: registro e
acompanhamento de glicemia, dashboard e **predição de risco de diabetes com IA**.

Projeto desenvolvido para o **A3 de Inteligência Artificial (USJT, 1º Semestre 2026)** —
Tema 01: *Diabetes Tipo 2 — predição de risco*.

## Funcionalidades

- Autenticação de usuários e perfil do paciente.
- Registro e histórico de medições de glicemia.
- **Predição de risco de diabetes** com modelo de Machine Learning treinado em dataset real.
- Dashboard com estatísticas e gráficos interativos (Plotly).
- Geração de relatório em CSV.

## Pipeline de IA

- **Dataset:** **Pesquisa Nacional de Saúde (PNS) 2019 — IBGE/Ministério da Saúde**
  ([microdados oficiais](https://ftp.ibge.gov.br/PNS/2019/Microdados/)). Dado **real
  brasileiro**, com relevância social direta. A partir dos microdados (fixed-width,
  ~455 MB) extraímos um dataset enxuto de **5.903 adultos** com 6 features + alvo, salvo
  em `data/diabetes.csv` (gerado por `models/preparar_dados_pns.py`).
- **Alvo:** diagnóstico médico de diabetes autorrelatado (variável `Q03001`). Prevalência
  de ~9,2% (desbalanceado, como na população real).
- **Features** (todas coletáveis no próprio app, **sem exames laboratoriais**):
  idade, sexo, IMC (de peso/altura medidos), hipertensão, atividade física e tabagismo.
- **Pré-processamento** (`utils/preprocessamento.py`): imputação pela mediana →
  padronização (StandardScaler), encapsulado em um `Pipeline` reutilizado no treino e na
  inferência (mesma transformação nos dois lados — sem *train/serve skew*).
- **Modelagem** (`models/treino_modelo.py`): comparação de **4 algoritmos** com
  **validação cruzada 5-fold** estratificada e seleção pelo melhor ROC-AUC. Como o alvo é
  desbalanceado, usa-se `class_weight="balanced"` para priorizar o **recall** clínico.
- **Avaliação:** accuracy, precision, recall, F1 e ROC-AUC; matriz de confusão e curva ROC.
- **Explicabilidade:** importância das features por permutação (model-agnostic).
- **Ética:** ver [ETICA.md](ETICA.md).

### Resultados (validação cruzada 5-fold)

| Algoritmo | ROC-AUC | Recall | F1 | Acurácia |
|---|---|---|---|---|
| **Regressão Logística** ⭐ | **0.772** | 0.702 | 0.301 | 0.701 |
| SVM (RBF) | 0.758 | 0.778 | 0.298 | 0.663 |
| Gradient Boosting | 0.754 | 0.019 | 0.034 | 0.905 |
| Random Forest | 0.701 | 0.074 | 0.110 | 0.891 |

⭐ Modelo selecionado. Desempenho no **conjunto de teste** (dados nunca vistos):
ROC-AUC **0.755**, **recall 0.69** na classe positiva. Figuras e métricas em `reports/`.

> Nota: a partir de features de **estilo de vida** (sem glicemia/insulina de laboratório),
> ROC-AUC ~0.76 é coerente. O destaque é o **recall ~0.69**: o modelo sinaliza ~7 de cada
> 10 pessoas em risco — para uma ferramenta de **triagem**, errar para o lado do falso
> positivo é preferível a deixar passar um caso. Modelos sem balanceamento (Gradient
> Boosting / Random Forest) atingem acurácia ~0.90 mas recall ~0 — inúteis na prática.

## Estrutura de pastas

```
glicuidado/
├── app.py                      # Aplicação Streamlit
├── requirements.txt
├── ETICA.md                    # Reflexão ética (vieses, fairness, mitigação)
├── data/
│   ├── diabetes.csv            # Dataset PNS 2019 já processado (treino do modelo)
│   ├── diabetes_pima_legado.csv # Dataset Pima da versão anterior (referência)
│   └── raw/PNS_2019.txt        # Microdados brutos do IBGE (NÃO versionado; baixar)
├── notebooks/
│   └── eda_diabetes.ipynb      # Análise Exploratória de Dados (EDA)
├── models/
│   ├── preparar_dados_pns.py   # Gera data/diabetes.csv a partir dos microdados da PNS
│   ├── treino_modelo.py        # Treino + comparação de algoritmos
│   ├── previsao.py             # Inferência (lazy loading do pipeline)
│   └── modelo_diabetes.pkl     # Gerado pelo treino
├── reports/                    # Gerado pelo treino
│   ├── metrics.json
│   └── figures/                # comparacao_modelos, matriz_confusao, curva_roc, importancia
├── utils/
│   ├── preprocessamento.py     # Pipeline de pré-processamento
│   ├── relatorio.py
│   ├── estilo.py / autenticacao.py / perfil.py / auth.py
├── database/
│   └── db.py
└── dashboards/
    └── dashboard.py
```

## Como executar

1. Crie e ative um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. (Opcional) **Regere o dataset** a partir dos microdados da PNS 2019. O CSV processado
   (`data/diabetes.csv`) já está versionado; só é preciso refazer se quiser reproduzir do
   zero. Baixe os [microdados do IBGE](https://ftp.ibge.gov.br/PNS/2019/Microdados/Dados/),
   extraia o `PNS_2019.txt` em `data/raw/` e rode:

```bash
python models/preparar_dados_pns.py
```

3. **Treine o modelo** (gera `models/modelo_diabetes.pkl`, `reports/metrics.json` e as figuras):

```bash
python models/treino_modelo.py
```

4. (Opcional) Explore a **EDA**: abra `notebooks/eda_diabetes.ipynb` no Jupyter/VSCode.

5. Rode a aplicação:

```bash
streamlit run app.py
```

A aba **"Predição IA"** usa o modelo treinado para estimar o risco de diabetes a partir do
perfil e estilo de vida (idade, sexo, IMC, hipertensão, atividade física e tabagismo).

## Deploy (Docker / EasyPanel)

O projeto está containerizado num **único serviço Streamlit**.

Arquivos de deploy:

- `Dockerfile` — imagem `python:3.11-slim`; instala as dependências e **treina o modelo
  no build** (o dataset já está versionado), entregando a imagem pronta.
- `docker-compose.yml` — serviço `app` na rede externa `easypanel`, com `restart`,
  `healthcheck` (`/_stcore/health`) e **volume persistente** para o banco SQLite.
- `.streamlit/config.toml` — configura o servidor para rodar atrás do proxy do EasyPanel.
- `.dockerignore` / `.env.example`.

### Pontos importantes

- **Porta do serviço:** `8501` (configure o domínio do EasyPanel para apontar para ela).
- **Persistência:** os dados dos usuários ficam em `/data/glicuidado.db`, montado no volume
  `glicuidado_data` (via `GLICUIDADO_DB_PATH`). Assim os dados **sobrevivem a redeploys**.
- **Rede:** usa a rede externa `easypanel` (a mesma do proxy), com alias `glicuidado_app`.

### Como subir no EasyPanel

1. Crie um app do tipo **Compose** apontando para este repositório.
2. Garanta que a rede `easypanel` exista (já usada pelos seus outros serviços).
3. Faça o deploy — o EasyPanel builda a imagem (incluindo o treino do modelo).
4. Configure o **domínio** do app para a porta **8501**.

### Teste local com Docker

```bash
docker compose up --build
# acesse http://localhost:8501  (exponha a porta se necessário)
```

