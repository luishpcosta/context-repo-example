---
id: PRD-20260823-1552-7f27
titulo: Oferta de automações no encerramento da configuração
status: rascunho
contextos: [Client Experience]
afeta: [Integration Platform, Automation & State Engine]
supera: []
depende_de: [PB-20260823-1540-6f00, PRD-20260823-1552-0f65, PRD-20260823-1552-2061]
---

# PRD: Oferta de automações no encerramento da configuração

## 1. Identificação

- **Produto**: POC Home Assistant
- **Funcionalidade**: oferecer os Blueprints aplicáveis no momento em que uma Config
  Entry acaba de ser criada
- **Responsável**: time home-assistant
- **Data**: 2026-08-23
- **Status**: Rascunho

## 2. Contexto e Problema

### 2.1 Cenário atual (as-is)

O fluxo de configuração de uma Integration termina confirmando que o Device foi
adicionado, e para ali. O usuário volta para onde estava. Automatizar o dispositivo é
uma jornada separada, que começa depois, em outro lugar, por iniciativa dele.

### 2.2 Problema

O momento de maior intenção do usuário é justamente o que o sistema não usa. Quem
acabou de parear um sensor sabe naquele instante o que quer que ele faça; uma hora
depois, já não vai voltar. Os PRDs 001 e 002 tornam a automação barata, mas ninguém
chega até ela se nada a oferecer.

### 2.3 Oportunidade / Valor

Este é o PRD que converte a capacidade em produto. É também o que carrega o maior
risco: uma oferta mal colocada no fim de um fluxo de configuração é interrupção, e
interrupção no momento errado ensina o usuário a fechar sem ler.

## 3. Objetivo

### 3.1 Objetivo principal

Oferecer, ao final da criação de uma Config Entry, as automações que o Device
recém-adicionado torna possíveis.

### 3.2 Métricas de sucesso

- Proporção de Config Entries criadas que terminam com ao menos uma Automation
  aplicada na mesma sessão — a métrica central do PB.
- Queda no intervalo entre adicionar um Device e ele participar de alguma Automation.
- Proporção de Devices sem nenhuma Automation 30 dias após a adição.
- Taxa de dispensa da oferta: alta demais indica oferta irrelevante ou mal colocada,
  não desinteresse por automação.

## 4. Escopo

### 4.1 No escopo

- Apresentar, ao término do fluxo de configuração de uma Integration, os Blueprints
  aplicáveis ao Device recém-adicionado.
- Permitir aplicar um deles ali mesmo, sem sair do fluxo.
- Permitir dispensar a oferta e concluir a configuração sem automação nenhuma.
- Tratar o caso de nenhum Blueprint aplicável sem mostrar nada ao usuário.

### 4.2 Fora do escopo (não faz)

- Determinar aplicabilidade → PRD-20260823-1552-0f65.
- Pré-preencher e criar a Automation → PRD-20260823-1552-2061.
- Oferecer automações para Devices adicionados antes desta funcionalidade — o gatilho
  aqui é o momento da adição.
- Ranquear ou personalizar a oferta por histórico de uso.
- Insistir: nenhuma reapresentação da oferta depois de dispensada.

## 5. Usuários / Personas

- **Personas**: quem está montando a casa; quem instala para outra pessoa.
- **JTBD**:
  - montando a casa — "quando eu terminar de adicionar um dispositivo, quero que o
    sistema me mostre o que ele pode fazer, para eu não precisar descobrir sozinho
    depois."
  - instalando para outro — "quando eu entregar a casa configurada, quero que as
    automações óbvias já estejam de pé."
- **Jornada (happy path)**: o usuário conclui a configuração da Integration; a Config
  Entry é criada; a oferta aparece com os Blueprints aplicáveis; ele escolhe um,
  confirma o pré-preenchido e a Automation nasce sem que ele saia do fluxo.
- **Cenário alternativo**: não há Blueprint aplicável ao tipo do Device. O fluxo
  encerra exatamente como encerra hoje — nada é mostrado, nem uma mensagem de vazio.
- **Cenário de erro**: a consulta de aplicabilidade falha ou demora além do aceitável.
  A configuração é concluída normalmente e a oferta simplesmente não aparece — falha na
  sugestão nunca compromete a adição do dispositivo.

## 6. Requisitos Funcionais

- **RF-01**: Ao ser criada uma Config Entry, o sistema consulta os Blueprints
  aplicáveis ao Device correspondente.
- **RF-02**: Havendo Blueprints aplicáveis, eles são apresentados ao usuário antes do
  encerramento do fluxo de configuração.
- **RF-03**: O usuário pode aplicar um Blueprint ofertado sem sair do fluxo de
  configuração.
- **RF-04**: O usuário pode dispensar a oferta e concluir a configuração sem criar
  nenhuma Automation.
- **RF-05**: Não havendo Blueprint aplicável, nada é apresentado e o fluxo encerra como
  encerraria sem esta funcionalidade.
- **RF-06**: Falha ou demora na consulta de aplicabilidade não impede nem atrasa a
  conclusão da configuração; a oferta é omitida.
- **RF-07**: Uma oferta dispensada não é reapresentada para a mesma Config Entry.
- **RF-08**: Cada Blueprint ofertado é descrito pelo que a automação fará, em
  linguagem de produto, não pelo nome técnico do Blueprint.

## 7. Requisitos Não Funcionais

- **RNF-01**: A oferta não bloqueia a conclusão da configuração em nenhuma hipótese —
  dispensá-la é sempre possível em um gesto.
- **RNF-02**: A consulta de aplicabilidade tem orçamento de tempo próprio; estourado,
  a oferta é omitida (RF-06) em vez de fazer o usuário esperar.
- **RNF-03**: A experiência é equivalente nas três superfícies de cliente — painel web,
  Android e iOS. Divergência de comportamento entre elas é defeito, não variação
  aceitável de plataforma.
- **RNF-04**: A oferta é acessível pelos mesmos meios que o restante do fluxo de
  configuração, incluindo navegação por teclado e leitor de tela.

## 8. Dependências e Restrições

- Depende do PRD-20260823-1552-0f65 (aplicabilidade) e do PRD-20260823-1552-2061
  (aplicar pré-preenchido). É o último da cadeia: sem os dois, não há o que oferecer
  nem como aplicar.
- Depende do PB-20260823-1540-6f00, que estabelece a oferta como convite, nunca como
  ação automática.
- **Nenhuma ADR vigente restringe esta capacidade** — não há ADR registrada neste
  repositório.
- Restrição de alcance: o contexto Client Experience é realizado por três componentes
  (`frontend`, `android`, `ios`), nenhum deles com caminho declarado no modelo. A
  arquitetura precisa decidir se a oferta é composta uma vez no servidor ou
  implementada três vezes — RNF-03 depende dessa decisão.

## 9. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| A oferta é lida como interrupção no fim de um fluxo que o usuário queria só concluir | Ele aprende a fechar sem ler, e a funcionalidade morre por hábito | RF-04 e RNF-01 tornam dispensar trivial; RF-07 impede insistência; a taxa de dispensa é métrica de vigilância, não de vaidade |
| Divergência entre as três superfícies de cliente | Comportamento diferente por plataforma, e uma métrica que não significa a mesma coisa nos três | RNF-03 trata divergência como defeito; a decisão de composição única entra na arquitetura |
| A consulta de aplicabilidade atrasa a conclusão da configuração | Adicionar dispositivo, que hoje funciona, passa a parecer mais lento | RF-06 e RNF-02: orçamento de tempo próprio e omissão silenciosa em caso de estouro |
| Oferta relevante demais cedo demais, antes de o Device reportar estado | Automation criada sobre um dispositivo que ainda não funciona direito | Aceito conscientemente: a Automation é editável e removível (RNF-03 do PRD-002); alternativa seria adiar a oferta e perder o momento |

## 10. Premissas

- O fluxo de configuração de uma Integration tem um ponto de encerramento identificável
  e comum a todas as integrações. Se cada uma encerrar do seu jeito, RF-02 vira um
  problema por integração e o escopo deste PRD muda.
- A Config Entry recém-criada permite chegar ao Device correspondente no momento do
  encerramento — se o Device só existir depois, o gatilho de RF-01 precisa ser outro.
- As três superfícies de cliente conseguem apresentar a oferta sem cada uma
  reimplementar a lógica de aplicabilidade; caso contrário, RNF-03 é inatingível na
  prática.
