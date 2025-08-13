from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from trading_system.trading_system_storage import TradingSystem, OrderBookError
from trading_system.order_book import Order


class OrderRequest(BaseModel):
    ticker: str
    side: str
    order_price: float
    quantity: int
    order_kind: str = "limit"


class TradeRequest(BaseModel):
    ticker: str
    side: str
    price: float
    quantity: int
    close_open: str


app = FastAPI(title="Trading system")
trading_system = TradingSystem()


@app.get("/portfolio/{portfolio_id}")
def get_portfolio(portfolio_id: str):
    try:
        # Load portfolio
        portfolio = trading_system.load_portfolio(portfolio_id=portfolio_id)

        # Get the quantities of each position in the portfolio
        positions = {ticker: position.quantity for ticker, position in portfolio.positions.items()}

        return {
            "portfolio_id": portfolio_id,
            "portfolio_cash": portfolio.cash,
            "commission_rate": portfolio.commission_rate,
            "current_positions": positions,
            "total_value": portfolio.total_portfolio_value
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PORTFOLIO NOT FOUND: {e}")


@app.get("/orderbook/{ticker}")
def get_order_book(ticker: str):
    # Load order book and values of interest
    order_book = trading_system.load_order_book(ticker=ticker)
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()

    return {
        "ticker": ticker,
        "best_bid": best_bid.order_price if best_bid else None,
        "best_ask": best_ask.order_price if best_ask else None,
        "spread": order_book.get_spread(),
        "total_orders": len(order_book.order_id_map),
        "trades_executed": len(order_book.trades)
    }


@app.post("/portfolio/{portfolio_id}/orders")
def submit_order(portfolio_id: str, order_request: OrderRequest):
    try:
        # Load order book
        order_book = trading_system.load_order_book(order_request.ticker)

        # Create order
        order_id = f"{portfolio_id}_{len(order_book.order_id_map)}"
        order = Order(
            order_id=order_id,
            ticker=order_request.ticker,
            side=order_request.side,
            order_price=order_request.order_price,
            quantity=order_request.quantity,
            portfolio_id=portfolio_id,
            order_kind=order_request.order_kind
        )

        # Find a match for order
        original_quantity = order.quantity
        trading_system.matching_engine.process_order(order=order, order_book=order_book)
        quantity_executed = original_quantity - order.quantity

        return {
            "order_id": order_id,
            "status": "submitted",
            "original_quantity": original_quantity,
            "quantity_executed": quantity_executed,
            "quantity_remaining": order.quantity,
            "message": f"Order submitted successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit order: {str(e)}"
        )


@app.post("/portfolio/{portfolio_id}/trade-requests")
def submit_trade_request(portfolio_id: str, trade_request: TradeRequest):
    pass


@app.post("/portfolio/{portfolio_id}/process-trades")
def process_trade_requests(portfolio_id: str):
    pass



@app.post("/orderbook/test/{ticker}")
def create_test_order_book(ticker: str, num_orders: int = 10000):
    import random

    order_book = trading_system.load_order_book(ticker=ticker)
    base_price = 100

    for i in range(num_orders):
        side = "bid"
        price = base_price + random.uniform(-1.0, 1.0)

        order = Order(
            order_id=f"DEMO_{i}",
            ticker=ticker,
            side=side,
            order_price=round(price, 2),
            quantity=random.randint(10, 100),
            portfolio_id="DEMO",
            order_kind="limit"
        )

        order_book.add_order(order)

    for i in range(num_orders):
        side = "ask"
        price = base_price + random.uniform(-1.0, 1.0)

        order = Order(
            order_id=f"TEST_{i}",
            ticker=ticker,
            side=side,
            order_price=round(price, 2),
            quantity=random.randint(10, 100),
            portfolio_id="TEST",
            order_kind="limit"
        )

        order_book.add_order(order)

    return {"message": f"Added {2 * num_orders} orders to {ticker}"}
