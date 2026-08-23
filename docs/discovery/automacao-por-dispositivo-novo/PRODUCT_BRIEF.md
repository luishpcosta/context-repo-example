---
id: PB-20260823-1540-6f00
titulo: Automações sugeridas ao adicionar um dispositivo
status: rascunho
contextos: [Integration Platform]
afeta: [Automation & State Engine, Client Experience]
supera: []
depende_de: []
---

# Briefing de produto: Automações sugeridas ao adicionar um dispositivo

## Resumo executivo

Quem acaba de adicionar um dispositivo à casa está no único momento em que sabe
exatamente o que quer que ele faça — e é justamente aí que o sistema não oferece nada.
A proposta é usar esse momento: assim que uma Config Entry é criada, oferecer os
Blueprints que se aplicam àquele tipo de Device, prontos para aplicar em um toque. A
aposta não é construir uma capacidade nova, e sim colocar uma capacidade existente no
momento certo.

## O Problema

Adicionar um dispositivo e automatizá-lo são hoje duas jornadas separadas, e a segunda
começa de uma tela em branco. Quem terminou de parear um sensor de porta precisa sair
do fluxo de configuração, abrir o editor de automações, entender o que é um Trigger,
descobrir quais Entities aquele Device expôs e montar a regra do zero — mesmo quando o
que ele quer ("acender a luz quando abrir") é a automação mais óbvia possível para
aquele tipo de dispositivo.

O custo disso não é o tempo: é a desistência. O usuário que não atravessa essa segunda
jornada fica com um dispositivo conectado que não faz nada além de reportar estado.

## A Solução

No fim do fluxo de configuração de uma Integration, quando a Config Entry acaba de ser
criada, apresentar os Blueprints aplicáveis ao tipo do Device recém-adicionado. O
usuário escolhe um, preenche o que muda (qual luz, qual horário) e a Automation nasce
sem que ele precise abrir o editor.

A aplicabilidade vem do que o Device já declara: as Device Automations dele — os
Triggers, Conditions e Actions que o tipo oferece prontos — dizem que Blueprints fazem
sentido. Um sensor de porta oferece um Trigger de abertura; um Blueprint que consome
esse Trigger é candidato. Nada disso exige o usuário saber quais Entities existem por
baixo.

Se o dispositivo estiver associado a uma Area, a sugestão pode se completar sozinha
(acender **a luz daquele cômodo**), reduzindo a escolha a confirmar em vez de
configurar.

## O que torna Isto Diferente

**A capacidade já existe; o momento é que não.** Blueprints já são um conceito do
sistema, importáveis de fora e aplicáveis a Automation e Script. Device Automations já
descrevem o que cada tipo de Device oferece. O que não existe é o encontro dos dois no
instante da adição — hoje o usuário só chega a um Blueprint se for procurá-lo por conta
própria, depois, em outro lugar.

A alternativa óbvia seria gerar automações automaticamente ao detectar o dispositivo,
sem perguntar. Foi descartada: automação que aparece sozinha na casa de alguém é
comportamento não solicitado, e a confiança perdida na primeira surpresa custa mais do
que a conveniência ganha. Aqui o sistema **oferece**; quem decide é o usuário.

## Quem Isto Serve

- **Quem está montando a casa** — o usuário no fluxo de adição, que ganha valor no
  mesmo minuto em que conectou o dispositivo.
- **Quem instala para outra pessoa** — integrador ou familiar que configura a casa de
  alguém e hoje precisa voltar depois para automatizar.
- **Quem publica Blueprints** — a comunidade que já os escreve e compartilha ganha um
  ponto de distribuição no momento de maior intenção.

## Critérios de Sucesso

- Proporção de Config Entries criadas que terminam com pelo menos uma Automation
  aplicada na mesma sessão.
- Queda no intervalo entre adicionar um dispositivo e ele participar de alguma
  Automation.
- Proporção de dispositivos que seguem sem nenhuma Automation 30 dias após a adição.
- Taxa de rejeição da sugestão — alta demais indica que a aplicabilidade está sendo
  inferida errado, não que o usuário não quer automatizar.

## Escopo

**No escopo:**

- Determinar quais Blueprints se aplicam a um Device, a partir das Device Automations
  que o tipo dele oferece.
- Oferecer essas sugestões no encerramento do fluxo de configuração da Integration.
- Aplicar um Blueprint escolhido com o mínimo de preenchimento, usando o Device
  recém-adicionado e a Area dele quando houver.

**Fora do escopo:**

- Criar Automations sem escolha explícita do usuário.
- Escrever ou editar Blueprints — este brief consome os que existem, não os produz.
- Sugerir automações para dispositivos já adicionados antes desta funcionalidade; o
  gatilho aqui é o momento da adição.
- Ranquear ou personalizar sugestões por histórico de uso.

## Visão

O mesmo mecanismo se estende para além da adição: um dispositivo que passa semanas sem
participar de nenhuma Automation é candidato à mesma oferta, no momento em que o
usuário voltar a olhar para ele. E, se a aplicabilidade por tipo de Device se mostrar
confiável, ela vira insumo para sugerir automações que combinam **vários**
dispositivos de um cômodo, não só o que acabou de entrar.
