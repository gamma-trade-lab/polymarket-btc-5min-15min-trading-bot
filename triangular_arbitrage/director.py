from dataclasses import dataclass
from typing import List, Optional

import triangular_arbitrage.detector as detector


@dataclass
class DirectorConfig:
    exchange_name: str
    max_cycle: int = 3
    taker_fee_bps: float = 10.0
    slippage_bps: float = 5.0
    min_net_profit_bps: float = 15.0


@dataclass
class TradeDecision:
    should_trade: bool
    reason: str
    gross_profit_multiplier: float
    net_profit_multiplier: float
    expected_net_profit_bps: float
    opportunities: Optional[List[detector.ShortTicker]]


class TradingLogicDirector:
    """
    A thin decision layer that turns raw cycle detection into a trade decision.
    It protects the strategy from blindly chasing gross edges that vanish after costs.
    """

    def __init__(self, config: DirectorConfig):
        self.config = config

    async def evaluate(self) -> TradeDecision:
        opportunities, gross_profit = await detector.run_detection(
            self.config.exchange_name,
            max_cycle=self.config.max_cycle,
        )
        return self._decide(opportunities, gross_profit)

    def _decide(
        self,
        opportunities: Optional[List[detector.ShortTicker]],
        gross_profit: float,
    ) -> TradeDecision:
        if opportunities is None:
            return TradeDecision(
                should_trade=False,
                reason="No closed arbitrage cycle detected.",
                gross_profit_multiplier=1.0,
                net_profit_multiplier=1.0,
                expected_net_profit_bps=0.0,
                opportunities=None,
            )

        net_profit = self._estimate_net_profit(gross_profit, len(opportunities))
        net_profit_bps = (net_profit - 1.0) * 10_000

        if net_profit_bps < self.config.min_net_profit_bps:
            return TradeDecision(
                should_trade=False,
                reason=(
                    "Net edge below threshold after costs "
                    f"({net_profit_bps:.2f} bps < {self.config.min_net_profit_bps:.2f} bps)."
                ),
                gross_profit_multiplier=gross_profit,
                net_profit_multiplier=net_profit,
                expected_net_profit_bps=net_profit_bps,
                opportunities=opportunities,
            )

        return TradeDecision(
            should_trade=True,
            reason="Net edge clears threshold.",
            gross_profit_multiplier=gross_profit,
            net_profit_multiplier=net_profit,
            expected_net_profit_bps=net_profit_bps,
            opportunities=opportunities,
        )

    def _estimate_net_profit(self, gross_profit_multiplier: float, legs_count: int) -> float:
        cost_per_leg = (self.config.taker_fee_bps + self.config.slippage_bps) / 10_000
        cost_multiplier_per_leg = max(0.0, 1.0 - cost_per_leg)
        return gross_profit_multiplier * (cost_multiplier_per_leg ** legs_count)


def format_opportunity_legs(opportunities: List[detector.ShortTicker]) -> List[str]:
    formatted = []
    for i, opportunity in enumerate(opportunities, start=1):
        base_currency = opportunity.symbol.base
        quote_currency = opportunity.symbol.quote
        order_side = "buy" if opportunity.reversed else "sell"
        relation = "with" if order_side == "buy" else "for"
        formatted.append(
            f"{i}. {order_side} {base_currency} {relation} {quote_currency} at {opportunity.last_price:.5f}"
        )
    return formatted
