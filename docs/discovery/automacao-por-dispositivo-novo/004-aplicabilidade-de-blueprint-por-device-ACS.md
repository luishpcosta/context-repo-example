# Atividades e Acceptance Criteria — ADR-20260823-1606-448c

Rastreabilidade: cada AC aponta para o requisito do PRD-20260823-1552-0f65 que a
origina. AC sem requisito de origem é escopo que ninguém pediu; requisito sem AC é
requisito que ninguém vai verificar.

## Componente: core

### Atividade ADR-20260823-1606-448c-AT-01: regra de aplicabilidade

Implementar o confronto entre o que um Device oferece e o que cada Blueprint precisa,
em `homeassistant/components/blueprint/`, consumindo
`homeassistant/components/device_automation/`.

É o recorte que carrega o risco de produto: se a regra for frouxa demais, sugere
Blueprints que não funcionam; rígida demais, não sugere nada. Não depende do comando
WebSocket para ser exercitada, e por isso vem primeiro.

- **AC-01** — Dado um Device cujo tipo oferece Device Automations que satisfazem todas
  as lacunas obrigatórias de um Blueprint, quando a aplicabilidade é avaliada para esse
  Device, então esse Blueprint é classificado como aplicável. _(RF-01, RF-02)_
- **AC-02** — Dado um Blueprint aplicável em que parte das lacunas é satisfeita pelo
  Device, quando a resposta é montada, então ela traz `resolvidas` com os valores
  derivados do Device e `abertas` com os nomes das lacunas restantes, em campos
  distintos. _(RF-03)_
- **AC-03** — Dado um Blueprint com ao menos uma lacuna obrigatória que nenhuma Device
  Automation do tipo satisfaz, quando a consulta é feita, então esse Blueprint **não**
  consta na resposta. _(RF-02)_
- **AC-04** — Dado um Device cujo tipo não oferece nenhuma Device Automation, quando a
  aplicabilidade é avaliada, então o resultado é um conjunto vazio — ausência de
  aplicáveis, não falha. _(RF-04)_
- **AC-05** — Dado um conjunto com Blueprints importados de fora e Blueprints criados
  localmente, quando a consulta é feita, então ambas as origens são avaliadas sem
  distinção. _(RF-06)_
- **AC-06** — Dado um Blueprint malformado no mesmo domínio, quando a consulta é feita,
  então ele consta na resposta com a chave `error` descrevendo o problema, os demais
  Blueprints são avaliados normalmente, e a consulta conclui com sucesso.
  _(RF-05, refinado pela ADR — ver Consequências)_

### Atividade ADR-20260823-1606-448c-AT-02: comando `blueprint/applicable`

Expor a regra da AT-01 como comando WebSocket, com schema, formato de resposta e
contrato de erro. A forma já está definida pela família de comandos existente — é
encanamento com precedente, não decisão nova.

**O contrato do comando**

- **AC-07** — Dado o comando `blueprint/applicable` com `device_id` válido, quando
  executado, então responde com `send_result` e o mapa no mesmo formato de
  `blueprint/list` (caminho do Blueprint como chave); resultado vazio é entregue como
  mapa vazio por `send_result`, não como erro. _(RF-01, RF-04)_
- **AC-08** — Dado o comando com `device_id` que não existe no registro de Devices,
  quando executado, então responde com erro `ERR_NOT_FOUND`. _(contrato da ADR)_
- **AC-09** — Dado o comando sem `device_id`, ou com `device_id` que não é string,
  quando executado, então é rejeitado pela validação de schema com
  `ERR_INVALID_FORMAT`, sem executar a consulta. _(contrato da ADR)_
- **AC-10** — Dado o comando com o campo opcional `domain` preenchido, quando
  executado, então apenas Blueprints daquele domínio são avaliados; omitido, os
  domínios `automation` e `script` são avaliados. _(contrato da ADR)_

**As garantias não funcionais**

- **AC-11** — Dada uma instalação com 200 Blueprints, quando a consulta é executada
  repetidamente, então o tempo de resposta no percentil 95 não excede 200ms.
  _(RNF-01)_
- **AC-12** — Dada qualquer execução da consulta, incluindo os cenários de erro, quando
  ela termina, então nenhuma Automation, Blueprint ou Config Entry foi criada,
  alterada ou removida. _(RNF-02)_
- **AC-13** — Dadas duas execuções consecutivas com o mesmo `device_id`, sem alteração
  no conjunto de Blueprints nem no registro de Devices, quando comparadas, então as
  respostas são idênticas. _(RNF-03)_
- **AC-14** — Dada uma instalação sem acesso à rede externa, quando a consulta é
  executada sobre Blueprints já importados, então ela conclui normalmente. _(RNF-04)_

## Tabela de rastreabilidade

| Requisito | ACs | Atividade | Cobertura |
|---|---|---|---|
| RF-01 | AC-01, AC-07 | AT-01, AT-02 | completa |
| RF-02 | AC-01, AC-03 | AT-01 | completa — o caso positivo e o negativo |
| RF-03 | AC-02 | AT-01 | completa |
| RF-04 | AC-04, AC-07 | AT-01, AT-02 | completa — a regra e a entrega |
| RF-05 | AC-06 | AT-01 | completa, com o refinamento registrado na ADR |
| RF-06 | AC-05 | AT-01 | completa |
| RNF-01 | AC-11 | AT-02 | completa |
| RNF-02 | AC-12 | AT-02 | completa |
| RNF-03 | AC-13 | AT-02 | completa |
| RNF-04 | AC-14 | AT-02 | completa |
| contrato da ADR | AC-08, AC-09, AC-10 | AT-02 | erros e campo opcional |

Nenhum requisito do PRD-20260823-1552-0f65 ficou sem AC, e nenhuma AC existe sem
requisito ou contrato de origem.

A AT-01 pode ser entregue e verificada sem que a AT-02 exista: a regra é exercitável
diretamente, sem subir conexão WebSocket. A AT-02 depende da AT-01.
