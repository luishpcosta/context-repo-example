# ADR-20250110-0900-9c3d: Geração de fatura é assíncrona

- **Status**: Aceito
- **Data**: 2025-01-10

## Contexto

O time de Billing processa faturas via fila para não travar o checkout no momento da
confirmação do pedido.

## Decisão

Pedido confirmado publica o evento `PedidoConfirmado`; o serviço de Billing consome
esse evento e gera a fatura de forma assíncrona.

## Consequências

- **Positivas**: checkout não trava esperando a geração da fatura.
- **Negativas**: cliente não vê a fatura imediatamente após confirmar o pedido.
