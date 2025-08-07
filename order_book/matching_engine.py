from trade import Trade
class MatchingEngine:
    def __init__(self, order_book):
        self.order_book = order_book
        self.trades = []

    def process_order(self, order):
        if order.side == "ask":
            self.process_sell_order(order=order)
        else:
            self.process_buy_order(order=order)

    def process_buy_order(self, order):

        while order.quantity > 0:
            best_ask = self.order_book.get_best_ask()

            if best_ask is None:
                break

            if not self.match_possible(buy_order=order, sell_order=best_ask):
                break

            trade = self.execute_trade(buy_order=order, sell_order=best_ask)

            if trade:
                self.trades.append(trade)

        if order.quantity > 0:
            self.order_book.add_order(order)

    def process_sell_order(self, order):
        while order.quantity > 0:
            best_bid = self.order_book.get_best_bid()

            if best_bid is None:
                break

            if not self.match_possible(buy_order=best_bid, sell_order=order):
                break

            trade = self.execute_trade(buy_order=best_bid, sell_order=order)

            if trade:
                self.trades.append(trade)

        if order.quantity > 0:
            self.order_book.add_order(order)

    def match_possible(self, buy_order=None, sell_order=None):
        if sell_order is None or buy_order is None:
            raise ValueError("BUY OR SELL ORDER NOT SPECIFIED")

        if sell_order.order_kind == "market" or buy_order == "market":
            return True

        return buy_order.order_price >= sell_order.order_price

    def execute_trade(self, buy_order, sell_order):
        trade_quantity = min(buy_order.quantity, sell_order.quantity)

        if trade_quantity <= 0:
            return None

        trade_price = self.get_trade_price(buy_order=buy_order, sell_order=sell_order)

        buy_order.quantity -= trade_quantity
        sell_order.quantity -= trade_quantity

        if buy_order.quantity == 0 and buy_order.order_id in self.order_book.order_id_map:
            self.order_book.cancel_order(order_id=buy_order.order_id)
        if sell_order.quantity == 0 and buy_order.order_id in self.order_book.order_id_map:
            self.order_book.cancel_order(order_id=sell_order.order_id)

        trade = Trade(trade_id=str(len(self.trades)),
                      buyer_order_id=buy_order.order_id,
                      seller_order_id=sell_order.order_id,
                      price=trade_price,
                      quantity=trade_quantity,
                      instrument="stock")

        self.trades.append(trade)

        return trade

    def get_trade_price(self, buy_order, sell_order):
        if buy_order.order_kind == "market":
            return sell_order.order_price
        if sell_order.order_kind == "market":
            return buy_order.order_price

        if buy_order.timestamp > sell_order.timestamp:
            return sell_order.order_price
        else:
            return buy_order.order_price
