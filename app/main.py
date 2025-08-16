from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from trading_system.trading_system_storage import TradingSystem, OrderBookError
from trading_system.order_book import Order
from trading_system.portfolio import Position



class OrderRequest(BaseModel):
    ticker: str
    side: str
    order_price: float
    quantity: int
    order_kind: str = "limit"


class TradeRequest(BaseModel):
    ticker: str
    position_type: Literal["long", "short"]
    close_open: Literal["open", "close"]
    quantity: float
    price: float
    commission: float = 0.001


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
        # Load order book based on request ticker
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
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"FAILED TO SUBMIT ORDER: {str(e)}"
        )


@app.post("/portfolio/{portfolio_id}/trade-requests")
def portfolio_trade_request(portfolio_id: str, trade_request: TradeRequest):
    try:
        portfolio = trading_system.load_portfolio(portfolio_id=portfolio_id)

        portfolio.request_trade(
            ticker=trade_request.ticker,
            position_type=trade_request.position_type,
            close_open=trade_request.close_open,
            quantity=trade_request.quantity,
            price=trade_request.price,
            commission=trade_request.commission
        )

        trading_system.save_portfolio(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "trade_request": trade_request.dict(),
            "queue_size": len(portfolio.trade_requests)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"PORTFOLIO FAILED TO REQUEST TRADE: {e}")

@app.post("/portfolio/{portfolio_id}/process-trades")
def process_portfolio_trade_requests(portfolio_id: str):
    try:
        portfolio = trading_system.load_portfolio(portfolio_id=portfolio_id)

        if len(portfolio.trade_requests) == 0:
            return {
                "message": f"PORTFOLIO {portfolio_id} HAS NO TRADE REQUESTS",
                "portfolio_id": portfolio_id
            }

        # Process trade requests and track how many requests processed
        requests_count_before = len(portfolio.trade_requests)
        trading_system.process_trade_request(portfolio)
        requests_count_after = len(portfolio.trade_requests)

        # Save portfolio
        trading_system.save_portfolio(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "requests_processed": requests_count_before - requests_count_after,
            "remaining_requests": len(portfolio.trade_requests)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FAILED TO PROCESS PORTFOLIO {portfolio_id} TRADE REQUESTS: {str(e)}"
        )
@app.post("/system/process-all-trades")
def process_all_portfolio_trades():
    try:
        total_processed_requests = 0
        results = {}
        fully_processed_portfolio_count = 0

        for portfolio_id, portfolio in trading_system.portfolios.items():
            request_count = len(portfolio.trade_requests)

            if request_count > 0:

                # Process trade requests of current portfolio
                trading_system.process_trade_request(portfolio=portfolio)

                # Calculate number of successfully processed requests
                new_request_count = len(portfolio.trade_requests)
                request_processed_count = request_count - new_request_count

                # Store number of successfully processed requests
                results[portfolio_id] = {
                    "requests_processed": request_processed_count,
                }

                total_processed_requests += request_processed_count

                if new_request_count == 0:
                    fully_processed_portfolio_count += 1

        # Save new trading system state
        trading_system.save_all()

        return {
            "fully_processed_portfolios": fully_processed_portfolio_count,
            "partially_processed_portfolios": len(trading_system.portfolios) - fully_processed_portfolio_count,
            "total_requests_processed": total_processed_requests,
            "portfolio_results": results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FAILED TO PROCESS PORTFOLIOS"
        )


@app.post("/orderbook/sample/{ticker}")
def create_sample_order_book(ticker: str, num_orders: int = 10000):
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

    return {"message": f"ADDED {2 * num_orders} ORDERS TO {ticker}"}
