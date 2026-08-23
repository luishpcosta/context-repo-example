---
id: PRD-20260823-1552-2061
titulo: Aplicar Blueprint pré-preenchido por Device e Area
status: rascunho
contextos: [Automation & State Engine]
afeta: [Integration Platform]
supera: []
depende_de: [PB-20260823-1540-6f00, PRD-20260823-1552-0f65]
---

# PRD: Aplicar Blueprint pré-preenchido por Device e Area

## 1. Identificação

- **Produto**: POC Home Assistant
- **Funcionalidade**: transformar um Blueprint em Automation com as lacunas já
  preenchidas pelo Device escolhido e pela Area dele
- **Responsável**: time home-assistant
- **Data**: 2026-08-23
- **Status**: Rascunho

## 2. Contexto e Problema

### 2.1 Cenário atual (as-is)

Aplicar um Blueprint hoje é preencher as lacunas dele à mão, uma a uma. Mesmo quando o
usuário chegou ali partindo de um Device específico, a informação se perde: ele
precisa reencontrar o dispositivo na lista de alvos, e depois escolher a luz, o
cômodo, a Entity — dados que o sistema já tinha.

### 2.2 Problema

O trabalho de preencher é justamente o que faz o usuário desistir entre "quero
automatizar isto" e "está automatizado". Cada lacuna que o sistema poderia ter
preenchido e não preencheu é uma chance de abandono — e uma chance de erro, porque
escolher a Entity errada de um Device com várias é fácil.

### 2.3 Oportunidade / Valor

Reduzir a aplicação de um Blueprint ao mínimo de decisões que só o usuário pode tomar.
Este PRD entrega valor sozinho, em qualquer ponto de entrada onde o usuário já tenha um
Device em mãos — não depende do PRD-003 para ser útil.

## 3. Objetivo

### 3.1 Objetivo principal

Aplicar um Blueprint a partir de um Device, criando a Automation com tudo que for
derivável já preenchido.

### 3.2 Métricas de sucesso

- Número de lacunas que o usuário ainda precisa preencher, comparado com aplicar o
  mesmo Blueprint sem partir de um Device.
- Proporção de aplicações iniciadas que chegam a criar a Automation.
- Proporção de Automations criadas por esta via que são desativadas ou removidas na
  primeira semana — sinal de que o pré-preenchimento acertou o alvo errado.

## 4. Escopo

### 4.1 No escopo

- Preencher as lacunas do Blueprint que o Device escolhido resolve diretamente.
- Usar a Area do Device para preencher lacunas que se referem a um cômodo, quando o
  Device estiver associado a uma.
- Apresentar ao usuário o que foi preenchido, de forma alterável, antes de a Automation
  existir.
- Criar a Automation somente após confirmação explícita do usuário.
- Permitir que o usuário altere qualquer valor pré-preenchido antes de confirmar.

### 4.2 Fora do escopo (não faz)

- Determinar quais Blueprints se aplicam a um Device → PRD-20260823-1552-0f65.
- Oferecer Blueprints no fluxo de configuração de uma Integration →
  PRD-20260823-1552-7f27.
- Criar qualquer Automation sem confirmação — proibição herdada do PB e inegociável
  neste PRD.
- Preencher lacunas por inferência de comportamento, histórico ou hábitos do usuário.
- Editar Automations já existentes.

## 5. Usuários / Personas

- **Personas**: quem está montando a casa; quem instala para outra pessoa.
- **JTBD**:
  - montando a casa — "quando eu escolher uma automação para o meu dispositivo, quero
    que o sistema já saiba de qual dispositivo estou falando, para eu só confirmar."
  - instalando para outro — "quando eu configurar a casa de alguém, quero deixar as
    automações óbvias prontas sem digitar nada duas vezes."
- **Jornada (happy path)**: o usuário parte de um Device e escolhe um Blueprint
  aplicável; vê as lacunas já preenchidas com o Device e a Area; confirma; a Automation
  passa a existir e está ativa.
- **Cenário alternativo**: o Device não tem Area associada. As lacunas de cômodo ficam
  abertas e são apresentadas como pendências normais, sem bloquear a aplicação.
- **Cenário de erro**: o Blueprint deixou de existir, ou mudou, entre a escolha e a
  confirmação. Nenhuma Automation é criada, e o usuário é informado do que mudou — nunca
  se cria uma Automation a partir de uma versão que ele não viu.

## 6. Requisitos Funcionais

- **RF-01**: Dado um Device e um Blueprint aplicável a ele, o sistema pré-preenche as
  lacunas que o Device resolve diretamente.
- **RF-02**: Quando o Device está associado a uma Area, as lacunas que se referem a um
  cômodo são pré-preenchidas com ela.
- **RF-03**: Todo valor pré-preenchido é exibido ao usuário e pode ser alterado antes
  da confirmação.
- **RF-04**: A Automation só é criada após confirmação explícita do usuário.
- **RF-05**: Lacunas que nem o Device nem a Area resolvem são apresentadas como
  pendências a preencher, sem impedir a aplicação.
- **RF-06**: Se o Blueprint tiver mudado ou desaparecido entre a escolha e a
  confirmação, nenhuma Automation é criada e o usuário é informado.
- **RF-07**: A Automation criada é rastreável ao Blueprint de origem e ao Device que a
  originou.

## 7. Requisitos Não Funcionais

- **RNF-01**: Nenhuma Automation é criada sem confirmação — este é um requisito de
  confiança, não de usabilidade, e nenhuma otimização de fluxo pode contorná-lo.
- **RNF-02**: A aplicação é atômica: ou a Automation existe completa e válida, ou nada
  foi criado. Não há estado intermediário visível.
- **RNF-03**: A Automation criada é indistinguível, em capacidade e em edição
  posterior, de uma criada à mão — aplicar um Blueprint não produz um objeto de
  segunda classe.
- **RNF-04**: A rastreabilidade de RF-07 sobrevive à edição posterior da Automation.

## 8. Dependências e Restrições

- Depende do PRD-20260823-1552-0f65, que estabelece quais Blueprints são aplicáveis a
  um Device e quais lacunas o Device já preenche. Sem ele, não há de onde derivar o
  pré-preenchimento.
- Depende do PB-20260823-1540-6f00, que proíbe criação de Automation sem escolha
  explícita — RNF-01 é a tradução direta dessa proibição.
- **Nenhuma ADR vigente restringe esta capacidade** — não há ADR registrada neste
  repositório.
- Toca o contrato `Entity`: a Automation criada opera sobre as Entities do Device, e o
  pré-preenchimento precisa escolher a Entity certa entre as que o Device expõe.

## 9. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| O pré-preenchimento escolhe a Entity errada num Device com várias | A Automation faz a coisa certa no alvo errado, e o usuário confia que estava certo | RF-03 torna todo valor visível e alterável antes de confirmar; a métrica de remoção na primeira semana expõe erro sistemático |
| Automation criada é difícil de desfazer para quem não entende o que aplicou | Casa com automações que o dono não sabe explicar nem remover | RF-07 mantém a origem rastreável; RNF-03 garante que ela é editável e removível como qualquer outra |
| A Area do Device está errada ou desatualizada | Pré-preenchimento propaga um dado errado com aparência de certeza | RF-02 só preenche, nunca decide sozinho; o valor fica visível e alterável |
| O usuário confirma sem ler o que foi preenchido | O consentimento vira formalidade | Apresentar o preenchido em linguagem de produto ("acender **a luz da sala**"), não como campos de formulário |

## 10. Premissas

- As lacunas de um Blueprint são identificáveis quanto ao que esperam (um Device, uma
  Entity, um cômodo) — sem isso não há como decidir o que o Device preenche.
- Um Device associado a uma Area está associado à Area correta; este PRD não valida
  essa associação, só a consome.
- O usuário que aplica um Blueprint entende o que a automação resultante faz, porque o
  Blueprint se descreve em linguagem de produto. Se essa premissa cair, o problema é do
  Blueprint, não deste PRD — mas o efeito recai sobre ele.
