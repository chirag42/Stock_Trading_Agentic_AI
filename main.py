from core.scheduler import Scheduler
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="ollama", choices=["ollama", "claude"])
    args = parser.parse_args()
    scheduler = Scheduler(
        watchlist=["AAPL", "MSFT", "TSLA"],
        poll_interval=300,  # 5 minutes
        backend=args.backend
    )

    # respect_market_hours=False lets you test any time of day
    scheduler.start(respect_market_hours=False)