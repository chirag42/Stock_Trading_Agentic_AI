from core.scheduler import Scheduler

if __name__ == "__main__":
    scheduler = Scheduler(
        watchlist=["AAPL", "MSFT", "TSLA"],
        poll_interval=300  # 5 minutes
    )

    # respect_market_hours=False lets you test any time of day
    scheduler.start(respect_market_hours=False)