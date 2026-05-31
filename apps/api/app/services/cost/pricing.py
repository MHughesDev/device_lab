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


def get_ebs_snapshot_price_per_gb_month(region: str) -> Decimal:
    """Return EBS snapshot storage price per GB-month. Falls back to $0.05 if awspricing fails."""
    try:
        import awspricing  # type: ignore[import]
        offer = awspricing.offer("AmazonEC2")
        price = offer.storage_price(
            storage_type="Amazon EBS Snapshots to Amazon S3",
            region=region,
        )
        return Decimal(str(price))
    except Exception:
        return Decimal("0.05")


def get_data_transfer_price_per_gb(region: str) -> Decimal:
    """Return outbound data transfer price per GB for the region."""
    try:
        import awspricing  # type: ignore[import]
        offer = awspricing.offer("AWSDataTransfer")
        price = offer.data_transfer_price(region=region, transfer_type="DataTransfer-Out-Bytes")
        return Decimal(str(price))
    except Exception:
        return Decimal("0.09")


def estimate_snapshot_cost(region: str, size_gb: float, retention_days: int = 30) -> Decimal:
    """Estimate cost for keeping a snapshot for retention_days."""
    price_per_gb_month = get_ebs_snapshot_price_per_gb_month(region)
    months = Decimal(str(retention_days)) / Decimal("30")
    return (price_per_gb_month * Decimal(str(size_gb)) * months).quantize(Decimal("0.01"))
