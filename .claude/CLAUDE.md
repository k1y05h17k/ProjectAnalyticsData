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

## Workflow Obrigatório de Inicialização

> **EXECUTE ESTES 4 PASSOS ANTES DE QUALQUER IMPLEMENTAÇÃO. SEM EXCEÇÕES.**

1. **Ler o CLAUDE.md** — confirmar arquitetura, stack, pipeline e restrições vigentes.
2. **Mapear arquivos existentes relevantes** — listar os módulos e dados que serão tocados pela tarefa.
3. **Apresentar plano detalhado** — descrever cada etapa a ser executada, os arquivos envolvidos e a camada do pipeline afetada.
4. **Aguardar aprovação explícita** — NÃO iniciar nenhuma implementação antes de o usuário confirmar o plano.

---

## Estado Atual do Projeto

> Atualize este checklist conforme cada item for concluído.

- [ ] Estrutura de diretórios criada
- [ ] `docker-compose.yml` e `Dockerfile` configurados
- [ ] Dados brutos disponíveis em `/data/raw`
- [ ] Pipeline de ingestão implementado
- [ ] Pipeline de processamento implementado
- [ ] Pipeline de transformação implementado
- [ ] Integração dos datasets implementada
- [ ] Armazenamento no PostgreSQL configurado
- [ ] Análise exploratória realizada
- [ ] Machine Learning aplicado com métricas
- [ ] Visualizações geradas
- [ ] Notebook documentado e revisado

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

> **GATE DE APROVAÇÃO:** ao concluir cada etapa abaixo, apresente o resultado parcial (amostras de dados, logs, métricas) e aguarde confirmação explícita antes de avançar para a próxima etapa.

### 1. Ingestão
- Armazenar dados brutos em `/data/raw`
- NÃO modificar dados nessa etapa
- Garantir idempotência (reexecutar sem efeitos colaterais)

> **GATE:** apresentar contagem de registros carregados por dataset e amostra das primeiras linhas. Aguardar aprovação.

---

### 2. Processamento
- Tratar valores nulos
- Corrigir tipos de dados
- Padronizar nomes de colunas (snake_case)
- Converter datas para formato consistente
- Remover duplicidades

> **GATE:** apresentar relatório de nulos removidos, tipos corrigidos e duplicatas eliminadas. Aguardar aprovação.

---

### 3. Transformação (Feature Engineering)
- Criar métricas derivadas: média de poluição, variação de temperatura, taxa de internações
- Criar agregações por: dia, mês, região

> **GATE:** apresentar amostra das features criadas e das agregações geradas. Aguardar aprovação.

---

### 4. Integração
- Unificar datasets usando chave: `data` + `localização`
- `dados_ar + dados_clima + dados_saude → dataset_final`
- Alinhar datas entre todos os datasets antes do join

> **GATE:** apresentar shape do `dataset_final`, colunas resultantes e verificação de nulos pós-join. Aguardar aprovação.

---

### 5. Armazenamento
- Todos os dados tratados → PostgreSQL (tabelas normalizadas, sem redundância)

> **GATE:** apresentar confirmação de gravação (contagem de linhas por tabela) e schema criado. Aguardar aprovação.

---

### 6. Análise
- Identificar correlações: poluição × internações, temperatura × qualidade do ar
- Base para as hipóteses do modelo de ML

> **GATE:** apresentar matriz de correlação e principais achados antes de prosseguir ao ML. Aguardar aprovação.

---

### 7. Machine Learning

- Modelos permitidos: Regressão Linear, Árvore de Decisão
- Separar treino/teste antes de qualquer ajuste
- Avaliar com métricas: RMSE (regressão), accuracy (classificação)
- NÃO permitir data leakage

**Targets definidos:**

| Tipo            | Target                                                              | Métrica  |
|-----------------|---------------------------------------------------------------------|----------|
| Regressão       | Número de internações do próximo período                            | RMSE     |
| Classificação   | `poluicao_alta` — binário, threshold definido via `.env`            | Accuracy |

> **GATE:** apresentar métricas de avaliação (treino e teste) e análise de overfitting antes de gerar visualizações. Aguardar aprovação.

---

### 8. Visualização
- Gráficos obrigatórios: séries temporais, correlação entre variáveis, distribuições

> **GATE:** apresentar os gráficos gerados e confirmar que cobrem todos os obrigatórios. Aguardar aprovação.

---

## Regras de Negócio

| Conceito           | Definição                                          |
|--------------------|----------------------------------------------------|
| Poluição alta      | valor acima do threshold configurado no `.env`     |
| Internações        | sempre agregadas por período (dia/mês)             |
| Dado inválido      | remover e registrar em log                         |
| Data inconsistente | corrigir e logar antes de qualquer integração      |

---

## Organização de Código

- Funções pequenas, reutilizáveis, com responsabilidade única
- NÃO misturar lógica de camadas diferentes no mesmo módulo
- Logs via `logging` (não `print`)
- Versionamento de dados garantido via naming convention em `/data/`

**Critérios objetivos para `utils/`:**

- Função usada em **mais de 1 módulo** → mover para `utils/` imediatamente
- Função com **mais de 30 linhas** → candidata a refatoração; avaliar extração
- **SEMPRE** verificar `utils/` antes de criar qualquer função nova — evitar duplicação

---

## Convenções de Código

| Elemento               | Convenção          | Exemplo                        |
|------------------------|--------------------|--------------------------------|
| Arquivos               | snake_case         | `air_quality_processor.py`     |
| Funções                | snake_case         | `load_raw_data()`              |
| Classes                | PascalCase         | `DataIngestionPipeline`        |
| Constantes             | UPPER_SNAKE_CASE   | `MAX_NULL_THRESHOLD`           |
| Variáveis de DataFrame | prefixo `df_`      | `df_air_quality`, `df_health`  |

---

## Padrão de Logging

> Use `logging` em todos os módulos. **Nunca use `print`.**

| Nível     | Quando usar                                                   |
|-----------|---------------------------------------------------------------|
| `DEBUG`   | Detalhes internos de execução (valores intermediários, shapes)|
| `INFO`    | Início e fim de cada etapa do pipeline                        |
| `WARNING` | Dado inválido removido ou data inconsistente corrigida        |
| `ERROR`   | Falha que interrompe ou compromete a execução                 |

**Formato padrão de mensagem:**

```
[ETAPA] mensagem descritiva
```

Exemplos:
```python
logging.info("[INGESTÃO] Carregados 1.200 registros de qualidade do ar.")
logging.warning("[PROCESSAMENTO] 14 registros com data inválida corrigidos.")
logging.error("[INTEGRAÇÃO] Join falhou: coluna 'localizacao' ausente em df_health.")
```

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

## Checklist Pré-entrega

> Execute este checklist antes de entregar qualquer resposta que contenha código.

- [ ] As camadas do pipeline estão separadas (sem mistura de responsabilidades)?
- [ ] Existe lógica duplicada que deveria estar em `utils/`?
- [ ] Os dados em `/data/raw` permanecem intocados?
- [ ] Há algum valor hardcoded que deveria estar no `.env`?
- [ ] O código usa `logging` em todos os pontos (nenhum `print` restante)?
- [ ] O código pertence à etapa correta do pipeline?
- [ ] Os targets de ML estão alinhados com a tabela definida neste documento?
- [ ] As convenções de nomenclatura (snake_case, PascalCase, `df_`) foram seguidas?

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
