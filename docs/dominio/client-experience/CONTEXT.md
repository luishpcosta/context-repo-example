---
contexto: Client Experience
compartilha_contrato_com:
  - contexto: Automation & State Engine
    contrato: State
  - contexto: Integration Platform
    contrato: Entity
---

# Client Experience

Subdomínio responsável por como o usuário efetivamente vê e controla o lar — web,
mobile e wearables. É onde o valor do Automation & State Engine e da Integration
Platform chega até a pessoa.

Realizado tecnicamente pelos componentes `frontend`, `android` e `ios` (ver
`../../../catalog-info.yaml`).

## Linguagem

**Dashboard**:
A tela principal de controle e visualização do lar — mostra o estado atual dos
dispositivos e ambientes e permite agir sobre eles com um toque. Superfície de
interação primária do produto, disponível em web, mobile e wearables.

**View**:
Uma seção/aba dentro de um Dashboard que organiza o conteúdo por perspectiva de uso
(ex.: uma view para a cozinha, outra para visitantes). Um Dashboard tem uma ou mais
Views.

**Card**:
O componente visual individual dentro de uma View que exibe um dado ou expõe um
controle. É a unidade de composição da interface.

**Companion App**:
O aplicativo móvel oficial (Android/iOS) que estende a experiência do produto ao
smartphone: leva o Dashboard para o bolso e adiciona capacidades exclusivas do
dispositivo móvel (localização, widgets, notificações).
_Evitar_: "app mobile", "cliente móvel".

**Push Notification**:
Um alerta enviado pelo lar ao dispositivo móvel do usuário fora do app, que além de
exibir uma mensagem pode carregar um comando que dispara uma ação no próprio
dispositivo.

**Assist**:
O assistente de voz do produto: permite controlar o lar por linguagem natural, com a
capacidade de rodar inteiramente no hardware do próprio usuário, preservando a
privacidade dos comandos.
_Evitar_: "voice assistant" genérico — Assist é o nome do produto.

**Widget**:
Um bloco de informação ou controle rápido exibido fora do app, direto na tela inicial
do dispositivo móvel.
