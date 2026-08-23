# Entrevista de impacto

A disciplina abaixo é a mesma "entrevista implacável" do `blueprintfy`, adaptada a um
escopo diferente: lá o objetivo é **fundar e afiar** o modelo de domínio; aqui o modelo
já existe e o objetivo é medir o **impacto de uma ideia nova sobre ele**. As perguntas
mudam, a postura não.

## Regras de condução

- **Uma pergunta de cada vez.** Espere a resposta antes da próxima. Perguntas
  empilhadas deixam o usuário sem saber o que responder primeiro e produzem respostas
  rasas exatamente nos pontos que mais importam.
- **Sempre ofereça uma resposta recomendada.** "Minha leitura é que isso estende o
  contexto Ordering — confere?" dá ao usuário algo concreto para confirmar ou corrigir,
  em vez de uma folha em branco.
- **O que o repositório pode responder, o repositório responde.** Antes de perguntar
  "quem é afetado?", rode `impacto` no grafo (ou faça a travessia manual) e apresente os
  candidatos: "o grafo aponta que Payment compartilha o contrato PedidoCancelado com
  Ordering — essa ideia mexe nesse contrato?". Perguntar às cegas o que o front matter
  já declara desperdiça a atenção do usuário e produz respostas menos confiáveis que o
  próprio mapa.
- **Desafie contra o glossário.** Se a ideia usa um termo que o `CONTEXT.md` do
  contexto define de outro jeito, aponte na hora: "seu glossário define 'cancelamento'
  como X, mas a demanda parece querer dizer Y — qual dos dois?". Termo novo que a ideia
  introduz é um achado da entrevista, não um detalhe: ele entra no PB e sinaliza que o
  glossário vai precisar de atualização.
- **Estresse com cenários concretos.** Quando o alcance da ideia estiver vago, invente
  um caso de borda e force a precisão: "se o pedido já foi despachado quando o
  reembolso chega, essa ideia ainda se aplica?".

## As perguntas centrais (nesta ordem, pulando as que o grafo já respondeu)

1. **Extensão ou contexto novo?** — "Essa ideia estende o contexto <X> ou está
   sugerindo um bounded context novo?" Um contexto novo é uma decisão de modelagem
   grande demais para nascer dentro de um PB: se a resposta apontar para isso,
   recomende passar pelo `blueprintfy` antes de formalizar o brief.
2. **Contratos publicados** — "Ela consome ou modifica um contrato já publicado?"
   Use `valida-aresta` (ou o front matter `compartilha_contrato_com`) para checar se a
   integração proposta existe na topologia declarada; se não existe, isso é um achado:
   ou a topologia muda (decisão!) ou a ideia se recorta.
3. **Quem mais é afetado** — apresente os candidatos do grafo (`impacto`, 2 saltos) e
   pergunte só o que o grafo não sabe: "além de Payment e Notification, que o grafo
   aponta, tem alguém fora do mapa — time, sistema externo — que precisa entrar?"
4. **Linguagem** — "Isso introduz um conceito que ainda não existe no glossário do
   contexto?" Se sim, o termo candidato aparece no PB (seção "A Solução" ou "Escopo")
   com a definição proposta.
5. **Decisões vigentes** — "Existe ADR que precisaria ser superada para essa ideia
   valer?" Use `vigentes` antes de aceitar a resposta: se a ideia reafirma uma
   premissa que vem de uma ADR **superada**, aponte a tensão — é o gatilho da Fase 3
   (argumentação + checkpoint), não um detalhe de rodapé. Na prática esta pergunta
   raramente chega a ser feita: se o conflito já era visível no reconhecimento da Fase
   0, o SKILL.md manda pular direto para a Fase 3 antes de abrir a entrevista — esta
   pergunta 5 só sobra para o caso em que o conflito é sutil o suficiente para só
   aparecer aqui, no meio da conversa.

## Quando parar

A entrevista termina quando as cinco perguntas centrais têm resposta (dada pelo
usuário ou pelo repositório) e nenhum cenário de borda em aberto muda a classificação
de impacto (contido vs amplo/conflitante). Não prolongue por completude: o PB é um
briefing, não uma spec — profundidade de requisito é trabalho do `pm-create-prd`.
