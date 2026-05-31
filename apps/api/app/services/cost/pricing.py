from decimal import Decimal

_FALLBACK_PRICES: dict[str, dict[str, Decimal]] = {
    "us-east-1": {
        "t3.micro": Decimal("0.0104"),
        "t3.small": Decimal("0.0208"),
        "t3.medium": Decimal("0.0416"),
        "t3.large": Decimal("0.0832"),
    },
    "us-west-2": {
        "t3.micro": Decimal("0.0104"),
        "t3.medium": Decimal("0.0416"),
    },
}


def get_hourly_price(region: str, instance_type: str) -> Decimal:
    """Return on-demand hourly price. Falls back to static table if awspricing fails."""
    try:
        import awspricing  # type: ignore[import]
        offer = awspricing.offer("AmazonEC2")
        price = offer.ondemand_price(
            instance_type=instance_type,
            region=region,
            operating_system="Linux",
            tenancy="Shared",
        )
        return Decimal(str(price))
    except Exception:
        region_prices = _FALLBACK_PRICES.get(region, _FALLBACK_PRICES["us-east-1"])
        return region_prices.get(instance_type, Decimal("0.05"))


def estimate_monthly_cost(region: str, instance_type: str, hours: float = 730.0) -> Decimal:
    hourly = get_hourly_price(region, instance_type)
    return (hourly * Decimal(str(hours))).quantize(Decimal("0.01"))
