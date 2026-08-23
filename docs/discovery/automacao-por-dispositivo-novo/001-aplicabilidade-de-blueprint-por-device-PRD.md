---
id: PRD-20260823-1552-0f65
titulo: Aplicabilidade de Blueprint por tipo de Device
status: rascunho
contextos: [Integration Platform]
afeta: [Automation & State Engine]
supera: []
depende_de: [PB-20260823-1540-6f00]
---

# PRD: Aplicabilidade de Blueprint por tipo de Device

## 1. Identificação

- **Produto**: POC Home Assistant
- **Funcionalidade**: dado um Device, determinar quais Blueprints se aplicam a ele
- **Responsável**: time home-assistant
- **Data**: 2026-08-23
- **Status**: Rascunho

## 2. Contexto e Problema

### 2.1 Cenário atual (as-is)

O sistema já conhece, para cada tipo de Device, as suas Device Automations — os
Triggers, Conditions e Actions que aquele tipo oferece prontos. E já conhece os
Blueprints disponíveis, cada um declarando as lacunas que precisa ter preenchidas.

As duas informações existem lado a lado e nunca se encontram: não há como perguntar
"quais Blueprints fazem sentido para *este* Device". Quem quer automatizar um
dispositivo precisa folhear os Blueprints e julgar por conta própria se cada um se
aplica.

### 2.2 Problema

Sem essa correspondência, todo consumidor que quisesse sugerir automações precisaria
reimplementar o julgamento de aplicabilidade — cada um com o seu critério, cada um
errando de um jeito diferente. É a peça que falta para qualquer oferta de automação
guiada por dispositivo, e por isso ela vem antes de qualquer superfície.

### 2.3 Oportunidade / Valor

Uma resposta única e consultável para "o que dá para automatizar com este
dispositivo". Este PRD não entrega valor visível ao usuário final sozinho — ele
entrega a base sobre a qual os PRDs 002 e 003 se apoiam, e por isso é o primeiro da
cadeia: é reversível, testável isoladamente e não altera nada que o usuário veja.

## 3. Objetivo

### 3.1 Objetivo principal

Responder, para um Device, quais Blueprints são aplicáveis a ele.

### 3.2 Métricas de sucesso

- Cobertura: proporção dos tipos de Device presentes numa instalação para os quais a
  consulta devolve ao menos um Blueprint.
- Precisão percebida: proporção de Blueprints devolvidos que, aplicados, funcionam sem
  o usuário precisar corrigir o alvo — medida quando o PRD-002 existir.
- Tempo de resposta da consulta dentro do orçamento definido em RNF-01.

## 4. Escopo

### 4.1 No escopo

- Determinar aplicabilidade cruzando as Device Automations que o tipo do Device
  oferece com as lacunas que cada Blueprint declara.
- Consultar por um Device específico e obter a lista de Blueprints aplicáveis.
- Informar, junto de cada Blueprint aplicável, quais lacunas dele o próprio Device já
  consegue preencher e quais continuam abertas.

### 4.2 Fora do escopo (não faz)

- Aplicar um Blueprint ou criar qualquer Automation → PRD-20260823-1552-2061.
- Oferecer ou exibir as sugestões em qualquer superfície → PRD-20260823-1552-7f27.
- Escrever, editar ou importar Blueprints — este PRD só consome os que existem.
- Ordenar ou ranquear os Blueprints aplicáveis por relevância, histórico ou
  popularidade.
- Inferir aplicabilidade a partir das Entities individuais do Device quando o tipo
  dele não oferece Device Automations.

## 5. Usuários / Personas

- **Personas**: nenhuma diretamente. Os consumidores desta capacidade são os PRDs 002
  e 003; o beneficiário final é quem está montando a casa, indiretamente.
- **JTBD**: "quando eu tiver um Device em mãos, quero saber o que dá para automatizar
  com ele, para não ter que descobrir isso lendo cada Blueprint."
- **Jornada (happy path)**: um consumidor informa um Device; recebe os Blueprints
  aplicáveis, cada um com as lacunas já preenchíveis pelo Device separadas das que
  restam.
- **Cenário alternativo**: o tipo do Device não oferece Device Automations. A resposta
  é uma lista vazia, explicitamente vazia — não um erro.
- **Cenário de erro**: um Blueprint está malformado ou declara lacunas
  incompreensíveis. Ele é excluído do resultado e o problema fica registrado, sem
  derrubar a consulta inteira: um Blueprint quebrado não pode impedir que os outros
  sejam oferecidos.

## 6. Requisitos Funcionais

- **RF-01**: Dado um Device, o sistema devolve a lista de Blueprints aplicáveis a ele.
- **RF-02**: Um Blueprint é considerado aplicável quando as Device Automations
  oferecidas pelo tipo do Device satisfazem as lacunas que o Blueprint declara como
  obrigatórias.
- **RF-03**: Para cada Blueprint aplicável, a resposta distingue as lacunas que o
  próprio Device preenche das que continuam abertas.
- **RF-04**: Quando o tipo do Device não oferece nenhuma Device Automation, a resposta
  é uma lista vazia, distinguível de falha.
- **RF-05**: Um Blueprint malformado é omitido do resultado sem interromper a
  avaliação dos demais, e a ocorrência é registrada.
- **RF-06**: A consulta considera todos os Blueprints disponíveis na instalação,
  independentemente de terem sido importados de fora ou criados localmente.

## 7. Requisitos Não Funcionais

- **RNF-01**: A consulta responde em tempo compatível com uso interativo, para uma
  instalação com o número de Blueprints típico de uma casa — o alvo exato é decidido
  na arquitetura, mas a consulta não pode ser percebida como espera.
- **RNF-02**: A consulta é livre de efeito colateral: não cria, altera nem remove
  Automation, Blueprint ou Config Entry.
- **RNF-03**: O resultado é determinístico para o mesmo Device e o mesmo conjunto de
  Blueprints — duas consultas seguidas sem mudança devolvem o mesmo.
- **RNF-04**: A avaliação de aplicabilidade não depende de rede externa; Blueprints já
  importados são avaliados localmente.

## 8. Dependências e Restrições

- **Nenhuma ADR vigente restringe esta capacidade.** Não existe nenhum ADR registrado
  neste repositório — este PRD é o primeiro documento a chegar até a fase de
  arquitetura, e as decisões que o `prd-to-adr` tomar sobre ele nascem sem precedente
  a respeitar.
- Depende do PB-20260823-1540-6f00, que estabelece o recorte e proíbe criação de
  Automation sem escolha do usuário.
- Depende do contrato `Device Automation`, compartilhado entre Integration Platform e
  Automation & State Engine — é dele que vem a informação de o que um tipo de Device
  oferece.
- Não depende de nenhum outro PRD: é o primeiro da cadeia e entrega isolado.

## 9. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| A correspondência entre Device Automations e lacunas de Blueprint é frouxa demais, devolvendo Blueprints que não funcionam na prática | Sugestões ruins minam a confiança no PRD-003 antes dele existir | Tratar aplicabilidade como obrigatória-estrita: só entra quem satisfaz todas as lacunas obrigatórias; medir precisão percebida assim que o PRD-002 permitir |
| A correspondência é rígida demais e quase nada é aplicável | A cadeia inteira entrega uma lista vazia | Medir cobertura por tipo de Device antes de seguir para o PRD-002; cobertura baixa é sinal de rever o critério, não de seguir adiante |
| Blueprints da comunidade declaram lacunas de formas inconsistentes | Resultados imprevisíveis conforme a origem do Blueprint | RF-05 isola o malformado; a taxa de exclusão vira sinal a observar |

## 10. Premissas

- As Device Automations declaradas por um tipo de Device descrevem com fidelidade o
  que ele realmente oferece — se forem incompletas, a aplicabilidade herda a lacuna.
- Os Blueprints declaram suas lacunas de forma suficientemente estruturada para serem
  confrontadas com as Device Automations sem interpretação de texto livre.
- O conjunto de Blueprints de uma instalação é pequeno o bastante para ser avaliado
  por consulta, sem índice mantido à parte. Se essa premissa cair, RNF-01 força uma
  decisão de arquitetura que este PRD não antecipa.
