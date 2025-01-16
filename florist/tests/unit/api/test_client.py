"""Tests for FLorist's client FastAPI endpoints."""
import json
import os
import signal
from unittest.mock import ANY, Mock, patch

from florist.api import client
from florist.api.clients.mnist import MnistClient
from florist.api.monitoring.logs import get_client_log_file_path
from florist.api.monitoring.metrics import RedisMetricsReporter


def test_connect() -> None:
    """Tests the client's connect endpoint."""
    response = client.connect()

    assert response.status_code == 200
    json_body = json.loads(response.body.decode())
    assert json_body == {"status": "ok"}


@patch("florist.api.client.launch_client")
def test_start_success(mock_launch_client: Mock) -> None:
    test_server_address = "test-server-address"
    test_client = "MNIST"
    test_data_path = "test/data/path"
    test_redis_host = "test-redis-host"
    test_redis_port = "test-redis-port"
    test_client_pid = 1234

    mock_client_process = Mock()
    mock_client_process.pid = test_client_pid
    mock_launch_client.return_value = mock_client_process

    response = client.start(test_server_address, test_client, test_data_path, test_redis_host, test_redis_port)

    assert response.status_code == 200
    json_body = json.loads(response.body.decode())
    log_file_path = str(get_client_log_file_path(json_body["uuid"]))
    assert json_body == {"uuid": ANY, "pid": str(test_client_pid), "log_file_path": log_file_path}

    mock_launch_client.assert_called_once_with(ANY, test_server_address, log_file_path)

    client_obj = mock_launch_client.call_args_list[0][0][0]
    assert isinstance(client_obj, MnistClient)
    assert str(client_obj.data_path) == test_data_path

    metrics_reporter = client_obj.reports_manager.reporters[0]
    assert isinstance(metrics_reporter, RedisMetricsReporter)
    assert metrics_reporter.host == test_redis_host
    assert metrics_reporter.port == test_redis_port
    assert metrics_reporter.run_id == json_body["uuid"]


def test_start_fail_unsupported_client() -> None:
    test_server_address = "test-server-address"
    test_client = "WRONG"
    test_data_path = "test/data/path"
    test_redis_host = "test-redis-host"
    test_redis_port = "test-redis-port"

    response = client.start(test_server_address, test_client, test_data_path, test_redis_host, test_redis_port)

    assert response.status_code == 400
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": ANY}
    assert f"Client '{test_client}' not supported" in json_body["error"]


@patch("florist.api.client.launch_client", side_effect=Exception("test exception"))
def test_start_fail_exception(_: Mock) -> None:
    test_server_address = "test-server-address"
    test_client = "MNIST"
    test_data_path = "test/data/path"
    test_redis_host = "test-redis-host"
    test_redis_port = "test-redis-port"

    response = client.start(test_server_address, test_client, test_data_path, test_redis_host, test_redis_port)

    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": "test exception"}


@patch("florist.api.monitoring.metrics.redis")
def test_check_status(mock_redis: Mock) -> None:
    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = b"{\"info\": \"test\"}"

    test_uuid = "test_uuid"
    test_redis_host = "localhost"
    test_redis_port = "testport"

    mock_redis.Redis.return_value = mock_redis_connection

    response = client.check_status(test_uuid, test_redis_host, test_redis_port)

    mock_redis.Redis.assert_called_with(host=test_redis_host, port=test_redis_port)
    assert json.loads(response.body.decode()) == {"info": "test"}


@patch("florist.api.monitoring.metrics.redis")
def test_check_status_not_found(mock_redis: Mock) -> None:
    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = None

    test_uuid = "test_uuid"
    test_redis_host = "localhost"
    test_redis_port = "testport"

    mock_redis.Redis.return_value = mock_redis_connection

    response = client.check_status(test_uuid, test_redis_host, test_redis_port)

    mock_redis.Redis.assert_called_with(host=test_redis_host, port=test_redis_port)
    assert response.status_code == 404
    assert json.loads(response.body.decode()) == {"error": f"Client {test_uuid} Not Found"}


@patch("florist.api.monitoring.metrics.redis.Redis", side_effect=Exception("test exception"))
def test_check_status_fail_exception(_: Mock) -> None:

    test_uuid = "test_uuid"
    test_redis_host = "localhost"
    test_redis_port = "testport"

    response = client.check_status(test_uuid, test_redis_host, test_redis_port)

    assert response.status_code == 500
    assert json.loads(response.body.decode()) == {"error": "test exception"}


def test_get_log() -> None:
    test_client_uuid = "test-client-uuid"
    test_log_file_content = "this is a test log file content"
    test_log_file_path = str(get_client_log_file_path(test_client_uuid))

    with open(test_log_file_path, "w") as f:
        f.write(test_log_file_content)

    response = client.get_log(test_log_file_path)

    assert response.status_code == 200
    assert response.body.decode() == f"\"{test_log_file_content}\""

    os.remove(test_log_file_path)

@patch("florist.api.client.os.kill")
def test_stop_success(mock_kill: Mock) -> None:
    test_pid = 1234

    response = client.stop(str(test_pid))

    assert response.status_code == 200
    assert json.loads(response.body.decode()) == {"status": "success"}
    mock_kill.assert_called_once_with(test_pid, signal.SIGTERM)


def test_stop_fail_no_pid() -> None:
    response = client.stop("")

    assert response.status_code == 400
    assert json.loads(response.body.decode()) == {"error": "PID is empty or None."}


def test_stop_fail_exception() -> None:
    test_pid = "inexistant-pid"

    response = client.stop(test_pid)

    assert response.status_code == 500
    assert json.loads(response.body.decode()) == {"error": f"invalid literal for int() with base 10: '{test_pid}'"}
