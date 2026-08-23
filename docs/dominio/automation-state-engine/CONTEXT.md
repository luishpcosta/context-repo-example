---
contexto: Automation & State Engine
depende_de: [Integration Platform]
realizado_por:
  - componente: core
    caminho: homeassistant/core.py
  - componente: core
    caminho: homeassistant/helpers
  - componente: core
    caminho: homeassistant/components/automation
  - componente: core
    caminho: homeassistant/components/script
  - componente: core
    caminho: homeassistant/components/scene
  - componente: core
    caminho: homeassistant/components/blueprint
  - componente: core
    caminho: homeassistant/components/device_automation
---

# Automation & State Engine

Núcleo diferenciador do produto: mantém o estado de tudo na casa e permite reagir a
mudanças através de automações. É o subdomínio de negócio mais central — sem ele o
sistema seria só um agregador passivo de integrações.

Realizado tecnicamente pelo componente [`core`](../../componentes/core.md), nos caminhos
listados em `realizado_por` no front matter acima.

## Linguagem

**State**:
A informação de interesse de uma entidade em um dado momento (ex.: se uma luz está
ligada, a temperatura atual).

**State Machine**:
O registro central que guarda o estado de todas as entidades do sistema; toda mudança
de estado passa por ele e dispara um Event correspondente.

**Entity**:
Um sensor, atuador ou função representada no sistema — o bloco fundamental que guarda
dados e possui um estado. Normalmente pertence a um Device.

**Event**:
O que é emitido sempre que algo acontece no sistema (ex.: toda mudança de estado gera
um evento); mecanismo pelo qual outras partes do sistema reagem a mudanças.

**Trigger**:
O conjunto de condições que, quando satisfeitas, faz uma Automation começar a rodar
(ex.: um horário, uma mudança de estado).

**Condition**:
Parte opcional de uma Automation que impede a Action de ser executada se não for
satisfeita, mesmo com o Trigger disparado.

**Action**:
O que é executado quando uma Automation dispara — interage com alvos (dispositivos,
entidades) para fazer algo acontecer.
_Evitar_: Service (termo antigo, substituído por Action).

**Automation**:
Conecta um ou mais Triggers a uma ou mais Actions, no formato "quando X, então faça
Y", com Conditions opcionais no meio.

**Script**:
Uma sequência de Actions executada quando acionada manualmente ou chamada por outra
automação — difere de Automation por não ter Trigger próprio.

**Blueprint**:
Um modelo reutilizável de Automation ou Script com lacunas a preencher — quem o usa
informa só o que muda (quais dispositivos, quais horários) em vez de montar a automação
inteira. Pode ser compartilhado e importado de fora do sistema.

**Device Automation**:
Os Triggers, Conditions e Actions que um Device oferece prontos pelo seu tipo — permite
montar uma automação escolhendo o dispositivo, sem saber quais Entities ele expõe por
dentro.

**Scene**:
Uma configuração predefinida de estados desejados para um conjunto de entidades (ex.:
"modo cinema" ajusta luzes, TV e persianas de uma vez).
