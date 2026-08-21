function cancelOrder(order) {
  order.items.forEach((item) => {
    item.status = 'cancelled';
  });
  order.status = 'cancelled';
  return order;
}

module.exports = { cancelOrder };
