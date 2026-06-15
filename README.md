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

- **Dataset:** Pima Indians Diabetes Database (768 registros, 8 features clínicas + alvo),
  em `data/diabetes.csv`.
- **Pré-processamento** (`utils/preprocessamento.py`): zeros fisiologicamente impossíveis
  tratados como ausentes → imputação pela mediana → padronização (StandardScaler), tudo
  encapsulado em um `Pipeline` reutilizado no treino e na inferência.
- **Modelagem** (`models/treino_modelo.py`): comparação de **4 algoritmos** com
  **validação cruzada 5-fold** estratificada e seleção pelo melhor ROC-AUC.
- **Avaliação:** accuracy, precision, recall, F1 e ROC-AUC; matriz de confusão e curva ROC.
- **Explicabilidade:** importância das features por permutação (model-agnostic).
- **Ética:** ver [ETICA.md](ETICA.md).

### Resultados (validação cruzada 5-fold)

| Algoritmo | ROC-AUC | F1 | Acurácia | Recall |
|---|---|---|---|---|
| **Regressão Logística** ⭐ | **0.843** | 0.655 | 0.788 | 0.575 |
| SVM (RBF) | 0.833 | 0.648 | 0.780 | 0.584 |
| Gradient Boosting | 0.821 | 0.631 | 0.756 | 0.598 |
| Random Forest | 0.820 | 0.653 | 0.774 | 0.608 |

⭐ Modelo selecionado. Desempenho no **conjunto de teste** (dados nunca vistos):
ROC-AUC **0.813**, acurácia 0.71. Figuras e métricas completas em `reports/`.

> Nota: a acurácia ~71% é **coerente** com o estado da arte para este dataset — não há
> vazamento de alvo. (A versão anterior usava a própria glicemia para definir e prever o
> alvo, o que inflava artificialmente os resultados.)

## Estrutura de pastas

```
glicuidado/
├── app.py                      # Aplicação Streamlit
├── requirements.txt
├── ETICA.md                    # Reflexão ética (vieses, fairness, mitigação)
├── data/
│   └── diabetes.csv            # Dataset Pima (treino do modelo de IA)
├── notebooks/
│   └── eda_diabetes.ipynb      # Análise Exploratória de Dados (EDA)
├── models/
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

2. **Treine o modelo** (gera `models/modelo_diabetes.pkl`, `reports/metrics.json` e as figuras):

```bash
python models/treino_modelo.py
```

3. (Opcional) Explore a **EDA**: abra `notebooks/eda_diabetes.ipynb` no Jupyter/VSCode.

4. Rode a aplicação:

```bash
streamlit run app.py
```

A aba **"Predição IA"** usa o modelo treinado para estimar o risco de diabetes a partir
dos dados clínicos informados.

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

