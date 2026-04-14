import json
import datetime as dt
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from lambda_functions.laads_alert import _check_recent_availability, handler


BUCKET = "test-laads-bucket"
SSM_PATH = "/test-stack/laads-alert-state"
WEBHOOK = "https://hooks.slack.example.com/test"


def _make_ssm_response(state: dict):
    return {"Parameter": {"Value": json.dumps(state)}}


def _iso_hours_ago(hours: float) -> str:
    return (dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=hours)).isoformat()


@pytest.fixture
def laads_env(monkeypatch):
    monkeypatch.setenv("LAADS_BUCKET", BUCKET)
    monkeypatch.setenv("LAADS_ALERT_STATE_SSM_PATH", SSM_PATH)
    monkeypatch.setenv("LAADS_LOOKBACK_DAYS", "3")
    monkeypatch.setenv("LAADS_ALERT_INTERVAL_HOURS", "12")
    monkeypatch.setenv("LAADS_LAG_HOURS", "30")


@patch("lambda_functions.laads_alert.ssm")
@patch("hls_lambda_layer.laads_utils.s3")
def test_all_available_no_prior_outage(mock_s3, mock_ssm, laads_env):
    """All data present, SSM shows available → no Slack message."""
    mock_s3.list_objects_v2.return_value = {"Contents": ["key"]}
    mock_ssm.get_parameter.return_value = _make_ssm_response({"status": "available"})

    result = handler({}, {})

    assert result["missing_days"] == []
    assert result["previous_status"] == "available"
    assert result["alerted"] is False
    saved = json.loads(mock_ssm.put_parameter.call_args[1]["Value"])
    assert saved["status"] == "available"


@patch("lambda_functions.laads_alert.ssm")
@patch("lambda_functions.laads_alert._post_slack")
@patch("hls_lambda_layer.laads_utils.s3")
def test_missing_data_sends_alert(
    mock_s3, mock_post_slack, mock_ssm, laads_env, monkeypatch
):
    """Data missing, no prior alert → Slack alert sent, SSM updated."""
    monkeypatch.setenv("HLS_SLACK_ALERT_WEBHOOK", WEBHOOK)

    mock_s3.list_objects_v2.return_value = {}
    mock_ssm.get_parameter.return_value = _make_ssm_response({"status": "available"})

    result = handler({}, {})

    assert len(result["missing_days"]) == 3
    assert result["alerted"] is True
    mock_post_slack.assert_called_once()
    assert "missing" in mock_post_slack.call_args[0][1].lower()

    saved = json.loads(mock_ssm.put_parameter.call_args[1]["Value"])
    assert saved["status"] == "missing"
    assert "missing_since" in saved
    assert "last_alert_sent" in saved


@patch("lambda_functions.laads_alert.ssm")
@patch("lambda_functions.laads_alert._post_slack")
@patch("hls_lambda_layer.laads_utils.s3")
def test_missing_alert_throttled(
    mock_s3, mock_post_slack, mock_ssm, laads_env, monkeypatch
):
    """Data still missing, alert sent recently → throttled, no Slack call."""
    monkeypatch.setenv("HLS_SLACK_ALERT_WEBHOOK", WEBHOOK)

    mock_s3.list_objects_v2.return_value = {}
    mock_ssm.get_parameter.return_value = _make_ssm_response(
        {
            "status": "missing",
            "missing_since": "2026-04-13",
            "last_alert_sent": _iso_hours_ago(1),  # sent 1 hour ago, interval is 12h
        }
    )

    result = handler({}, {})

    assert len(result["missing_days"]) == 3
    assert result["alerted"] is False
    mock_post_slack.assert_not_called()


@patch("lambda_functions.laads_alert.ssm")
@patch("lambda_functions.laads_alert._post_slack")
@patch("hls_lambda_layer.laads_utils.s3")
def test_missing_alert_fires_after_interval(
    mock_s3, mock_post_slack, mock_ssm, laads_env, monkeypatch
):
    """Data still missing, last alert was >12h ago → alert fires again."""
    monkeypatch.setenv("HLS_SLACK_ALERT_WEBHOOK", WEBHOOK)

    mock_s3.list_objects_v2.return_value = {}
    mock_ssm.get_parameter.return_value = _make_ssm_response(
        {
            "status": "missing",
            "missing_since": "2026-04-13",
            "last_alert_sent": _iso_hours_ago(13),  # sent 13 hours ago
        }
    )

    result = handler({}, {})

    assert result["alerted"] is True
    mock_post_slack.assert_called_once()


@patch("lambda_functions.laads_alert.ssm")
@patch("lambda_functions.laads_alert._post_slack")
@patch("hls_lambda_layer.laads_utils.s3")
def test_recovery_sends_immediately(
    mock_s3, mock_post_slack, mock_ssm, laads_env, monkeypatch
):
    """Data recovered after outage → Slack recovery alert sent immediately, ignores throttle."""
    monkeypatch.setenv("HLS_SLACK_ALERT_WEBHOOK", WEBHOOK)

    mock_s3.list_objects_v2.return_value = {"Contents": ["key"]}
    mock_ssm.get_parameter.return_value = _make_ssm_response(
        {
            "status": "missing",
            "missing_since": "2026-04-10",
            "last_alert_sent": _iso_hours_ago(1),  # recent alert — recovery still fires
        }
    )

    result = handler({}, {})

    assert result["missing_days"] == []
    assert result["previous_status"] == "missing"
    assert result["alerted"] is True
    mock_post_slack.assert_called_once()
    assert "recovered" in mock_post_slack.call_args[0][1].lower()

    saved = json.loads(mock_ssm.put_parameter.call_args[1]["Value"])
    assert saved["status"] == "available"


@patch("lambda_functions.laads_alert.ssm")
@patch("lambda_functions.laads_alert._post_slack")
@patch("hls_lambda_layer.laads_utils.s3")
def test_no_webhook_skips_slack(mock_s3, mock_post_slack, mock_ssm, laads_env):
    """Missing data but no webhook configured → no Slack call."""
    mock_s3.list_objects_v2.return_value = {}
    mock_ssm.get_parameter.return_value = _make_ssm_response({"status": "available"})

    result = handler({}, {})

    assert len(result["missing_days"]) == 3
    mock_post_slack.assert_not_called()


@patch("lambda_functions.laads_alert.ssm")
@patch("hls_lambda_layer.laads_utils.s3")
def test_lag_anchor_date(mock_s3, mock_ssm, laads_env):
    """The most recent date checked respects the lag — not today's date."""
    checked_dates = []

    def fake_list(Bucket, Prefix):
        checked_dates.append(Prefix)
        return {"Contents": ["key"]}

    mock_s3.list_objects_v2.side_effect = fake_list

    _check_recent_availability(
        BUCKET, lookback=dt.timedelta(days=3), lag=dt.timedelta(hours=30)
    )

    today_ydoy = dt.date.today().strftime("%Y%j")
    assert not any(
        today_ydoy in p for p in checked_dates
    ), f"Today ({today_ydoy}) should not be checked due to lag; got {checked_dates}"


@patch("lambda_functions.laads_alert.ssm")
@patch("hls_lambda_layer.laads_utils.s3")
def test_ssm_not_found_treated_as_available(mock_s3, mock_ssm, laads_env):
    """SSM parameter missing on first run → treated as previously available."""
    mock_s3.list_objects_v2.return_value = {"Contents": ["key"]}
    error_response = {"Error": {"Code": "ParameterNotFound", "Message": "not found"}}
    mock_ssm.get_parameter.side_effect = ClientError(error_response, "GetParameter")

    result = handler({}, {})

    assert result["previous_status"] == "available"
    assert result["missing_days"] == []
