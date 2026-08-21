# Regras de faturamento (produção)

1. A Fatura é gerada de forma assíncrona após a confirmação do Pedido, a partir do
   evento `PedidoConfirmado`.
2. Estornos são processados pelo time de faturamento e sempre referenciam a Fatura
   original.
3. Uma Fatura nunca é editada após emitida — correções geram Nota de Ajuste.
