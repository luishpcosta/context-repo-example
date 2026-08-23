# Critérios de escala: 1 PRD ou N PRDs?

A quebra de um PB em PRDs não é uma preferência estética — ela define as fronteiras
de entrega (o que pode ir para produção sozinho) e as fronteiras de arquitetura (o que
o `prd-to-adr` vai decompor depois). Avalie os quatro critérios abaixo **e mostre a
avaliação ao usuário**: a decisão precisa ser auditável, não um palpite.

## 1. Contextos tocados

Conte os bounded contexts em `contextos` + `afeta` do front matter do PB — e confira
com o grafo (`impacto contexto:<Nome>`, 2 saltos), porque o PB pode ter subestimado o
alcance (ex.: um contrato compartilhado arrasta um contexto que o brief não citou).

- **1 contexto** → aponta para 1 PRD.
- **2+ contextos** → forte sinal de quebra: cada contexto tem ciclo de entrega e dono
  diferentes; um PRD que atravessa contextos obriga times a sincronizar entrega.

## 2. Atores/personas envolvidos

Conte os perfis distintos na seção "Quem Isto Serve" do PB. Muitos atores com
jornadas diferentes dentro de um mesmo PRD produzem uma seção de requisitos que
mistura fluxos — e requisitos misturados viram acceptance criteria ambíguas lá na
frente.

- **1-2 atores com jornadas próximas** → cabe em 1 PRD.
- **3+ atores, ou jornadas sem interseção** → cada jornada independente é candidata a
  PRD próprio.

## 3. Dependência entre capacidades

Liste as capacidades do escopo do PB e pergunte de cada par: "B funciona sem A?".

- **Capacidades acopladas** (só fazem sentido juntas) → mantê-las no mesmo PRD; quebrar
  criaria dependência artificial de entrega.
- **Capacidades independentes** → separá-las permite entrega incremental; o
  encadeamento real (quando existir) fica explícito no `depende_de` do front matter,
  não implícito num documento único.

## 4. Risco / reversibilidade

"É fácil desfazer depois?" Decisões baratas de reverter toleram um PRD maior — se a
aposta errar, volta-se atrás. Decisões caras de reverter (migração de dados, contrato
público, mudança de modelo de cobrança) pedem PRDs menores, com fronteiras que
permitam **parar no meio** sem deixar o sistema em estado quebrado.

## Regra de decisão

- **1 PRD direto**: 1 contexto **e** capacidades acopladas **e** poucos atores.
  Reversibilidade baixa não força quebra sozinha, mas aparece na seção 9 (Riscos).
- **N PRDs (com checkpoint humano antes de gerar)**: qualquer outro arranjo. A
  proposta nomeia cada PRD (capacidade + contexto), diz quais entregam isolados e
  quais dependem de quais — e espera o aceite ou ajuste do usuário.

## Exemplo de proposta de quebra

> O PB `PB-...-indicacao` toca Ordering, Payment e Notification, com 3 capacidades:
> (A) registrar indicação no primeiro pedido, (B) conceder crédito ao indicador,
> (C) comunicar os dois clientes.
> B não funciona sem A; C funciona com o evento que A já publica. Sugiro:
> - PRD-1 — capacidade A, contexto Ordering — entrega isolada
> - PRD-2 — capacidade B, contexto Payment — `depende_de: [PRD-1]`
> - PRD-3 — capacidade C, contexto Notification — `depende_de: [PRD-1]`
