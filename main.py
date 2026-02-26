import asyncio
import os
# allow minimal octobot_commons imports
os.environ["USE_MINIMAL_LIBS"] = "true"

import octobot_commons.os_util as os_util

from triangular_arbitrage.director import (
    DirectorConfig,
    TradingLogicDirector,
    format_opportunity_legs,
)

if __name__ == "__main__":
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Windows handles asynchronous event loops

    benchmark = os_util.parse_boolean_environment_var("IS_BENCHMARKING", "False")
    if benchmark:
        import time

        s = time.perf_counter()

    # Conscious strategy defaults
    print("Scanning...")
    config = DirectorConfig(
        exchange_name="bitget",  # use any ccxt exchange id
        max_cycle=3,             # triangular by default
        taker_fee_bps=10.0,      # 0.10%
        slippage_bps=5.0,        # 0.05%
        min_net_profit_bps=15.0, # require >= 0.15% after costs
    )

    director = TradingLogicDirector(config)
    decision = asyncio.run(director.evaluate())

    if decision.opportunities is not None:
        print("-------------------------------------------")
        gross_profit_percentage = (decision.gross_profit_multiplier - 1) * 100
        net_profit_percentage = (decision.net_profit_multiplier - 1) * 100
        print(f"Best gross cycle on {config.exchange_name}: {gross_profit_percentage:.5f}%")
        print(f"Expected net edge after costs: {net_profit_percentage:.5f}%")
        print(f"Decision: {'TRADE' if decision.should_trade else 'SKIP'} ({decision.reason})")
        for line in format_opportunity_legs(decision.opportunities):
            print(line)
        print("-------------------------------------------")
    else:
        print(f"Decision: SKIP ({decision.reason})")

    if benchmark:
        elapsed = time.perf_counter() - s
        print(f"{__file__} executed in {elapsed:0.2f} seconds.")
