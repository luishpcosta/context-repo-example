# PRODUCT_BRIEF — Ordering (to-be)

Evolução planejada do contexto Ordering para o próximo ciclo.

## Funcionalidade em refinamento: cancelamento parcial

Permitir que o Cliente cancele **Itens individuais** de um Pedido antes do despacho,
mantendo o restante do Pedido ativo. O estorno passa a ser proporcional aos Itens
cancelados (impacto no evento `PedidoCancelado` consumido por Payment ainda não
definido).
