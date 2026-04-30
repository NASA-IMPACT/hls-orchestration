"""
HLS: LAADS Availability Alert

Scheduled Lambda that checks whether LAADS auxiliary data is available in S3
for the recent past (configurable lookback window, default 14 days). Sends a
Slack alert when data is missing and a recovery alert when data reappears after
an outage. State is persisted in SSM Parameter Store to enable recovery detection
and alert throttling.

The check can run frequently (e.g. every 30 minutes) but "missing" alerts are
throttled to at most once every LAADS_ALERT_INTERVAL_HOURS hours. Recovery
alerts fire immediately regardless of the throttle.

Environment variables:
  LAADS_BUCKET                - S3 bucket containing LAADS auxiliary data
  HLS_SLACK_ALERT_WEBHOOK     - Slack incoming webhook URL (optional; skips alerting if unset)
  LAADS_ALERT_STATE_SSM_PATH  - SSM parameter path for persisting outage state
  LAADS_LOOKBACK_DAYS         - Number of days back to check (default: 14)
  LAADS_ALERT_INTERVAL_HOURS  - Min hours between repeated "missing" alerts (default: 12)
  LAADS_LAG_HOURS             - Expected publication lag in hours (default: 30 = 24h lag + 6h
                                buffer). The most recent date checked is today minus this lag,
                                so we don't false-alert on data that simply hasn't been published
                                yet.
  STACKNAME                   - Deployment stage name (e.g. dev / prod), included in alert text.
"""

import dataclasses
import json
import os
import urllib.request
from dataclasses import dataclass, field
import datetime as dt
from typing import Literal

import boto3
from botocore.exceptions import ClientError

from hls_lambda_layer.laads_utils import check_laads_for_date

ssm = boto3.client("ssm")


@dataclass
class AlertState:
    status: Literal["available", "missing"] = "available"
    last_alert_sent: dt.datetime | None = None  # UTC datetime of last Slack post
    missing_since: str | None = (
        None  # yyyy-mm-dd of first missing day in current outage
    )
    missing_days: list[str] = field(default_factory=list)  # yyyy-mm-dd, newest-first


def _get_state(ssm_path: str) -> AlertState:
    """Read alert state from SSM. Returns a default AlertState if the parameter doesn't exist yet."""
    try:
        response = ssm.get_parameter(Name=ssm_path, WithDecryption=False)
        data = json.loads(response["Parameter"]["Value"])
        if data.get("last_alert_sent"):
            data["last_alert_sent"] = dt.datetime.fromisoformat(data["last_alert_sent"])
        return AlertState(**data)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            return AlertState()
        raise


def _put_state(ssm_path: str, state: AlertState) -> None:
    """Persist alert state to SSM."""

    def _serialize(obj):
        if isinstance(obj, dt.datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    ssm.put_parameter(
        Name=ssm_path,
        Value=json.dumps(dataclasses.asdict(state), default=_serialize),
        Type="String",
        Overwrite=True,
    )


def _post_slack(webhook_url: str, message: str) -> None:
    """Send a plain text message to a Slack incoming webhook."""
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"Slack response: {resp.status}")


def _check_recent_availability(
    bucket: str, lookback: dt.timedelta, lag: dt.timedelta
) -> list[str]:
    """Check LAADS availability for the past lookback period, accounting for
    the provider's publication lag.

    The most recent date checked is (now - lag), so we don't false-alert on
    data that simply hasn't been published yet (LAADS publishes with ~24h lag).

    Returns a list of date strings (yyyy-mm-dd) for which data is missing,
    ordered newest-first.
    """
    anchor = (dt.datetime.now(tz=dt.timezone.utc) - lag).date()
    missing = []
    for offset in range(lookback.days):
        check_date = anchor - dt.timedelta(days=offset)
        date_str = check_date.strftime("%Y-%m-%d")
        available, _ = check_laads_for_date(bucket, date_str)
        if not available:
            missing.append(date_str)
    return missing


def _alert_due(state: AlertState, alert_interval: dt.timedelta) -> bool:
    """Return True if enough time has passed since the last "missing" alert."""
    if state.last_alert_sent is None:
        return True
    return dt.datetime.now(tz=dt.timezone.utc) - state.last_alert_sent >= alert_interval


def _handle_outage(
    state: AlertState,
    missing_days: list[str],
    lookback: dt.timedelta,
    alert_interval: dt.timedelta,
    now: dt.datetime,
    webhook_url: str | None,
    stackname: str,
) -> tuple[AlertState, bool]:
    new_state = AlertState(
        status="missing",
        missing_since=state.missing_since or missing_days[0],
        missing_days=missing_days,
        last_alert_sent=state.last_alert_sent,
    )
    if not _alert_due(state, alert_interval):
        print(
            f"LAADS data still missing but alert throttled (last sent: {state.last_alert_sent})."
        )
        return new_state, False

    message = (
        f":warning: [{stackname}] LAADS data is missing for {len(missing_days)} day(s) "
        f"within the past {lookback.days} days. "
        f"Missing dates: {', '.join(sorted(missing_days))}."
    )
    print(message)
    new_state.last_alert_sent = now
    if webhook_url:
        _post_slack(webhook_url, message)
    return new_state, True


def _handle_recovery_or_ok(
    state: AlertState,
    lookback: dt.timedelta,
    now: dt.datetime,
    webhook_url: str | None,
    stackname: str,
) -> tuple[AlertState, bool]:
    new_state = AlertState(status="available", last_alert_sent=now)
    if state.status != "missing":
        print(
            f"LAADS data is available for all {lookback.days} days checked. No alert needed."
        )
        return new_state, False

    message = (
        f":white_check_mark: [{stackname}] LAADS data has recovered. "
        f"Data was missing since {state.missing_since or 'unknown'}."
    )
    print(message)
    if webhook_url:
        _post_slack(webhook_url, message)
    return new_state, True


def handler(event: dict, context: dict) -> dict:
    """AWS Lambda handler."""
    bucket = os.environ["LAADS_BUCKET"]
    webhook_url: str | None = os.getenv("HLS_SLACK_ALERT_WEBHOOK") or None
    ssm_path = os.environ["LAADS_ALERT_STATE_SSM_PATH"]
    stackname = os.environ["STACKNAME"]
    lookback = dt.timedelta(days=int(os.getenv("LAADS_LOOKBACK_DAYS", "14")))
    alert_interval = dt.timedelta(
        hours=int(os.getenv("LAADS_ALERT_INTERVAL_HOURS", "12"))
    )
    lag = dt.timedelta(hours=int(os.getenv("LAADS_LAG_HOURS", "30")))

    missing_days = _check_recent_availability(bucket, lookback, lag)
    state = _get_state(ssm_path)
    now = dt.datetime.now(tz=dt.timezone.utc)

    if missing_days:
        new_state, alerted = _handle_outage(
            state, missing_days, lookback, alert_interval, now, webhook_url, stackname
        )
    else:
        new_state, alerted = _handle_recovery_or_ok(
            state, lookback, now, webhook_url, stackname
        )

    _put_state(ssm_path, new_state)
    return {
        "missing_days": missing_days,
        "previous_status": state.status,
        "alerted": alerted,
    }
