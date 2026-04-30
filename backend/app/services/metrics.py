import asyncio
from datetime import datetime, timezone

# Global metrics store
metrics = {
    "total_signals": 0,
    "signals_last_window": 0,
    "window_start": datetime.now(timezone.utc),
    "debounced_count": 0,
    "rate_limited_count": 0,
}


def record_signal():
    metrics["total_signals"] += 1
    metrics["signals_last_window"] += 1


def record_debounced():
    metrics["debounced_count"] += 1


def record_rate_limited():
    metrics["rate_limited_count"] += 1


async def print_throughput_metrics():
    while True:
        await asyncio.sleep(5)
        now = datetime.now(timezone.utc)
        elapsed = (now - metrics["window_start"]).total_seconds()
        signals_per_sec = round(metrics["signals_last_window"] / max(elapsed, 1), 2)

        print(f"""
========== IMS THROUGHPUT METRICS ==========
Time              : {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
Signals/sec       : {signals_per_sec}
Total signals     : {metrics["total_signals"]}
Debounced signals : {metrics["debounced_count"]}
Rate limited      : {metrics["rate_limited_count"]}
=============================================
        """)

        # Reset window
        metrics["signals_last_window"] = 0
        metrics["window_start"] = now
