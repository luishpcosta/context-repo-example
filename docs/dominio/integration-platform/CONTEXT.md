---
contexto: Integration Platform
compartilha_contrato_com:
  - contexto: Automation & State Engine
    contrato: Entity
---

# Integration Platform

Subdomínio responsável por conectar o sistema ao mundo real — dispositivos e serviços
externos. É o que dá escala ao produto: cada integração nova amplia o que o Automation
& State Engine consegue enxergar e controlar.

Realizado tecnicamente pelo componente `core` (ver `../../../catalog-info.yaml`).

## Linguagem

**Integration**:
Software que conecta o sistema a um dispositivo, serviço ou plataforma externa; é a
origem de todas as Entities e Actions disponíveis no sistema.

**Domain**:
O identificador único de uma Integration (ex.: `light`, `scene`) — namespace que
prefixa todo Entity ID pertencente àquela integração.

**Device**:
Uma unidade física ou lógica que agrupa uma ou mais Entities (ex.: uma central
multissensor que expõe temperatura, umidade e bateria como entidades separadas).

**Config Entry**:
A configuração de uma instância ativa de uma Integration, fornecida pelo usuário via
fluxo de configuração.

**Platform**:
Um bloco de construção que uma Integration disponibiliza para ser usado por outras
integrações.

**Area**:
Agrupamento lógico de Devices e Entities que corresponde a um cômodo/espaço físico da
casa — permite direcionar ações a um cômodo inteiro de uma vez.

**Zone**:
Uma região geográfica definida em um mapa (não um cômodo) usada para detecção de
presença e disparo de automações por localização.
