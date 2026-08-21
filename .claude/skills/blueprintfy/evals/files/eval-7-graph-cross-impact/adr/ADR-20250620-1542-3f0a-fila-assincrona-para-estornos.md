---
id: ADR-20250620-1542-3f0a
titulo: Estornos passam a ser processados por fila assíncrona
status: aceito
contextos: [Payment]
afeta: [Payment, Ordering]
supera: [ADR-20250115-1030-7a2c]
depende_de: []
---
# ADR-20250620-1542-3f0a: Estornos passam a ser processados por fila assíncrona

- **Status**: Aceito
- **Data**: 2025-06-20
- **Contexto de domínio**: Payment

## Contexto

Nos picos de tráfego de campanhas promocionais, o volume de estornos simultâneos
derrubou a latência de Payment e chegou a causar timeout em chamadas de outros
serviços que dependiam dele. É preciso desacoplar o processamento de estorno do
restante do sistema para o serviço não virar gargalo em pico.

## Decisão

Payment passa a publicar cada pedido de estorno em uma fila e processá-lo de forma
assíncrona. Quem chama Payment recebe apenas a confirmação de que o pedido de estorno
foi aceito na fila — não espera mais pelo resultado final do estorno na mesma
chamada.

## Consequências

- **Positivas**: Payment não vira gargalo em picos de tráfego
- **Negativas / trade-offs**: quem depende do resultado do estorno precisa lidar com
  uma confirmação futura, não mais imediata

## Contextos/componentes afetados

- Payment
