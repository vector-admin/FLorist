import asyncio
import json
from pytest import raises
from typing import Dict, Any, Tuple
from unittest.mock import Mock, AsyncMock, patch, ANY, call

from florist.api.db.config import DATABASE_NAME
from florist.api.db.entities import Job, JobStatus, JOB_COLLECTION_NAME
from florist.api.models.mnist import MnistNet
from florist.api.routes.server.training import (
    client_training_listener,
    start,
    server_training_listener
)

@patch("florist.api.routes.server.training.client_training_listener")
@patch("florist.api.routes.server.training.server_training_listener")
@patch("florist.api.routes.server.training.launch_local_server")
@patch("florist.api.monitoring.metrics.redis")
@patch("florist.api.routes.server.training.requests")
@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.db.entities.Job.set_uuids")
@patch("florist.api.db.entities.Job.set_server_log_file_path")
@patch("florist.api.db.entities.Job.set_client_log_file_path")
@patch("florist.api.db.entities.Job.set_pids")
async def test_start_success(
    mock_set_pids: Mock,
    mock_set_client_log_file_path: Mock,
    mock_server_log_file_path: Mock,
    mock_set_uuids: Mock,
    mock_set_status: Mock,
    mock_requests: Mock,
    mock_redis: Mock,
    mock_launch_local_server: Mock,
    mock_server_training_listener: Mock,
    mock_client_training_listener: Mock,
) -> None:
    # Arrange
    test_job_id = "test-job-id"
    test_server_config, test_job, mock_job_collection, mock_fastapi_request = _setup_test_job_and_mocks()

    test_server_uuid = "test-server-uuid"
    test_server_log_file_path = "test-log-file-path"
    test_server_pid = 12345
    mock_server_process = Mock()
    mock_server_process.pid = test_server_pid
    mock_launch_local_server.return_value = (test_server_uuid, mock_server_process, test_server_log_file_path)

    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = b"{\"fit_start\": null}"
    mock_redis.Redis.return_value = mock_redis_connection

    mock_response = Mock()
    mock_response.status_code = 200
    test_client_1_uuid = "test-client-1-uuid"
    test_client_1_log_file_path = "test-client-1-log-file-path"
    test_client_1_pid = "test-client-1-pid"
    test_client_2_uuid = "test-client-2-uuid"
    test_client_2_log_file_path = "test-client-2-log-file-path"
    test_client_2_pid = "test-client-2-pid"
    mock_response.json.side_effect = [
        {"uuid": test_client_1_uuid, "log_file_path": test_client_1_log_file_path, "pid": test_client_1_pid},
        {"uuid": test_client_2_uuid, "log_file_path": test_client_2_log_file_path, "pid": test_client_2_pid},
    ]
    mock_requests.get.return_value = mock_response

    mock_client_training_listener.return_value = AsyncMock()
    mock_server_training_listener.return_value = AsyncMock()

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 200
    json_body = json.loads(response.body.decode())
    assert json_body == {"server_uuid": test_server_uuid, "client_uuids": [test_client_1_uuid, test_client_2_uuid]}

    mock_job_collection.find_one.assert_called_with({"_id": test_job_id})
    mock_set_status.assert_called_once_with(JobStatus.IN_PROGRESS, mock_fastapi_request.app.database)

    assert isinstance(mock_launch_local_server.call_args_list[0][1]["model"], MnistNet)
    mock_launch_local_server.assert_called_once_with(
        model=ANY,
        n_clients=len(test_job["clients_info"]),
        server_address=test_job["server_address"],
        n_server_rounds=test_server_config["n_server_rounds"],
        batch_size=test_server_config["batch_size"],
        local_epochs=test_server_config["local_epochs"],
        redis_host=test_job["redis_host"],
        redis_port=test_job["redis_port"],
    )
    mock_redis.Redis.assert_called_once_with(host=test_job["redis_host"], port=test_job["redis_port"])
    mock_redis_connection.get.assert_called_once_with(test_server_uuid)
    mock_server_log_file_path.assert_called_once_with(test_server_log_file_path, mock_fastapi_request.app.database)

    mock_requests.get.assert_any_call(
        url=f"http://{test_job['clients_info'][0]['service_address']}/api/client/start",
        params={
            "server_address": test_job["server_address"],
            "client": test_job["clients_info"][0]["client"],
            "data_path": test_job["clients_info"][0]["data_path"],
            "redis_host": test_job["clients_info"][0]["redis_host"],
            "redis_port": test_job["clients_info"][0]["redis_port"],
        },
    )
    mock_requests.get.assert_any_call(
        url=f"http://{test_job['clients_info'][1]['service_address']}/api/client/start",
        params={
            "server_address": test_job["server_address"],
            "client": test_job["clients_info"][1]["client"],
            "data_path": test_job["clients_info"][1]["data_path"],
            "redis_host": test_job["clients_info"][1]["redis_host"],
            "redis_port": test_job["clients_info"][1]["redis_port"],
        },
    )

    mock_set_client_log_file_path.assert_has_calls([
        call(0, test_client_1_log_file_path, mock_fastapi_request.app.database),
        call(1, test_client_2_log_file_path, mock_fastapi_request.app.database),
    ])

    mock_set_uuids.assert_called_once_with(
        test_server_uuid,
        [test_client_1_uuid, test_client_2_uuid],
        mock_fastapi_request.app.database,
    )
    mock_set_pids.assert_called_once_with(
        str(test_server_pid),
        [test_client_1_pid, test_client_2_pid],
        mock_fastapi_request.app.database,
    )

    expected_job = Job(**test_job)
    expected_job.id = ANY
    expected_job.clients_info[0].id = ANY
    expected_job.clients_info[1].id = ANY

    mock_server_training_listener.assert_called_with(expected_job)
    mock_client_training_listener.assert_has_calls([
        call(expected_job, expected_job.clients_info[0]),
        call(expected_job, expected_job.clients_info[1]),
    ])


async def test_start_fail_unsupported_server_model() -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, test_job, _, mock_fastapi_request = _setup_test_job_and_mocks()
    test_job["model"] = "WRONG MODEL"

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": ANY}
    assert "value is not a valid enumeration member" in json_body["error"]


async def test_start_fail_unsupported_client() -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, test_job, _, mock_fastapi_request = _setup_test_job_and_mocks()
    test_job["clients_info"][1]["client"] = "WRONG CLIENT"

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": ANY}
    assert "value is not a valid enumeration member" in json_body["error"]


@patch("florist.api.db.entities.Job.set_status")
async def test_start_fail_missing_info(_: Mock) -> None:
    fields_to_be_removed = ["model", "server_config", "clients_info", "server_address", "redis_host", "redis_port"]

    for field_to_be_removed in fields_to_be_removed:
        # Arrange
        test_job_id = "test-job-id"
        _, test_job, _, mock_fastapi_request = _setup_test_job_and_mocks()
        del test_job[field_to_be_removed]

        # Act
        response = await start(test_job_id, mock_fastapi_request)

        # Assert
        assert response.status_code == 400
        json_body = json.loads(response.body.decode())
        assert json_body == {"error": ANY}
        assert f"Missing Job information: {field_to_be_removed}" in json_body["error"]


@patch("florist.api.db.entities.Job.set_status")
async def test_start_fail_invalid_server_config(_: Mock) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, test_job, _, mock_fastapi_request = _setup_test_job_and_mocks()
    test_job["server_config"] = "not json"

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 400
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": ANY}
    assert f"server_config is not a valid json string." in json_body["error"]


@patch("florist.api.db.entities.Job.set_status")
async def test_start_fail_empty_clients_info(_: Mock) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, test_job, _, mock_fastapi_request = _setup_test_job_and_mocks()
    test_job["clients_info"] = []

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 400
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": ANY}
    assert f"Missing Job information: clients_info" in json_body["error"]


@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.routes.server.training.launch_local_server")
async def test_start_launch_server_exception(mock_launch_local_server: Mock, _: Mock) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, _, _, mock_fastapi_request = _setup_test_job_and_mocks()

    test_exception = Exception("test exception")
    mock_launch_local_server.side_effect = test_exception

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": str(test_exception)}


@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.routes.server.training.launch_local_server")
@patch("florist.api.monitoring.metrics.redis")
@patch("florist.api.db.entities.Job.set_server_log_file_path")
async def test_start_wait_for_metric_exception(
    mock_set_server_log_file_path: Mock,
    mock_redis: Mock,
    mock_launch_local_server: Mock,
    _: Mock,
) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, _, _, mock_fastapi_request = _setup_test_job_and_mocks()

    test_server_uuid = "test-server-uuid"
    test_log_file_path = "test-log-file-path"
    mock_launch_local_server.return_value = (test_server_uuid, None, test_log_file_path)

    test_exception = Exception("test exception")
    mock_redis.Redis.side_effect = test_exception

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": str(test_exception)}

    mock_set_server_log_file_path.assert_called_once_with(test_log_file_path, mock_fastapi_request.app.database)


@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.routes.server.training.launch_local_server")
@patch("florist.api.monitoring.metrics.redis")
@patch("florist.api.monitoring.metrics.time")  # just so time.sleep does not actually sleep
@patch("florist.api.db.entities.Job.set_server_log_file_path")
async def test_start_wait_for_metric_timeout(
    mock_set_server_log_file_path: Mock,
    _: Mock,
    mock_redis: Mock,
    mock_launch_local_server: Mock,
    __: Mock,
) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, _, _, mock_fastapi_request = _setup_test_job_and_mocks()

    test_server_uuid = "test-server-uuid"
    test_log_file_path = "test-log-file-path"
    mock_launch_local_server.return_value = (test_server_uuid, None, test_log_file_path)

    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = b"{\"foo\": null}"
    mock_redis.Redis.return_value = mock_redis_connection

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": "Metric 'fit_start' not been found after 20 retries."}

    mock_set_server_log_file_path.assert_called_once_with(test_log_file_path, mock_fastapi_request.app.database)


@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.routes.server.training.launch_local_server")
@patch("florist.api.monitoring.metrics.redis")
@patch("florist.api.routes.server.training.requests")
@patch("florist.api.db.entities.Job.set_server_log_file_path")
async def test_start_fail_response(
    mock_set_server_log_file_path: Mock,
    mock_requests: Mock,
    mock_redis: Mock,
    mock_launch_local_server: Mock,
    _: Mock,
) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, _, _, mock_fastapi_request = _setup_test_job_and_mocks()

    test_server_uuid = "test-server-uuid"
    test_log_file_path = "test-log-file-path"
    mock_launch_local_server.return_value = (test_server_uuid, None, test_log_file_path)

    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = b"{\"fit_start\": null}"
    mock_redis.Redis.return_value = mock_redis_connection

    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.json.return_value = "error"
    mock_requests.get.return_value = mock_response

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": f"Client response returned 403. Response: error"}

    mock_set_server_log_file_path.assert_called_once_with(test_log_file_path, mock_fastapi_request.app.database)


@patch("florist.api.db.entities.Job.set_status")
@patch("florist.api.routes.server.training.launch_local_server")
@patch("florist.api.monitoring.metrics.redis")
@patch("florist.api.routes.server.training.requests")
@patch("florist.api.db.entities.Job.set_server_log_file_path")
async def test_start_no_uuid_in_response(
    mock_set_server_log_file_path: Mock,
    mock_requests: Mock,
    mock_redis: Mock,
    mock_launch_local_server: Mock,
    _: Mock,
) -> None:
    # Arrange
    test_job_id = "test-job-id"
    _, _, _, mock_fastapi_request = _setup_test_job_and_mocks()

    test_server_uuid = "test-server-uuid"
    test_log_file_path = "test-log-file-path"
    mock_launch_local_server.return_value = (test_server_uuid, None, test_log_file_path)

    mock_redis_connection = Mock()
    mock_redis_connection.get.return_value = b"{\"fit_start\": null}"
    mock_redis.Redis.return_value = mock_redis_connection

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"foo": "bar"}
    mock_requests.get.return_value = mock_response

    # Act
    response = await start(test_job_id, mock_fastapi_request)

    # Assert
    assert response.status_code == 500
    json_body = json.loads(response.body.decode())
    assert json_body == {"error": "Client response did not return a UUID. Response: {'foo': 'bar'}"}

    mock_set_server_log_file_path.assert_called_once_with(test_log_file_path, mock_fastapi_request.app.database)


@patch("florist.api.routes.server.training.AsyncIOMotorClient")
@patch("florist.api.routes.server.training.get_from_redis")
@patch("florist.api.routes.server.training.get_subscriber")
async def test_server_training_listener(
    mock_get_subscriber: Mock,
    mock_get_from_redis: Mock,
    mock_motor_client: Mock,
) -> None:
    # Setup
    test_job = Job(**{
        "server_uuid": "test-server-uuid",
        "redis_host": "test-redis-host",
        "redis_port": "test-redis-port",
        "clients_info": [
            {
                "service_address": "test-service-address",
                "uuid": "test-uuid",
                "redis_host": "test-client-redis-host",
                "redis_port": "test-client-redis-port",
                "client": "MNIST",
                "data_path": "test-data-path",
            }
        ]
    })
    test_server_metrics = [
        {"fit_start": "2022-02-02 02:02:02"},
        {"fit_start": "2022-02-02 02:02:02", "rounds": []},
        {"fit_start": "2022-02-02 02:02:02", "rounds": [], "fit_end": "2022-02-02 03:03:03"},
    ]
    mock_get_from_redis.side_effect = test_server_metrics
    mock_subscriber = Mock()
    mock_subscriber.listen.return_value = [
        {"type": "message"},
        {"type": "not message"},
        {"type": "message"},
        {"type": "message"},
        {"type": "message"},
    ]
    mock_get_subscriber.return_value = mock_subscriber
    mock_db_client = make_mock_db_client()
    mock_motor_client.return_value = mock_db_client

    with patch.object(Job, "set_status", AsyncMock()) as mock_set_status:
        with patch.object(Job, "set_server_metrics", AsyncMock()) as mock_set_server_metrics:
            # Act
            await server_training_listener(test_job)

            # Assert
            mock_set_status.assert_called_once_with(JobStatus.FINISHED_SUCCESSFULLY, mock_db_client[DATABASE_NAME])

            assert mock_set_server_metrics.call_count == 3
            mock_set_server_metrics.assert_has_calls([
                call(test_server_metrics[0], mock_db_client[DATABASE_NAME]),
                call(test_server_metrics[1], mock_db_client[DATABASE_NAME]),
                call(test_server_metrics[2], mock_db_client[DATABASE_NAME]),
            ])

    assert mock_get_from_redis.call_count == 3
    mock_get_subscriber.assert_called_once_with(test_job.server_uuid, test_job.redis_host, test_job.redis_port)
    mock_db_client.close.assert_called()


@patch("florist.api.routes.server.training.AsyncIOMotorClient")
@patch("florist.api.routes.server.training.get_from_redis")
async def test_server_training_listener_already_finished(mock_get_from_redis: Mock, mock_motor_client: Mock) -> None:
    # Setup
    test_job = Job(**{
        "server_uuid": "test-server-uuid",
        "redis_host": "test-redis-host",
        "redis_port": "test-redis-port",
        "clients_info": [
            {
                "service_address": "test-service-address",
                "uuid": "test-uuid",
                "redis_host": "test-client-redis-host",
                "redis_port": "test-client-redis-port",
                "client": "MNIST",
                "data_path": "test-data-path",
            }
        ]
    })
    test_server_final_metrics = {"fit_start": "2022-02-02 02:02:02", "rounds": [], "fit_end": "2022-02-02 03:03:03"}
    mock_get_from_redis.side_effect = [test_server_final_metrics]
    mock_db_client = make_mock_db_client()
    mock_motor_client.return_value = mock_db_client

    with patch.object(Job, "set_status", AsyncMock()) as mock_set_status:
        with patch.object(Job, "set_server_metrics", AsyncMock()) as mock_set_server_metrics:
            # Act
            await server_training_listener(test_job)

            # Assert
            mock_set_status.assert_called_once_with(JobStatus.FINISHED_SUCCESSFULLY, mock_db_client[DATABASE_NAME])
            mock_set_server_metrics.assert_called_once_with(test_server_final_metrics, mock_db_client[DATABASE_NAME])

    assert mock_get_from_redis.call_count == 1
    mock_db_client.close.assert_called()


async def test_server_training_listener_fail_no_server_uuid() -> None:
    test_job = Job(**{
        "redis_host": "test-redis-host",
        "redis_port": "test-redis-port",
    })

    with raises(AssertionError, match="job.server_uuid is None."):
        await server_training_listener(test_job)


async def test_server_training_listener_fail_no_redis_host() -> None:
    test_job = Job(**{
        "server_uuid": "test-server-uuid",
        "redis_port": "test-redis-port",
    })

    with raises(AssertionError, match="job.redis_host is None."):
        await server_training_listener(test_job)


async def test_server_training_listener_fail_no_redis_port() -> None:
    test_job = Job(**{
        "server_uuid": "test-server-uuid",
        "redis_host": "test-redis-host",
    })

    with raises(AssertionError, match="job.redis_port is None."):
        await server_training_listener(test_job)


@patch("florist.api.routes.server.training.AsyncIOMotorClient")
@patch("florist.api.routes.server.training.get_from_redis")
@patch("florist.api.routes.server.training.get_subscriber")
async def test_client_training_listener(
    mock_get_subscriber: Mock,
    mock_get_from_redis: Mock,
    mock_motor_client: Mock,
) -> None:
    # Setup
    test_client_uuid = "test-client-uuid"
    test_job = Job(**{
        "clients_info": [
            {
                "service_address": "test-service-address",
                "uuid": test_client_uuid,
                "redis_host": "test-client-redis-host",
                "redis_port": "test-client-redis-port",
                "client": "MNIST",
                "data_path": "test-data-path",
            }
        ]
    })
    test_client_metrics = [
        {"initialized": "2022-02-02 02:02:02"},
        {"initialized": "2022-02-02 02:02:02", "rounds": []},
        {"initialized": "2022-02-02 02:02:02", "rounds": [], "shutdown": "2022-02-02 03:03:03"},
    ]
    mock_get_from_redis.side_effect = test_client_metrics
    mock_subscriber = Mock()
    mock_subscriber.listen.return_value = [
        {"type": "message"},
        {"type": "not message"},
        {"type": "message"},
        {"type": "message"},
        {"type": "message"},
    ]
    mock_get_subscriber.return_value = mock_subscriber
    mock_db_client = make_mock_db_client()
    mock_motor_client.return_value = mock_db_client

    with patch.object(Job, "set_client_metrics", AsyncMock()) as mock_set_client_metrics:
        # Act
        await client_training_listener(test_job, test_job.clients_info[0])

        # Assert
        assert mock_set_client_metrics.call_count == 3
        mock_set_client_metrics.assert_has_calls([
            call(test_client_uuid, test_client_metrics[0], mock_db_client[DATABASE_NAME]),
            call(test_client_uuid, test_client_metrics[1], mock_db_client[DATABASE_NAME]),
            call(test_client_uuid, test_client_metrics[2], mock_db_client[DATABASE_NAME]),
        ])

    assert mock_get_from_redis.call_count == 3
    mock_get_subscriber.assert_called_once_with(
        test_job.clients_info[0].uuid,
        test_job.clients_info[0].redis_host,
        test_job.clients_info[0].redis_port,
    )
    mock_db_client.close.assert_called()


@patch("florist.api.routes.server.training.AsyncIOMotorClient")
@patch("florist.api.routes.server.training.get_from_redis")
async def test_client_training_listener_already_finished(mock_get_from_redis: Mock, mock_motor_client: Mock) -> None:
    # Setup
    test_client_uuid = "test-client-uuid"
    test_job = Job(**{
        "clients_info": [
            {
                "service_address": "test-service-address",
                "uuid": test_client_uuid,
                "redis_host": "test-client-redis-host",
                "redis_port": "test-client-redis-port",
                "client": "MNIST",
                "data_path": "test-data-path",
            }
        ]
    })
    test_client_final_metrics = {"initialized": "2022-02-02 02:02:02", "rounds": [], "shutdown": "2022-02-02 03:03:03"}
    mock_get_from_redis.side_effect = [test_client_final_metrics]
    mock_db_client = make_mock_db_client()
    mock_motor_client.return_value = mock_db_client

    with patch.object(Job, "set_client_metrics", AsyncMock()) as mock_set_client_metrics:
        # Act
        await client_training_listener(test_job, test_job.clients_info[0])

        # Assert
        mock_set_client_metrics.assert_called_once_with(
            test_client_uuid,
            test_client_final_metrics,
            mock_db_client[DATABASE_NAME],
        )

    assert mock_get_from_redis.call_count == 1
    mock_db_client.close.assert_called()


async def test_client_training_listener_fail_no_uuid() -> None:
    test_job = Job(**{
        "clients_info": [
            {
                "redis_host": "test-redis-host",
                "redis_port": "test-redis-port",
                "service_address": "test-service-address",
                "client": "MNIST",
                "data_path": "test-data-path",
            },
        ],
    })

    with raises(AssertionError, match="client_info.uuid is None."):
        await client_training_listener(test_job, test_job.clients_info[0])


def _setup_test_job_and_mocks() -> Tuple[Dict[str, Any], Dict[str, Any], Mock, Mock]:
    test_server_config = {
        "n_server_rounds": 2,
        "batch_size": 8,
        "local_epochs": 1,
    }
    test_job = {
        "status": "NOT_STARTED",
        "model": "MNIST",
        "server_address": "test-server-address",
        "server_config": json.dumps(test_server_config),
        "config_parser": "BASIC",
        "redis_host": "test-redis-host",
        "redis_port": "test-redis-port",
        "server_uuid": "test-server-uuid",
        "server_metrics": "test-server-metrics",
        "clients_info": [
            {
                "client": "MNIST",
                "service_address": "test-service-address-1",
                "data_path": "test-data-path-1",
                "redis_host": "test-redis-host-1",
                "redis_port": "test-redis-port-1",
                "uuid": "test-client-uuids-1",
                "metrics": "test-client-metrics-1",
            },
            {
                "client": "MNIST",
                "service_address": "test-service-address-2",
                "data_path": "test-data-path-2",
                "redis_host": "test-redis-host-2",
                "redis_port": "test-redis-port-2",
                "uuid": "test-client-uuids-2",
                "metrics": "test-client-metrics-2",
            },
        ],
    }

    mock_find_one = asyncio.Future()
    mock_find_one.set_result(test_job)
    mock_job_collection = Mock()
    mock_job_collection.find_one.return_value = mock_find_one
    mock_fastapi_request = Mock()
    mock_fastapi_request.app.database = {JOB_COLLECTION_NAME: mock_job_collection}
    mock_fastapi_request.app.synchronous_database = {JOB_COLLECTION_NAME: mock_job_collection}

    return test_server_config, test_job, mock_job_collection, mock_fastapi_request


def make_mock_db_client() -> Mock:
    mock_database = Mock()
    mock_db_client = Mock()
    mock_db_client.__getitem__ = Mock(
        side_effect=lambda database_name: mock_database if database_name == DATABASE_NAME else None
    )
    return mock_db_client
