# Context Map

Visão de produto e capacidades da POC Home Assistant — subdomínios de domínio (DDD),
não a arquitetura técnica (essa vive em `catalog-info.yaml`). Este mapa é o único
ponto de entrada para navegar a documentação de domínio deste repositório.

## Contextos

- [Automation & State Engine](./docs/dominio/automation-state-engine/CONTEXT.md) — mantém o estado da casa e reage a mudanças através de automações; núcleo diferenciador do produto
- [Integration Platform](./docs/dominio/integration-platform/CONTEXT.md) — conecta o sistema a dispositivos e serviços externos, dando escala ao que o Automation Engine enxerga e controla
- [Add-on & System Management](./docs/dominio/addon-system-management/CONTEXT.md) — gerencia o ciclo de vida do sistema em si: add-ons, backups, updates, saúde do host
- [Client Experience](./docs/dominio/client-experience/CONTEXT.md) — como o usuário vê e controla o lar: web, mobile, voz, wearables
- [Build & Distribution](./docs/dominio/build-distribution/CONTEXT.md) — entrega os demais componentes ao usuário de forma consistente entre arquiteturas de hardware

## Relacionamentos

- **Integration Platform → Automation & State Engine**: compartilha o contrato `Entity` — toda Entity registrada pela Integration Platform é o que o Automation & State Engine observa e manipula.
- **Client Experience → Automation & State Engine**: compartilha o contrato `State` — o Dashboard/Companion App exibe e comanda o State mantido pela State Machine.
- **Client Experience → Integration Platform**: compartilha o contrato `Entity` — os Cards do Dashboard representam Entities.
- **Add-on & System Management → Automation & State Engine**: depende do core estar rodando para orquestrar em torno dele (Supervisor gerencia o processo do core).
- **Build & Distribution**: subdomínio de suporte genérico, sem dependência de domínio — fornece a base de imagens usada pelos demais na entrega.

## Correlação com catalog-info.yaml (arquitetura técnica)

Cada `Component` de `catalog-info.yaml` declara `spec.subdomain`, apontando para as
entradas deste mapa — é o elo entre a visão de produto (aqui) e a visão as-is técnica
(lá):

| Subdomínio | Componentes (`catalog-info.yaml`) |
|---|---|
| Automation & State Engine | `core` |
| Integration Platform | `core` |
| Add-on & System Management | `supervisor`, `operating-system` |
| Client Experience | `frontend`, `android`, `ios` |
| Build & Distribution | `docker` |

## Documentos de negócio (as-is)

Nenhum PRD/briefing formal existe para este projeto open source — os `CONTEXT.md`
acima foram construídos a partir da documentação pública oficial
(developers.home-assistant.io, home-assistant.io/docs) e validados contra a
terminologia real usada no código dos repositórios clonados. Fontes citadas dentro de
cada `CONTEXT.md` que originou termos específicos.

## Planejamento (to-be)

Nenhum ainda — POC em estágio de modelagem de domínio inicial.
