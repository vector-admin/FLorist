import json
import signal
from datetime import datetime

from unittest.mock import patch, Mock, AsyncMock, call
from fastapi.responses import JSONResponse
from freezegun import freeze_time

from florist.api.clients.common import Client
from florist.api.routes.server.job import change_job_status, get_job, stop_job
from florist.api.db.entities import JobStatus, ClientInfo


@patch("florist.api.db.entities.Job.find_by_id")
async def test_get_job_success(mock_find_by_id: Mock) -> None:
    mock_job = Mock()
    mock_find_by_id.return_value = mock_job

    mock_request = Mock()
    mock_request.app.database = Mock()

    test_id = "test_id"

    response = await get_job(test_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_id, mock_request.app.database)

    assert response == mock_job


@patch("florist.api.db.entities.Job.find_by_id")
async def test_get_job_fail_none_job(mock_find_by_id: Mock) -> None:
    mock_find_by_id.return_value = None

    mock_request = Mock()
    mock_request.app.database = Mock()

    test_id = "test_id"

    response = await get_job(test_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_id, mock_request.app.database)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert json.loads(response.body.decode("utf-8")) == {"error": f"Job with ID {test_id} does not exist."}


@patch("florist.api.db.entities.Job.find_by_id")
async def test_change_job_status_success(mock_find_by_id: Mock) -> None:
    mock_job = Mock()
    mock_job.set_status = AsyncMock()

    mock_find_by_id.return_value = mock_job

    mock_request = Mock()
    mock_request.app.database = Mock()

    test_id = "test_id"
    test_status = JobStatus.NOT_STARTED

    response = await change_job_status(test_id, test_status, mock_request)

    mock_find_by_id.assert_called_once_with(test_id, mock_request.app.database)
    mock_job.set_status.assert_called_once_with(test_status, mock_request.app.database)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert json.loads(response.body.decode("utf-8")) == {"status": "success"}


@patch("florist.api.db.entities.Job.find_by_id")
async def test_change_job_status_failure_in_find_by_id(mock_find_by_id: Mock) -> None:
    mock_find_by_id.return_value = None

    mock_request = Mock()
    mock_request.app.database = Mock()

    test_id = "test_id"
    test_status = JobStatus.NOT_STARTED

    response = await change_job_status(test_id, test_status, mock_request)

    mock_find_by_id.assert_called_once_with(test_id, mock_request.app.database)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert json.loads(response.body.decode("utf-8")) == {"error": "Job test_id not found"}


@patch("florist.api.db.entities.Job.find_by_id")
async def test_change_job_status_failure_in_set_status(mock_find_by_id: Mock) -> None:
    mock_job = Mock()
    mock_job.set_status = AsyncMock()
    mock_job.set_status.side_effect = ValueError("Test Error")

    mock_find_by_id.return_value = mock_job

    mock_request = Mock()
    mock_request.app.database = Mock()

    test_id = "test_id"
    test_status = JobStatus.NOT_STARTED

    response = await change_job_status(test_id, test_status, mock_request)

    mock_find_by_id.assert_called_once_with(test_id, mock_request.app.database)
    mock_job.set_status.assert_called_once_with(test_status, mock_request.app.database)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert json.loads(response.body.decode("utf-8")) == {"error": "Test Error"}


@freeze_time("2012-12-11 10:09:08")
@patch("florist.api.db.entities.Job.find_by_id")
@patch("florist.api.routes.server.job.requests")
@patch("florist.api.routes.server.job.os.kill")
async def test_stop_job_success(mock_kill: Mock, mock_requests: Mock, mock_find_by_id: Mock) -> None:
    test_job_id = "test-job-id"
    test_pid = 1234
    test_clients = [
        ClientInfo(service_address="test-service-address-1", pid="test-pid-1", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
        ClientInfo(service_address="test-service-address-2", pid="test-pid-2", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
    ]

    mock_job = Mock()
    mock_job.server_pid = test_pid
    mock_job.clients_info = test_clients
    mock_job.set_status = AsyncMock()
    mock_job.set_error_message = AsyncMock()
    mock_find_by_id.return_value = mock_job
    mock_request = Mock()
    mock_request.app.database = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    response = await stop_job(test_job_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_job_id, mock_request.app.database)
    mock_kill.assert_called_once_with(test_pid, signal.SIGTERM)
    mock_job.set_status.assert_called_once_with(JobStatus.FINISHED_WITH_ERROR, mock_request.app.database)
    mock_job.set_error_message(f"Training job terminated manually on {datetime.now()}", mock_request.app.database)
    mock_requests.get.assert_has_calls([
        call(url=f"http://{test_clients[0].service_address}/api/client/stop/{test_clients[0].pid}"),
        call(url=f"http://{test_clients[1].service_address}/api/client/stop/{test_clients[1].pid}"),
    ])

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert json.loads(response.body.decode("utf-8")) == {"status": "success"}


@freeze_time("2012-12-11 10:09:08")
@patch("florist.api.db.entities.Job.find_by_id")
@patch("florist.api.routes.server.job.requests")
@patch("florist.api.routes.server.job.os.kill")
async def test_stop_job_fail_stop_client(mock_kill: Mock, mock_requests: Mock, mock_find_by_id: Mock) -> None:
    test_job_id = "test-job-id"
    test_pid = 1234
    test_clients = [
        ClientInfo(uuid="test-client-uuid-1", service_address="test-service-address-1", pid="test-pid-1", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
        ClientInfo(uuid="test-client-uuid-1", service_address="test-service-address-2", pid="test-pid-2", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
    ]
    test_error = "test-error"

    mock_job = Mock()
    mock_job.server_pid = test_pid
    mock_job.clients_info = test_clients
    mock_job.set_status = AsyncMock()
    mock_job.set_error_message = AsyncMock()
    mock_find_by_id.return_value = mock_job
    mock_request = Mock()
    mock_request.app.database = Mock()
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": test_error}
    mock_requests.get.return_value = mock_response

    response = await stop_job(test_job_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_job_id, mock_request.app.database)
    mock_kill.assert_called_once_with(test_pid, signal.SIGTERM)
    mock_job.set_status.assert_called_once_with(JobStatus.FINISHED_WITH_ERROR, mock_request.app.database)
    mock_requests.get.assert_has_calls([
        call(url=f"http://{test_clients[0].service_address}/api/client/stop/{test_clients[0].pid}"),
        call(url=f"http://{test_clients[1].service_address}/api/client/stop/{test_clients[1].pid}"),
    ], any_order=True)
    mock_job.set_error_message(
        (
            f"Training job terminated manually on {datetime.now()}",
            f"Failed to stop client {test_clients[0].uuid}: {test_error}",
            f"Failed to stop client {test_clients[1].uuid}: {test_error}",
        ),
        mock_request.app.database,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert json.loads(response.body.decode("utf-8")) == {"status": "success"}


@freeze_time("2012-12-11 10:09:08")
@patch("florist.api.db.entities.Job.find_by_id")
@patch("florist.api.routes.server.job.requests")
@patch("florist.api.routes.server.job.os.kill")
async def test_stop_job_fail_stop_server(_: Mock, mock_requests: Mock, mock_find_by_id: Mock) -> None:
    test_job_id = "test-job-id"
    test_server_uuid = "test-server-uuid"
    test_pid = "incorrect-pid"
    test_clients = [
        ClientInfo(service_address="test-service-address-1", pid="test-pid-1", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
        ClientInfo(service_address="test-service-address-2", pid="test-pid-2", client=Client.MNIST, data_path="", redis_host="", redis_port=""),
    ]

    mock_job = Mock()
    mock_job.server_uuid = test_server_uuid
    mock_job.server_pid = test_pid
    mock_job.clients_info = test_clients
    mock_job.set_status = AsyncMock()
    mock_job.set_error_message = AsyncMock()
    mock_find_by_id.return_value = mock_job
    mock_request = Mock()
    mock_request.app.database = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_requests.get.return_value = mock_response

    response = await stop_job(test_job_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_job_id, mock_request.app.database)
    mock_job.set_status.assert_called_once_with(JobStatus.FINISHED_WITH_ERROR, mock_request.app.database)
    mock_requests.get.assert_has_calls([
        call(url=f"http://{test_clients[0].service_address}/api/client/stop/{test_clients[0].pid}"),
        call(url=f"http://{test_clients[1].service_address}/api/client/stop/{test_clients[1].pid}"),
    ])
    mock_job.set_error_message(
        (
            f"Training job terminated manually on {datetime.now()}",
            f"Failed to stop server {test_server_uuid}: invalid literal for int() with base 10: '{test_pid}'",
        ),
        mock_request.app.database,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert json.loads(response.body.decode("utf-8")) == {"status": "success"}


@patch("florist.api.db.entities.Job.find_by_id")
async def test_stop_job_assertion_error(mock_find_by_id: Mock) -> None:
    test_job_id = "test-job-id"
    mock_find_by_id.return_value = None
    mock_request = Mock()
    mock_request.app.database = Mock()

    response = await stop_job(test_job_id, mock_request)

    mock_find_by_id.assert_called_once_with(test_job_id, mock_request.app.database)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert json.loads(response.body.decode("utf-8")) == {"error": f"Job {test_job_id} not found"}
