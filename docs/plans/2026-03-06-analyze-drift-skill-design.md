# Design: `/analyze-drift` Skill

> Slash command do Claude Code que executa o pipeline completo de Strategy Drift Detection para qualquer empresa publica.

## Uso

```
/analyze-drift SQ                  # modo interativo (pausa nos gates)
/analyze-drift SQ --auto           # fire-and-forget (gates automaticos)
```

## Estrutura de Dados

```
data/
├── processed/
│   └── {TICKER}/
│       └── {YYYY-MM-DD}/
│           ├── company_context.json    ← Stage -1 (novo)
│           ├── stage_0_sources.md
│           ├── stage_1a_strategy.json
│           ├── stage_1b_actions.json
│           ├── stage_1c_commitments.json
│           ├── stage_2_pillars.json
│           ├── stage_3_actions.json
│           ├── stage_4_coherence.json
│           ├── final_report.md
│           ├── final_report.html
│           └── qa_review.md
├── raw/
│   └── {TICKER}/
│       └── {YYYY-MM-DD}/
│           ├── {ticker}_strategy_*.txt
│           ├── {ticker}_actions_*.txt
│           └── {ticker}_commitments_*.txt
```

## Pipeline (7 Stages)

```
Stage -1 → Stage 0 → Stage 1A/1B/1C → Stage 2 → Stage 3 → Stage 4 → Stage 5
Context    Sources    Gather Info       Pillars   Map        Score     Report
Discovery  Mapping    (parallel)        Synthesis Actions    Coherence + HTML
```

### Stage -1: Company Context Discovery (novo)

O lead agent pesquisa informacoes basicas da empresa e salva em `company_context.json`:

```json
{
  "company_name": "Block, Inc.",
  "ticker": "SQ",
  "exchange": "NYSE",
  "sector": "Financial Technology",
  "ceo": "Jack Dorsey",
  "cfo": "Amrita Ahuja",
  "business_segments": ["Cash App", "Square/Seller", "TIDAL", "TBD/Bitcoin"],
  "ir_url": "https://investors.block.xyz",
  "sec_cik": "0001512673",
  "recent_name_changes": "Formerly Square, Inc. (renamed Dec 2021)"
}
```

Esse contexto e injetado nos prompts via placeholders: `{COMPANY}`, `{TICKER}`, `{CEO}`, `{SEGMENTS}`, etc.

### Stages 0-5: Mesmo pipeline existente

Sem mudancas no framework — apenas parametrizado por empresa.

## Prompts

Mudancas necessarias nos 8 arquivos em `prompts/`:

- Substituir todas as referencias hardcoded a "Block, Inc." por `{COMPANY}`
- Substituir "SQ" por `{TICKER}`, "Jack Dorsey" por `{CEO}`, etc.
- Remover exemplos especificos da Block dos prompts (Cash App, Square/Seller, etc.)
- Os detalhes especificos vem do `company_context.json` gerado no Stage -1
- Stage -1 nao precisa de prompt file — instrucao inline na skill

## Skill File

Localizado em `.claude/skills/analyze-drift.md`.

Conteudo:
1. Parsing do argumento (ticker obrigatorio + flag `--auto` opcional)
2. Criacao dos diretorios `data/processed/{TICKER}/{DATE}/` e `data/raw/{TICKER}/{DATE}/`
3. Execucao do Stage -1 (company context discovery)
4. Orquestracao do time de agentes (TeamCreate + Agent + SendMessage)
5. Quality gates (interativo ou auto, baseado no flag)
6. Geracao do HTML ao final do Stage 5

## Quality Gates

| Gate | Interativo (default) | Auto (`--auto`) |
|------|---------------------|-----------------|
| Apos Wave 1 (sources) | Pausa, mostra resumo, pede aprovacao | Lead valida sozinho |
| Apos Wave 2 (data gathering) | Pausa, mostra sufficiency assessment | Lead valida sozinho |
| Apos Wave 3 (analysis) | Pausa, mostra pillar mappings | Lead valida sozinho |
| Apos Wave 4 (report) | Mostra QA review | Mostra QA review (sempre) |

## Arquitetura de Agentes

Mesmo time de 5 agentes + lead, sem mudancas:

| Agente | Papel |
|--------|-------|
| `prompt-engineer` | QA review do report final |
| `source-scout` | Stage 0 — source mapping |
| `strategy-intel` | Stage 1A + Stage 2 |
| `execution-intel` | Stage 1B + 1C + Stage 3 |
| `drift-analyst` | Stage 4 + Stage 5 |

## O que NAO muda

- Framework de scoring (5 dimensoes, pesos, classificacoes)
- Estrutura do relatorio final (7 secoes)
- Principios cross-cutting (bias tags, rigor metodologico, linguagem academica)
- Arquitetura do time de agentes (5 agentes + lead)

## Execucao em 4 Waves

```
Wave 1 (parallel)     Wave 2 (parallel)        Wave 3 (parallel)     Wave 4 (sequential)
─────────────────     ──────────────────        ─────────────────     ──────────────────
prompt-engineer ──┐   strategy-intel ────┐      strategy-intel ──┐    drift-analyst
  Task: QA prep   │     Task: Stage 1A   │        Task: Stage 2  │      Task: Stage 4
                  │                      │                       │      Coherence
source-scout ─────┤   execution-intel ───┤      execution-intel──┤          │
  Task: Stage 0   │     Task: Stage 1B   │        Task: Stage 3  │          ▼
  Map sources     │     + Stage 1C       │        Map actions    │    drift-analyst
                  │                      │                       │      Task: Stage 5
                  ▼                      ▼                       ▼      + HTML gen
            ┌──────────┐          ┌──────────┐            ┌──────────┐      │
            │  GATE 1  │          │  GATE 2  │            │  GATE 3  │      ▼
            └──────────┘          └──────────┘            └──────────┘┌──────────┐
                                                                     │  GATE 4  │
                                                                     │ QA review│
                                                                     └──────────┘
```
