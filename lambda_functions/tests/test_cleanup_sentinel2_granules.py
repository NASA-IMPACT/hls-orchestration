from unittest.mock import patch
import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("SENTINEL_INPUT_BUCKET", "sentinelinput")


@pytest.fixture
def mock_delete_object():
    from lambda_functions.cleanup_sentinel2_granules import s3

    with patch.object(s3, "delete_object") as mock_delete_object:
        yield mock_delete_object


def test_single_granule_case(mock_delete_object, capsys):
    from lambda_functions.cleanup_sentinel2_granules import handler, s3

    with patch.object(
        s3,
        "list_objects_v2",
        return_value={"Contents": [{"Key": "one.zip"}]},
    ):
        handler({"granule": "one12345"}, {})
        assert mock_delete_object.call_count == 1

    captured = capsys.readouterr()
    assert "Deleting input of single granule case" in captured.out


def test_twin_granule_only_one_skip_delete(mock_delete_object, capsys):
    from lambda_functions.cleanup_sentinel2_granules import handler, s3

    with patch.object(
        s3,
        "list_objects_v2",
        return_value={"Contents": [{"Key": "one.zip"}, {"Key": "two.zip"}]},
    ):
        handler({"granule": "one12345"}, {})
        mock_delete_object.assert_not_called()

    captured = capsys.readouterr()
    assert (
        "Twin granule case detected but this workflow did not process it. Skipping"
        in captured.out
    )


def test_twin_granule_has_both_deletes_both(mock_delete_object, capsys):
    from lambda_functions.cleanup_sentinel2_granules import handler, s3

    with patch.object(
        s3,
        "list_objects_v2",
        return_value={"Contents": [{"Key": "one.zip"}, {"Key": "two.zip"}]},
    ):
        handler({"granule": "one12345_111111,one12345_222222"}, {})
        assert mock_delete_object.call_count == 2

    captured = capsys.readouterr()
    assert "Deleting inputs of twin granule case" in captured.out


def test_bad_granule_id_inputs(mock_delete_object):
    from lambda_functions.cleanup_sentinel2_granules import handler, s3

    with (
        patch.object(
            s3,
            "list_objects_v2",
            return_value={"Contents": [{"Key": "one.zip"}, {"Key": "two.zip"}]},
        ) as mock_list_objects,
        pytest.raises(ValueError, match=r"Received 2 granule prefixes"),
    ):
        handler({"granule": "thisiswronggranuleid,obviouslynotagranuleid"}, {})
        mock_list_objects.assert_not_called()
        mock_delete_object.assert_not_called()
