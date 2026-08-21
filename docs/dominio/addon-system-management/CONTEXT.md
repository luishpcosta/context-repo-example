---
contexto: Add-on & System Management
depende_de: [Automation & State Engine]
---

# Add-on & System Management

Subdomínio de suporte que cuida do ciclo de vida do sistema em si: instalar/atualizar
add-ons, fazer backup, manter o host saudável. Não é o diferencial de produto, mas é
o que torna o produto operável de forma confiável em hardware dedicado.

Realizado tecnicamente pelos componentes `supervisor` e `operating-system` (ver
`../../../catalog-info.yaml`).

## Linguagem

**Home Assistant Supervisor**:
O componente que orquestra add-ons, atualizações e backups do sistema — a camada de
gestão que roda ao lado do core, cuidando do ciclo de vida do que roda na instalação.
_Evitar_: Hass.io (nome legado).

**Add-on**:
Uma aplicação containerizada que estende as capacidades do sistema (ex.: um servidor
MQTT, um banco de dados), instalada e gerenciada pelo Supervisor, fora do processo do
core.

**Add-on Store**:
A vitrine onde o usuário descobre e instala add-ons, alimentada por um ou mais
Repositórios de Add-ons.

**Repositório de Add-ons**:
Uma fonte (git) de definições de add-ons que qualquer pessoa pode publicar e que o
usuário adiciona à Add-on Store para expandir o catálogo disponível.

**Ingress**:
A capacidade de acessar a interface de um add-on através do próprio sistema, sem
precisar expor portas adicionais na rede.

**Backup**:
Um ponto de restauração do sistema (configuração, add-ons, dados) que o usuário cria
manualmente ou por agendamento.
_Evitar_: Snapshot (nome legado, ainda usado pela comunidade).

**Update Channel**:
O nível de estabilidade que o usuário escolhe para receber atualizações — Stable
(padrão), Beta (pré-lançamento) ou Dev (desenvolvimento contínuo, instável).

**Host**:
O sistema operacional subjacente (tipicamente Home Assistant OS) sobre o qual o
Supervisor e seus containers rodam.

**Hardware Passthrough**:
A capacidade de um add-on ou do core acessar dispositivos físicos conectados ao host
(USB, GPIO, Bluetooth) através de permissões concedidas pelo Supervisor.

**Watchdog**:
Mecanismo de auto-recuperação que monitora componentes críticos e reinicia/reverte
automaticamente quando detecta falha, sem intervenção do usuário.

**Home Assistant OS**:
A distribuição Linux dedicada, minimalista, construída para rodar o Supervisor e os
containers do sistema em hardware dedicado — não é de uso geral.

**Boot Slot**:
Uma de duas partições de sistema (A/B) mantidas pelo Home Assistant OS para
atualizações seguras — a atualização é escrita no slot inativo, e o boot só migra
definitivamente para ele se for bem-sucedido; falhas revertem automaticamente.
