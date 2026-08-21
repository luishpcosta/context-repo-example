# Ordering

Contexto responsável por receber e acompanhar pedidos de clientes até o despacho.

## Linguagem

**Pedido**:
Uma solicitação de compra feita por um Cliente, composta por um ou mais Itens.
_Evitar_: Order, compra, transação

**Cancelamento**:
O encerramento de um Pedido antes do despacho, sempre do Pedido inteiro.
_Evitar_: estorno (estorno é do contexto Payment)

**Cliente**:
Uma pessoa ou organização que faz Pedidos.
_Evitar_: usuário, conta
