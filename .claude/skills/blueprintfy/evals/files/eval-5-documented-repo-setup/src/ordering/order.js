export function confirmOrder(order) {
  order.status = 'confirmed';
  publish('PedidoConfirmado', { orderId: order.id, total: order.total });
  return order;
}
