# PRD — Cancelamento de Pedidos

## Contexto

Hoje, quando um cliente quer cancelar uma compra, o time de atendimento faz isso
manualmente direto no banco. Queremos um fluxo self-service.

## Conceitos

- **Pedido**: conjunto de itens comprados por um cliente em uma única transação de
  checkout.
- **Cliente**: pessoa cadastrada na plataforma que realiza pedidos. Diferente do
  usuário que só navega sem se cadastrar.
- **Cancelamento**: ato de encerrar um pedido antes da entrega, devolvendo o valor
  pago integralmente.
- **Fatura**: documento gerado após o pedido ser confirmado, usado para cobrança.

## Requisitos

- RF-01: cliente pode cancelar pedido ainda não enviado.
- RF-02: cancelamento gera estorno automático.
- RF-03: cancelamento é sempre do pedido inteiro (não existe cancelamento parcial de
  itens, por ora).
