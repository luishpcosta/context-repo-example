---
contexto: Ordering
depende_de: []
compartilha_contrato_com:
  - contexto: Payment
    contrato: PedidoCancelado
---
# Ordering

Contexto responsável por receber, acompanhar e cancelar pedidos de clientes.

## Linguagem

**Pedido**:
Conjunto de itens comprados por um cliente em uma única transação.
_Evitar_: Order, compra
