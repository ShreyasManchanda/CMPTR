from dataclasses import dataclass
from typing import Optional
from pricing.pricing_engine import Recommendation


@dataclass(frozen=True)
class FinalAction:
    product_id: str
    final_action: str
    suggested_price: Optional[float]
    confidence: float
    policy_reason: str

class RulesAgent:

    def __init__(
        self,
        min_confidence_to_act: float = 0.6,
        allow_auto_reduce: bool = False,
        allow_auto_increase: bool = False,
    ):

        self.min_confidence_to_act = min_confidence_to_act
        self.allow_auto_reduce = allow_auto_reduce
        self.allow_auto_increase = allow_auto_increase

    def decide(self, recommendation: Recommendation) -> FinalAction:

        if recommendation.action == "manual_review":
            return FinalAction(
                product_id=recommendation.product_id,
                final_action="manual_review",
                suggested_price=None,
                confidence=recommendation.rec_confidence,
                policy_reason=recommendation.reason
            )

        if recommendation.rec_confidence < self.min_confidence_to_act:
            return FinalAction(
                product_id=recommendation.product_id,
                final_action="manual_review",
                suggested_price=None,
                confidence=recommendation.rec_confidence,
                policy_reason="confidence_below_policy_threshold"
            )

        if recommendation.action == "reduce":
            if not self.allow_auto_reduce:
                return FinalAction(
                    product_id=recommendation.product_id,
                    final_action="reduce",
                    suggested_price=recommendation.suggested_price,
                    confidence=recommendation.rec_confidence,
                    policy_reason="requires_human_approval"
                )

        if recommendation.action == "increase":
            if not self.allow_auto_increase:
                return FinalAction(
                    product_id=recommendation.product_id,
                    final_action="increase",
                    suggested_price=recommendation.suggested_price,
                    confidence=recommendation.rec_confidence,
                    policy_reason="requires_human_approval"
                )

        return FinalAction(
            product_id=recommendation.product_id,
            final_action=recommendation.action,
            suggested_price=recommendation.suggested_price,
            confidence=recommendation.rec_confidence,
            policy_reason="allowed_by_policy"
        )
