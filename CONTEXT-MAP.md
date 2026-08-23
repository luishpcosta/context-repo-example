---
product: POC Home Assistant
owner: home-assistant
system: home-assistant
repos_root: ..
domain_docs: docs/dominio
component_docs: docs/componentes
---

# Context Map

Visão de produto e capacidades da POC Home Assistant — subdomínios de domínio (DDD)
e os componentes técnicos que os realizam. Este mapa é o único ponto de entrada para
navegar a documentação deste repositório: o que ele não alcança não existe para as
ferramentas.

O front matter acima é a configuração do repo (produto, dono, onde os repositórios
técnicos estão clonados) — não há arquivo de config separado.

## Contextos

- [Automation & State Engine](./docs/dominio/automation-state-engine/CONTEXT.md) — mantém o estado da casa e reage a mudanças através de automações; núcleo diferenciador do produto
- [Integration Platform](./docs/dominio/integration-platform/CONTEXT.md) — conecta o sistema a dispositivos e serviços externos, dando escala ao que o Automation Engine enxerga e controla
- [Add-on & System Management](./docs/dominio/addon-system-management/CONTEXT.md) — gerencia o ciclo de vida do sistema em si: add-ons, backups, updates, saúde do host
- [Client Experience](./docs/dominio/client-experience/CONTEXT.md) — como o usuário vê e controla o lar: web, mobile, voz, wearables
- [Build & Distribution](./docs/dominio/build-distribution/CONTEXT.md) — entrega os demais componentes ao usuário de forma consistente entre arquiteturas de hardware

## Relacionamentos

- **Integration Platform → Automation & State Engine**: compartilha dois contratos.
  `Entity` — toda Entity registrada pela Integration Platform é o que o Automation &
  State Engine observa e manipula. `Device Automation` — cada tipo de Device declara
  os Triggers, Conditions e Actions que oferece prontos, e o Automation & State Engine
  os consome para montar automações sem descer ao nível de Entity.
- **Client Experience → Automation & State Engine**: compartilha o contrato `State` — o Dashboard/Companion App exibe e comanda o State mantido pela State Machine.
- **Client Experience → Integration Platform**: compartilha o contrato `Entity` — os Cards do Dashboard representam Entities.
- **Add-on & System Management → Automation & State Engine**: depende do core estar rodando para orquestrar em torno dele (Supervisor gerencia o processo do core).
- **Build & Distribution**: subdomínio de suporte genérico, sem dependência de domínio — fornece a base de imagens usada pelos demais na entrega.

## Componentes técnicos

Os repositórios de código que realizam os contextos acima. Cada arquivo guarda o
`remote`, o `local` (relativo à raiz deste repo) e duas revisões: `commit`, o pin que
só muda quando um humano decide, e `ultimo_visto`, a marca d'água que
`scripts/scan_repos.py --update-refs` atualiza sozinho. Divergência entre as duas é o
sinal de que o componente está descasado da documentação.

- [core](./docs/componentes/core.md) — backend Python: integrações e motor de automação
- [frontend](./docs/componentes/frontend.md) — UI web (TypeScript/Lit)
- [supervisor](./docs/componentes/supervisor.md) — add-ons, updates e backups
- [operating-system](./docs/componentes/operating-system.md) — distro Linux dedicada (HAOS)
- [docker](./docs/componentes/docker.md) — imagens base usadas pelos demais
- [android](./docs/componentes/android.md) — app cliente Android
- [ios](./docs/componentes/ios.md) — app cliente iOS

## Correlação entre domínio e código

A correlação mora no front matter de cada `CONTEXT.md`, no campo `realizado_por`, que
aponta para um componente acima **e para o caminho dentro dele**:

```yaml
realizado_por:
  - componente: core
    caminho: homeassistant/components/automation
```

Ela é declarada uma vez só, na direção domínio → código, porque é essa a direção da
consulta: dada uma pergunta de negócio, achar o código que a responde. O `caminho`
existe para que o escopo de leitura do código seja **dado**, não heurística — sem ele,
uma pergunta sobre automação obrigaria a varrer os 600MB do `core` inteiro.

## Documentos de negócio (as-is)

Nenhum PRD/briefing formal existe para este projeto open source — os `CONTEXT.md`
acima foram construídos a partir da documentação pública oficial
(developers.home-assistant.io, home-assistant.io/docs) e validados contra a
terminologia real usada no código dos repositórios clonados. Fontes citadas dentro de
cada `CONTEXT.md` que originou termos específicos.

## Planejamento (to-be)

Discovery de produto vive em `discovery/<assunto>/`, um diretório por assunto em
refinamento:

```
discovery/<assunto>/
├── PRODUCT_BRIEF.md                   ← o PB (skill pm-create-pb)
├── NNN-slug-<assunto>-PRD.md          ← os PRDs (skill pm-create-prd)
└── NNN-slug-<assunto>-ADR.md          ← a arquitetura (skill prd-to-adr)
```

A pasta é organizada por **assunto**, não por contexto: um assunto que vale a pena
refinar quase sempre atravessa mais de um contexto, e escolher uma pasta obrigaria a
eleger um dono arbitrário. A qual contexto cada documento pertence é declarado no front
matter dele (`contextos`, `afeta`) — que é o que o grafo lê. Caminho não é estrutura
aqui; front matter é.

Cada documento criado precisa ser referenciado nesta seção: o mapa é o único ponto de
entrada, e o que ele não alcança é invisível para o grafo e para as consultas.

O que distingue este repositório de um repositório de planejamento comum é que o
discovery nasce sabendo onde o código está: `pm-create-pb` e `pm-create-prd` leem o
mesmo grafo que a seção "Correlação entre domínio e código" alimenta, então medir
quantos contextos uma ideia toca e achar o código que ela mexe são a mesma travessia.
Para aprofundar até o código-fonte real, a skill `ask` responde sob demanda — leitura e
apresentação, sem gravar nada, a menos que seja pedido.

- [Automações sugeridas ao adicionar um dispositivo](./discovery/automacao-por-dispositivo-novo/PRODUCT_BRIEF.md) — `PB-20260823-1540-6f00`, rascunho: usar o momento da adição de um Device para oferecer os Blueprints aplicáveis ao tipo dele
  - [001 — Aplicabilidade de Blueprint por tipo de Device](./discovery/automacao-por-dispositivo-novo/001-aplicabilidade-de-blueprint-por-device-PRD.md) — `PRD-20260823-1552-0f65`, entrega isolada
  - [002 — Aplicar Blueprint pré-preenchido](./discovery/automacao-por-dispositivo-novo/002-aplicar-blueprint-pre-preenchido-PRD.md) — `PRD-20260823-1552-2061`, depende do 001
  - [003 — Oferta no encerramento da configuração](./discovery/automacao-por-dispositivo-novo/003-oferta-no-fim-da-configuracao-PRD.md) — `PRD-20260823-1552-7f27`, depende do 001 e do 002
