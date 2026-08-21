# Context Map

## Contextos

- [Ordering](./docs/dominio/ordering/CONTEXT.md) — recebe e acompanha pedidos de clientes
- [Payment](./docs/dominio/payment/CONTEXT.md) — processa pagamentos e estornos

## Relacionamentos

- **Ordering → Payment**: Ordering emite evento `PedidoCancelado`; Payment consome
  para iniciar o estorno

## Documentos de negócio (as-is)

- **Ordering**: [regras do domínio](./docs/dominio/ordering/pedidos/) — regras de
  negócio de pedido e cancelamento já produtivas

## Planejamento (to-be)

- **Ordering**: [refinamento](./docs/refinamento/ordering/) — PRODUCT_BRIEF e PRDs
  das funcionalidades em planejamento
