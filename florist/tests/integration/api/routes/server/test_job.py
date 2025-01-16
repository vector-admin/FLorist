import json
import os
from unittest.mock import ANY

import uvicorn
from fastapi.encoders import jsonable_encoder

from florist.api.clients.common import Client
from florist.api.db.entities import ClientInfo, Job, JobStatus
from florist.api.monitoring.logs import get_server_log_file_path, get_client_log_file_path
from florist.api.routes.server.job import list_jobs_with_status, new_job, get_server_log, get_client_log
from florist.api.servers.common import Model
from florist.tests.integration.api.utils import mock_request, TestUvicornServer
from florist.api.servers.config_parsers import ConfigParser


async def test_new_job(mock_request) -> None:
    test_empty_job = Job()
    result = await new_job(mock_request, test_empty_job)

    assert jsonable_encoder(result) == {
        "_id": ANY,
        "status": JobStatus.NOT_STARTED.value,
        "model": None,
        "server_address": None,
        "server_config": None,
        "config_parser": None,
        "redis_host": None,
        "redis_port": None,
        "clients_info": None,
        "server_metrics": None,
        "server_uuid": None,
        "server_log_file_path": None,
        "server_pid": None,
        "error_message": None,
    }

    test_job = Job(
        id="test-id",
        status=JobStatus.IN_PROGRESS,
        model=Model.MNIST,
        server_address="test-server-address",
        server_config="{\"test-server-info\": 123}",
        config_parser=ConfigParser.BASIC,
        redis_host="test-redis-host",
        redis_port="test-redis-port",
        server_metrics="test-server-metrics",
        server_uuid="test-server-uuid",
        server_log_file_path="test-server-log-file-path",
        server_pid="test-server-pid",
        error_message="test-error-message",
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-1",
                data_path="test/data/path-1",
                redis_host="test-redis-host-1",
                redis_port="test-redis-port-1",
                metrics="test-client-metrics-1",
                uuid="test-client-uuid-1",
                log_file_path="test-log-file-path-1",
                pid="test-client-pid-1",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-2",
                data_path="test/data/path-2",
                redis_host="test-redis-host-2",
                redis_port="test-redis-port-2",
                metrics="test-client-metrics-2",
                uuid="test-client-uuid-2",
                log_file_path="test-log-file-path-2",
                pid="test-client-pid-2",
            ),
        ]
    )
    result = await new_job(mock_request, test_job)

    assert jsonable_encoder(result) == {
        "_id": test_job.id,
        "status": test_job.status.value,
        "model": test_job.model.value,
        "server_address": "test-server-address",
        "server_config": "{\"test-server-info\": 123}",
        "config_parser": test_job.config_parser.value,
        "redis_host": test_job.redis_host,
        "redis_port": test_job.redis_port,
        "server_uuid": test_job.server_uuid,
        "server_metrics": test_job.server_metrics,
        "server_log_file_path": test_job.server_log_file_path,
        "server_pid": test_job.server_pid,
        "error_message": test_job.error_message,
        "clients_info": [
            {
                "_id": ANY,
                "client": test_job.clients_info[0].client.value,
                "service_address": test_job.clients_info[0].service_address,
                "data_path": test_job.clients_info[0].data_path,
                "redis_host": test_job.clients_info[0].redis_host,
                "redis_port": test_job.clients_info[0].redis_port,
                "uuid": test_job.clients_info[0].uuid,
                "metrics": test_job.clients_info[0].metrics,
                "log_file_path": test_job.clients_info[0].log_file_path,
                "pid": test_job.clients_info[0].pid,
            }, {
                "_id": ANY,
                "client": test_job.clients_info[1].client.value,
                "service_address": test_job.clients_info[1].service_address,
                "data_path": test_job.clients_info[1].data_path,
                "redis_host": test_job.clients_info[1].redis_host,
                "redis_port": test_job.clients_info[1].redis_port,
                "uuid": test_job.clients_info[1].uuid,
                "metrics": test_job.clients_info[1].metrics,
                "log_file_path": test_job.clients_info[1].log_file_path,
                "pid": test_job.clients_info[1].pid,
            },
        ],
    }


async def test_list_jobs_with_status(mock_request) -> None:
    test_job1 = Job(
        id="test-id1",
        status=JobStatus.NOT_STARTED,
        model=Model.MNIST,
        server_address="test-server-address1",
        server_config="{\"test-server-info\": 123}",
        config_parser=ConfigParser.BASIC,
        redis_host="test-redis-host1",
        redis_port="test-redis-port1",
        server_metrics="test-server-metrics1",
        server_uuid="test-server-uuid1",
        server_log_file_path="test-server-log-file-path1",
        server_pid="test-server-pid1",
        error_message="test-error-message1",
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-1-1",
                data_path="test/data/path-1-1",
                redis_host="test-redis-host-1-1",
                redis_port="test-redis-port-1-1",
                metrics="test-client-metrics-1-1",
                uuid="test-client-uuid-1-1",
                log_file_path="test-log-file-path-1-1",
                pid="test-client-pid-1-1",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-2-1",
                data_path="test/data/path-2-1",
                redis_host="test-redis-host-2-1",
                redis_port="test-redis-port-2-1",
                metrics="test-client-metrics-2-1",
                uuid="test-client-uuid-2-1",
                log_file_path="test-log-file-path-2-1",
                pid="test-client-pid-2-1",
            ),
        ]
    )

    test_job2 = Job(
        id="test-id2",
        status=JobStatus.IN_PROGRESS,
        model=Model.MNIST,
        server_address="test-server-address2",
        server_config="{\"test-server-info\": 123}",
        config_parser=ConfigParser.BASIC,
        redis_host="test-redis-host2",
        redis_port="test-redis-port2",
        server_metrics="test-server-metrics2",
        server_uuid="test-server-uuid2",
        server_log_file_path="test-server-log-file-path2",
        server_pid="test-server-pid2",
        error_message="test-error-message2",
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-1-2",
                data_path="test/data/path-1-2",
                redis_host="test-redis-host-1-2",
                redis_port="test-redis-port-1-2",
                metrics="test-client-metrics-1-2",
                uuid="test-client-uuid-1-2",
                log_file_path="test-log-file-path-1-2",
                pid="test-client-pid-1-2",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-2-2",
                data_path="test/data/path-2-2",
                redis_host="test-redis-host-2-2",
                redis_port="test-redis-port-2-2",
                metrics="test-client-metrics-2-2",
                uuid="test-client-uuid-2-2",
                log_file_path="test-log-file-path-2-2",
                pid="test-client-pid-2-2",
            ),
        ]
    )

    test_job3 = Job(
        id="test-id3",
        status=JobStatus.FINISHED_WITH_ERROR,
        model=Model.MNIST,
        server_address="test-server-address3",
        server_config="{\"test-server-info\": 123}",
        config_parser=ConfigParser.BASIC,
        redis_host="test-redis-host3",
        redis_port="test-redis-port3",
        server_metrics="test-server-metrics3",
        server_uuid="test-server-uuid3",
        server_log_file_path="test-server-log-file-path3",
        server_pid="test-server-pid3",
        error_message="test-error-message3",
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-1-3",
                data_path="test/data/path-1-3",
                redis_host="test-redis-host-1-3",
                redis_port="test-redis-port-1-3",
                metrics="test-client-metrics-1-3",
                uuid="test-client-uuid-1-3",
                log_file_path="test-log-file-path-1-3",
                pid="test-client-pid-1-3",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-2-3",
                data_path="test/data/path-2-3",
                redis_host="test-redis-host-2-3",
                redis_port="test-redis-port-2-3",
                metrics="test-client-metrics-2-3",
                uuid="test-client-uuid-2-3",
                log_file_path="test-log-file-path-2-3",
                pid="test-client-pid-2-3",
            ),
        ]
    )

    test_job4 = Job(
        id="test-id4",
        status=JobStatus.FINISHED_SUCCESSFULLY,
        model=Model.MNIST,
        server_address="test-server-address4",
        server_config="{\"test-server-info\": 123}",
        config_parser=ConfigParser.BASIC,
        redis_host="test-redis-host4",
        redis_port="test-redis-port4",
        server_metrics="test-server-metrics4",
        server_uuid="test-server-uuid4",
        server_log_file_path="test-server-log-file-path4",
        server_pid="test-server-pid4",
        error_message="test-error-message4",
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-1-4",
                data_path="test/data/path-1-4",
                redis_host="test-redis-host-1-4",
                redis_port="test-redis-port-1-4",
                metrics="test-client-metrics-1-4",
                uuid="test-client-uuid-1-4",
                log_file_path="test-log-file-path-1-4",
                pid="test-client-pid-1-4",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address="test-addr-2-4",
                data_path="test/data/path-2-4",
                redis_host="test-redis-host-2-4",
                redis_port="test-redis-port-2-4",
                metrics="test-client-metrics-2-4",
                uuid="test-client-uuid-2-4",
                log_file_path="test-log-file-path-2-4",
                pid="test-client-pid-2-4",
            ),
        ]
    )
    await new_job(mock_request, test_job1)
    await new_job(mock_request, test_job2)
    await new_job(mock_request, test_job3)
    await new_job(mock_request, test_job4)

    result_not_started = await list_jobs_with_status(JobStatus.NOT_STARTED, mock_request)
    result_in_progress = await list_jobs_with_status(JobStatus.IN_PROGRESS, mock_request)
    result_finished_with_error = await list_jobs_with_status(JobStatus.FINISHED_WITH_ERROR, mock_request)
    result_finished_successfully = await list_jobs_with_status(JobStatus.FINISHED_SUCCESSFULLY, mock_request)

    assert isinstance(result_not_started, list)
    assert isinstance(result_in_progress, list)
    assert isinstance(result_finished_with_error, list)
    assert isinstance(result_finished_successfully, list)

    assert jsonable_encoder(result_not_started[0]) == {
        "_id": test_job1.id,
        "status": test_job1.status.value,
        "model": test_job1.model.value,
        "server_address": "test-server-address1",
        "server_config": "{\"test-server-info\": 123}",
        "config_parser": test_job1.config_parser.value,
        "redis_host": test_job1.redis_host,
        "redis_port": test_job1.redis_port,
        "server_metrics": test_job1.server_metrics,
        "server_uuid": test_job1.server_uuid,
        "server_log_file_path": test_job1.server_log_file_path,
        "server_pid": test_job1.server_pid,
        "error_message": test_job1.error_message,
        "clients_info": [
            {
                "_id": ANY,
                "client": test_job1.clients_info[0].client.value,
                "service_address": test_job1.clients_info[0].service_address,
                "data_path": test_job1.clients_info[0].data_path,
                "redis_host": test_job1.clients_info[0].redis_host,
                "redis_port": test_job1.clients_info[0].redis_port,
                "metrics": test_job1.clients_info[0].metrics,
                "uuid": test_job1.clients_info[0].uuid,
                "log_file_path": test_job1.clients_info[0].log_file_path,
                "pid": test_job1.clients_info[0].pid,
            }, {
                "_id": ANY,
                "client": test_job1.clients_info[1].client.value,
                "service_address": test_job1.clients_info[1].service_address,
                "data_path": test_job1.clients_info[1].data_path,
                "redis_host": test_job1.clients_info[1].redis_host,
                "redis_port": test_job1.clients_info[1].redis_port,
                "metrics": test_job1.clients_info[1].metrics,
                "uuid": test_job1.clients_info[1].uuid,
                "log_file_path": test_job1.clients_info[1].log_file_path,
                "pid": test_job1.clients_info[1].pid,
            },
        ],
    }

    assert jsonable_encoder(result_in_progress[0]) == {
        "_id": test_job2.id,
        "status": test_job2.status.value,
        "model": test_job2.model.value,
        "server_address": "test-server-address2",
        "server_config": "{\"test-server-info\": 123}",
        "config_parser": test_job2.config_parser.value,
        "redis_host": test_job2.redis_host,
        "redis_port": test_job2.redis_port,
        "server_metrics": test_job2.server_metrics,
        "server_uuid": test_job2.server_uuid,
        "server_log_file_path": test_job2.server_log_file_path,
        "server_pid": test_job2.server_pid,
        "error_message": test_job2.error_message,
        "clients_info": [
            {
                "_id": ANY,
                "client": test_job2.clients_info[0].client.value,
                "service_address": test_job2.clients_info[0].service_address,
                "data_path": test_job2.clients_info[0].data_path,
                "redis_host": test_job2.clients_info[0].redis_host,
                "redis_port": test_job2.clients_info[0].redis_port,
                "metrics": test_job2.clients_info[0].metrics,
                "uuid": test_job2.clients_info[0].uuid,
                "log_file_path": test_job2.clients_info[0].log_file_path,
                "pid": test_job2.clients_info[0].pid,
            }, {
                "_id": ANY,
                "client": test_job2.clients_info[1].client.value,
                "service_address": test_job2.clients_info[1].service_address,
                "data_path": test_job2.clients_info[1].data_path,
                "redis_host": test_job2.clients_info[1].redis_host,
                "redis_port": test_job2.clients_info[1].redis_port,
                "metrics": test_job2.clients_info[1].metrics,
                "uuid": test_job2.clients_info[1].uuid,
                "log_file_path": test_job2.clients_info[1].log_file_path,
                "pid": test_job2.clients_info[1].pid,
            },
        ],
    }

    assert jsonable_encoder(result_finished_with_error[0]) == {
        "_id": test_job3.id,
        "status": test_job3.status.value,
        "model": test_job3.model.value,
        "server_address": "test-server-address3",
        "server_config": "{\"test-server-info\": 123}",
        "config_parser": test_job3.config_parser.value,
        "redis_host": test_job3.redis_host,
        "redis_port": test_job3.redis_port,
        "server_metrics": test_job3.server_metrics,
        "server_uuid": test_job3.server_uuid,
        "server_log_file_path": test_job3.server_log_file_path,
        "server_pid": test_job3.server_pid,
        "error_message": test_job3.error_message,
        "clients_info": [
            {
                "_id": ANY,
                "client": test_job3.clients_info[0].client.value,
                "service_address": test_job3.clients_info[0].service_address,
                "data_path": test_job3.clients_info[0].data_path,
                "redis_host": test_job3.clients_info[0].redis_host,
                "redis_port": test_job3.clients_info[0].redis_port,
                "metrics": test_job3.clients_info[0].metrics,
                "uuid": test_job3.clients_info[0].uuid,
                "log_file_path": test_job3.clients_info[0].log_file_path,
                "pid": test_job3.clients_info[0].pid,
            }, {
                "_id": ANY,
                "client": test_job3.clients_info[1].client.value,
                "service_address": test_job3.clients_info[1].service_address,
                "data_path": test_job3.clients_info[1].data_path,
                "redis_host": test_job3.clients_info[1].redis_host,
                "redis_port": test_job3.clients_info[1].redis_port,
                "metrics": test_job3.clients_info[1].metrics,
                "uuid": test_job3.clients_info[1].uuid,
                "log_file_path": test_job3.clients_info[1].log_file_path,
                "pid": test_job3.clients_info[1].pid,
            },
        ],
    }

    assert jsonable_encoder(result_finished_successfully[0]) == {
        "_id": test_job4.id,
        "status": test_job4.status.value,
        "model": test_job4.model.value,
        "server_address": "test-server-address4",
        "server_config": "{\"test-server-info\": 123}",
        "config_parser": test_job4.config_parser.value,
        "redis_host": test_job4.redis_host,
        "redis_port": test_job4.redis_port,
        "server_metrics": test_job4.server_metrics,
        "server_uuid": test_job4.server_uuid,
        "server_log_file_path": test_job4.server_log_file_path,
        "server_pid": test_job4.server_pid,
        "error_message": test_job4.error_message,
        "clients_info": [
            {
                "_id": ANY,
                "client": test_job4.clients_info[0].client.value,
                "service_address": test_job4.clients_info[0].service_address,
                "data_path": test_job4.clients_info[0].data_path,
                "redis_host": test_job4.clients_info[0].redis_host,
                "redis_port": test_job4.clients_info[0].redis_port,
                "metrics": test_job4.clients_info[0].metrics,
                "uuid": test_job4.clients_info[0].uuid,
                "log_file_path": test_job4.clients_info[0].log_file_path,
                "pid": test_job4.clients_info[0].pid,
            }, {
                "_id": ANY,
                "client": test_job4.clients_info[1].client.value,
                "service_address": test_job4.clients_info[1].service_address,
                "data_path": test_job4.clients_info[1].data_path,
                "redis_host": test_job4.clients_info[1].redis_host,
                "redis_port": test_job4.clients_info[1].redis_port,
                "metrics": test_job4.clients_info[1].metrics,
                "uuid": test_job4.clients_info[1].uuid,
                "log_file_path": test_job4.clients_info[1].log_file_path,
                "pid": test_job4.clients_info[1].pid,
            },
        ],
    }


async def test_get_server_log_success(mock_request):
    test_log_file_name = "test-log-file-name"
    test_log_file_content = "this is a test log file content"
    test_log_file_path = str(get_server_log_file_path(test_log_file_name))

    with open(test_log_file_path, "w") as f:
        f.write(test_log_file_content)

    result_job = await new_job(mock_request, Job(server_log_file_path=test_log_file_path))

    result = await get_server_log(result_job.id, mock_request)

    assert result.status_code == 200
    assert result.body.decode() == f"\"{test_log_file_content}\""

    os.remove(test_log_file_path)


async def test_get_server_log_error_no_job(mock_request):
    test_job_id = "inexistent-job-id"

    result = await get_server_log(test_job_id, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Job {test_job_id} not found"}


async def test_get_server_log_error_no_log_path(mock_request):
    result_job = await new_job(mock_request, Job())

    result = await get_server_log(result_job.id, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Log file path is None or empty"}


async def test_get_client_log_success(mock_request):
    test_log_file_name = "test-log-file-name"
    test_log_file_content = "this is a test log file content"
    test_log_file_path = str(get_client_log_file_path(test_log_file_name))

    with open(test_log_file_path, "w") as f:
        f.write(test_log_file_content)

    test_client_host = "localhost"
    test_client_port = 8001

    result_job = await new_job(mock_request, Job(
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address=f"{test_client_host}:{test_client_port}",
                data_path="test/data/path-1",
                redis_host="test-redis-host-1",
                redis_port="test-redis-port-1",
            ),
            ClientInfo(
                client=Client.MNIST,
                service_address=f"{test_client_host}:{test_client_port}",
                data_path="test/data/path-2",
                redis_host="test-redis-host-2",
                redis_port="test-redis-port-2",
                log_file_path=test_log_file_path,
            ),
        ],
    ))

    client_config = uvicorn.Config("florist.api.client:app", host=test_client_host, port=test_client_port, log_level="debug")
    client_service = TestUvicornServer(config=client_config)
    with client_service.run_in_thread():
        result = await get_client_log(result_job.id, 1, mock_request)

    assert result.status_code == 200
    assert result.body.decode() == f"\"{test_log_file_content}\""

    os.remove(test_log_file_path)


async def test_get_client_log_error_no_job(mock_request):
    test_job_id = "inexistent-job-id"

    result = await get_client_log(test_job_id, 0, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Job {test_job_id} not found"}


async def test_get_client_log_error_no_clients(mock_request):
    result_job = await new_job(mock_request, Job())

    result = await get_client_log(result_job.id, 0, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Job has no clients."}


async def test_get_client_log_error_invalid_client_index(mock_request):
    result_job = await new_job(mock_request, Job(
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address=f"test-address",
                data_path="test/data/path-1",
                redis_host="test-redis-host-1",
                redis_port="test-redis-port-1",
            ),
        ],
    ))

    result = await get_client_log(result_job.id, 1, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Client index 1 is invalid (total: 1)"}


async def test_get_client_log_error_log_file_path_is_none(mock_request):
    result_job = await new_job(mock_request, Job(
        clients_info=[
            ClientInfo(
                client=Client.MNIST,
                service_address=f"test-address",
                data_path="test/data/path-1",
                redis_host="test-redis-host-1",
                redis_port="test-redis-port-1",
            ),
        ],
    ))

    result = await get_client_log(result_job.id, 0, mock_request)

    assert result.status_code == 400
    assert json.loads(result.body.decode()) == {"error": f"Log file path is None or empty"}
