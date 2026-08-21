# ADR-20250115-1030-7a2c: Cancelamento só confirma para o cliente depois do estorno confirmado

- **Status**: Aceito
- **Data**: 2025-01-15
- **Contexto de domínio**: Ordering ↔ Payment

## Contexto

Times de suporte relataram casos em que o pedido aparecia como "cancelado" para o
cliente, mas o dinheiro só voltava dias depois — gerando reclamações e retrabalho.
Queremos garantir que o cliente nunca veja a confirmação de cancelamento antes do
estorno realmente acontecer.

## Decisão

Ordering chama Payment de forma síncrona (HTTP) no fluxo de cancelamento: Payment
processa o estorno e devolve o resultado final na mesma chamada. Ordering só marca o
pedido como cancelado e responde ao cliente depois de receber a confirmação de que o
estorno foi concluído com sucesso.

## Consequências

- **Positivas**: o cliente nunca vê "cancelado" sem o dinheiro devolvido
- **Negativas / trade-offs**: o cancelamento fica mais lento e passa a depender da
  disponibilidade de Payment no momento da chamada

## Contextos/componentes afetados

- Ordering
- Payment
