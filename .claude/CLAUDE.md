# ProjectAnalyticsData — Air Quality & Health Analytics

Perfil: **Senior Python Developer & Data Engineer**

> Consulte este arquivo em toda nova interação antes de sugerir ou implementar qualquer coisa.

---

## Objetivo

Solução de engenharia de dados baseada em **dados estruturados (tabulares)** para analisar a relação entre poluição do ar, condições climáticas e impacto na saúde pública (internações hospitalares), com foco em:

- Identificar padrões e correlações entre as variáveis
- Prever riscos de alta poluição ou impacto na saúde
- Gerar insights acionáveis

---

## Fontes de Dados

| Dataset              | Formato | Conteúdo                        |
|----------------------|---------|---------------------------------|
| Qualidade do ar      | CSV     | índices de poluição por região  |
| Dados climáticos     | CSV     | temperatura, umidade            |
| Dados de saúde       | CSV     | internações hospitalares        |

> Dados estruturados: organizados em linhas (registros) e colunas (atributos tipados). Base ideal para ML e análise analítica de alta performance.

---

## Arquitetura — NÃO ALTERAR SEM JUSTIFICATIVA

```
Data Sources → Ingestion → Processing → Transformation → Storage → Analysis → ML → Visualization
```

Cada etapa tem responsabilidade exclusiva. Nunca misturar lógicas entre camadas.

---

## Stack Tecnológica

| Categoria      | Tecnologia                          |
|----------------|-------------------------------------|
| Linguagem      | Python 3.11+                        |
| Dados          | pandas, numpy                       |
| Visualização   | matplotlib, seaborn                 |
| ML             | scikit-learn                        |
| Banco de dados | PostgreSQL                          |
| Ambiente       | Docker + Docker Compose             |
| Documentação   | Jupyter Notebook                    |
| Config         | .env                                |

---

## Estrutura de Diretórios

```
project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── data/
│   └── raw/          # dados brutos — nunca modificar
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── transformation/
│   ├── analysis/
│   ├── ml/
│   └── utils/
└── notebooks/
```

---

## Regras de Containerização — OBRIGATÓRIAS

- NÃO instalar dependências fora do container
- Fixar versões no `requirements.txt`
- Usar volumes para persistência de dados
- Separar serviços: `app` (Python + Jupyter) e `db` (PostgreSQL)
- Configurações via `.env` — nunca hardcoded

---

## Pipeline de Dados — NÃO QUEBRAR ETAPAS

### 1. Ingestão
- Armazenar dados brutos em `/data/raw`
- NÃO modificar dados nessa etapa
- Garantir idempotência (reexecutar sem efeitos colaterais)

### 2. Processamento
- Tratar valores nulos
- Corrigir tipos de dados
- Padronizar nomes de colunas (snake_case)
- Converter datas para formato consistente
- Remover duplicidades

### 3. Transformação (Feature Engineering)
- Criar métricas derivadas: média de poluição, variação de temperatura, taxa de internações
- Criar agregações por: dia, mês, região

### 4. Integração
- Unificar datasets usando chave: `data` + `localização`
- `dados_ar + dados_clima + dados_saude → dataset_final`
- Alinhar datas entre todos os datasets antes do join

### 5. Armazenamento
- Todos os dados tratados → PostgreSQL (tabelas normalizadas, sem redundância)

### 6. Análise
- Identificar correlações: poluição × internações, temperatura × qualidade do ar
- Base para as hipóteses do modelo de ML

### 7. Machine Learning
- Modelos permitidos: Regressão Linear, Árvore de Decisão
- Separar treino/teste antes de qualquer ajuste
- Avaliar com métricas: RMSE (regressão), accuracy (classificação)
- NÃO permitir data leakage

### 8. Visualização
- Gráficos obrigatórios: séries temporais, correlação entre variáveis, distribuições

---

## Regras de Negócio

| Conceito        | Definição                                          |
|-----------------|----------------------------------------------------|
| Poluição alta   | valor acima do threshold configurado no `.env`     |
| Internações     | sempre agregadas por período (dia/mês)             |
| Dado inválido   | remover e registrar em log                         |
| Data inconsistente | corrigir e logar antes de qualquer integração  |

---

## Organização de Código

- Funções pequenas, reutilizáveis, com responsabilidade única
- NÃO duplicar código — extrair para `utils/` quando necessário
- NÃO misturar lógica de camadas diferentes no mesmo módulo
- Logs via `logging` (não `print`)
- Versionamento de dados garantido via naming convention em `/data/`

---

## Documentação (Notebooks)

Cada notebook deve conter:
1. Descrição dos dados utilizados
2. Processo de limpeza e transformações realizadas
3. Análises e gráficos
4. Decisões técnicas e justificativas
5. Conclusões e insights

---

## Restrições Absolutas

- NÃO alterar arquitetura sem justificativa explícita
- NÃO misturar etapas do pipeline
- NÃO duplicar lógica entre módulos
- NÃO modificar dados em `/data/raw`
- SEMPRE explicar a abordagem antes de implementar mudanças

---

## Checklist de Entrega

- [ ] Dados carregados corretamente dos três datasets
- [ ] Pipeline end-to-end funcionando
- [ ] Integração entre datasets (ar + clima + saúde)
- [ ] Machine Learning aplicado com métricas
- [ ] Notebook documentado
- [ ] Insights gerados e visualizados

---

## Extensões Opcionais

- Dashboard interativo com Streamlit
- API REST para consulta de dados
- Agendamento do pipeline
