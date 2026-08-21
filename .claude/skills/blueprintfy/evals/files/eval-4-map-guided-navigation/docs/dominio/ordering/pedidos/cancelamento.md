# Regras de cancelamento (as-is)

Regras produtivas hoje:

1. O Cancelamento só é permitido **antes do despacho** do Pedido. Após o despacho,
   o caminho é devolução, tratada fora deste contexto.
2. O Cancelamento é sempre do **Pedido inteiro** — não existe cancelamento parcial
   por Item em produção.
3. Ao cancelar, Ordering emite o evento `PedidoCancelado`, consumido pelo contexto
   Payment para estorno integral.
