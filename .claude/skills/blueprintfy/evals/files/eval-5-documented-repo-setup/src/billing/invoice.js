export function createInvoice(event) {
  return {
    orderId: event.orderId,
    amount: event.total,
    status: 'issued',
  };
}
