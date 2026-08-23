# Formato de ADR

ADRs de modelagem de domínio seguem a mesma convenção usada pelas skills
`prd-to-adr`/`issue-to-adr` deste catálogo, para manter um único formato de ADR no
repo onde a skill for instalada: arquivo `adr/ADR-<id>-titulo.md`.

Crie a pasta `adr/` (ou a que o repo já usa, se houver uma) de forma preguiçosa — só
quando a primeira ADR for realmente necessária.

## Quando vale a pena registrar uma ADR

Todas as três condições abaixo precisam ser verdadeiras:

1. **Difícil de reverter** — o custo de mudar de ideia depois é relevante.
2. **Surpreendente sem contexto** — um leitor futuro vai olhar para o código e se
   perguntar "por que fizeram assim?".
3. **Resultado de um trade-off real** — havia alternativas genuínas e uma foi
   escolhida por razões específicas.

Se a decisão é fácil de reverter, pule — ela será revertida se precisar. Se não é
surpreendente, ninguém vai se perguntar o porquê. Se não havia alternativa real, não
há nada a registrar além de "fizemos o óbvio".

### O que costuma qualificar (no contexto de modelagem de domínio)

- **Forma dos bounded contexts.** "Ordering e Billing são contextos separados porque
  têm ciclos de vida e times diferentes."
- **Padrões de integração entre contextos.** "Ordering e Billing se comunicam via
  eventos de domínio, não HTTP síncrono."
- **Escolhas de linguagem onipresente com impacto largo.** Quando renomear um
  conceito central (ex.: "Account" → "Customer") afeta múltiplos contextos e times.
- **Decisões de fronteira e escopo.** "Dados do Customer pertencem ao contexto
  Customer; outros contextos só referenciam por ID." Os "nãos" explícitos valem tanto
  quanto os "sins".
- **Desvios deliberados do caminho óbvio.** Qualquer coisa em que um leitor razoável
  assumiria o oposto.
- **Alternativas rejeitadas quando a rejeição não é óbvia.** Se um modelo alternativo
  (ex.: um único contexto genérico "Sales" em vez de Ordering+Billing separados) foi
  considerado e descartado por razões sutis, registre — senão alguém vai propor de
  novo em seis meses.

## Gerando o ID

Mesma convenção de `prd-to-adr`: `ADR-<data:YYYYMMDD>-<hora:HHMM>-<sufixo aleatório de
4 caracteres>` (ex.: `ADR-20260620-1542-3f0a`).

```bash
date +%Y%m%d-%H%M
printf '%04x' $((RANDOM % 65536))
```

Não depende de histórico nem de perguntar ao usuário. Antes de usar, confira se já
existe `adr/ADR-<id>-*.md`; se houver colisão, gere um novo sufixo e tente de novo.

## Front matter de relação (obrigatório)

Toda ADR abre com um front matter YAML — é o metadado que alimenta o grafo de
dependências (`scripts/graph_query.py`); o corpo continua markdown/prosa. Os valores de
`contextos`/`afeta` usam **o nome exato da entrada no `CONTEXT-MAP.md`**.

```yaml
---
id: ADR-<id>
titulo: <título curto da decisão>
status: proposto            # proposto | aceito | superado
contextos: [<contexto(s) a que a decisão pertence>]
afeta: [<contexto(s)/componente(s) impactado(s)>]
supera: [<ADR-id que esta decisão substitui>]   # [] se não substitui nenhuma
depende_de: [<ADR-id>]                           # opcional
---
```

Regras:
- **`supera` é declarado na ADR nova**, não na antiga. `graph_query.py` deriva
  `status: superado` para a ADR alvo — **não** edite a ADR antiga à mão.
- Se a decisão vier de `prd-to-adr`/`issue-to-adr`, o front matter é o mesmo (mantêm o
  formato uniforme para o grafo enxergar todas as ADRs).

## Template

```md
---
id: ADR-<id>
titulo: <título curto da decisão>
status: proposto
contextos: [<contexto>]
afeta: [<contexto/componente>]
supera: []
depende_de: []
---

# ADR-<id>: <título curto da decisão>

- **Status**: Proposto
- **Data**: <data>

## Contexto

<Por que essa decisão precisa ser tomada agora. Cite o termo/relação do CONTEXT.md
que motivou a discussão, ou o documento de negócio de origem. 2-4 frases.>

## Decisão

<Descrição objetiva do que foi decidido — fronteira de contexto, padrão de
integração, escolha de linguagem onipresente. Inclua diagrama se ajudar a
visualizar a relação entre contextos: se a skill `make-diagram` estiver
disponível, gere a imagem com ela assim que a ADR for criada e referencie aqui
(`![Decisão](./ADR-<id>-diagrama.png)`); senão, use Mermaid inline.>

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|-------------|---------------------------|
| <opção 2> | <motivo> |
| <opção 3> | <motivo> |

## Consequências

- **Positivas**: <ex.: fronteira clara reduz acoplamento acidental>
- **Negativas / trade-offs**: <ex.: exige tradução de dados na borda do contexto>
- **Riscos**: <ex.: contexto ainda pode se mostrar mal-recortado com o tempo>

## Contextos/componentes afetados

- <contexto-1>
- <contexto-2>
```

A seção **Alternativas consideradas** só entra se as alternativas rejeitadas forem
não-óbvias; a seção **Consequências** só entra se houver efeitos colaterais que valham
a pena registrar. Um ADR pode ser bem mais curto que o template completo — a parte
obrigatória é Contexto + Decisão.
