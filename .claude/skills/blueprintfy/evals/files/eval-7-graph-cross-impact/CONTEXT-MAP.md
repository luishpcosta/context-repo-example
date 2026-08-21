# Context Map

## Contextos

- [Ordering](./docs/dominio/ordering/CONTEXT.md) — recebe, acompanha e cancela pedidos de clientes
- [Payment](./docs/dominio/payment/CONTEXT.md) — processa pagamentos e estornos

## Relacionamentos

- **Ordering → Payment**: Ordering aciona Payment no fluxo de cancelamento para
  processar o estorno do pedido

## Decisões (ADR)

- [Registro de decisões](./adr/) — ADRs de todo o sistema, afetam Ordering e Payment
