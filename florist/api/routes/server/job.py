"""FastAPI routes for the job."""

import logging
import os
import signal
from datetime import datetime
from typing import List, Union

import requests
from fastapi import APIRouter, Body, Request, status
from fastapi.responses import JSONResponse

from florist.api.db.entities import MAX_RECORDS_TO_FETCH, Job, JobStatus


router = APIRouter()

LOGGER = logging.getLogger("uvicorn.error")


@router.get(
    path="/{job_id}",
    response_description="Retrieves a job by ID",
    status_code=status.HTTP_200_OK,
    response_model=Job,
)
async def get_job(job_id: str, request: Request) -> Union[Job, JSONResponse]:
    """
    Retrieve a training job by its ID.

    :param request: (fastapi.Request) the FastAPI request object.
    :param job_id: (str) The ID of the job to be retrieved.

    :return: (Union[Job, JSONResponse]) The job with the given ID, or a 400 JSONResponse if it hasn't been found.
    """
    job = await Job.find_by_id(job_id, request.app.database)

    if job is None:
        return JSONResponse(content={"error": f"Job with ID {job_id} does not exist."}, status_code=400)

    return job


@router.post(
    path="",
    response_description="Create a new job",
    status_code=status.HTTP_201_CREATED,
    response_model=Job,
)
async def new_job(request: Request, job: Job = Body(...)) -> Job:  # noqa: B008
    """
    Create a new training job.

    If calling from the REST API, it will receive the job attributes as the Request Body in raw/JSON format.
    See `florist.api.db.entities.Job` to check the list of attributes and their requirements.

    :param request: (fastapi.Request) the FastAPI request object.
    :param job: (Job) The Job instance to be saved in the database.
    :return: (Job) The job that has been saved in the database.
    :raises: (HTTPException) status 400 if job.server_info is not None and cannot be parsed into JSON.
    """
    job_id = await job.create(request.app.database)
    job_in_db = await Job.find_by_id(job_id, request.app.database)

    assert job_in_db is not None
    return job_in_db


@router.get(
    path="/status/{status}",
    response_description="List jobs with the specified status",
    response_model=List[Job],
)
async def list_jobs_with_status(status: JobStatus, request: Request) -> List[Job]:
    """
    List jobs with specified status.

    Fetches list of Job with max length MAX_RECORDS_TO_FETCH.

    :param status: (JobStatus) The status of jobs to query the Job DB for.
    :param request: (fastapi.Request) the FastAPI request object.
    :return: (List[Dict[str, Any]]) A list where each entry is a dictionary with the attributes
        of a Job instance with the specified status.
    """
    return await Job.find_by_status(status, MAX_RECORDS_TO_FETCH, request.app.database)


@router.post(path="/change_status", response_description="Change job to the specified status")
async def change_job_status(job_id: str, status: JobStatus, request: Request) -> JSONResponse:
    """
    Change job job_id to specified status.

    :param job_id: (str) The id of the job to change the status of.
    :param status: (JobStatus) The status to change job_id to.
    :param request: (fastapi.Request) the FastAPI request object.

    :return: (JSONResponse) If successful, returns 200. If not successful, returns response with status code 400
        and body: {"error": <error message>}
    """
    job_in_db = await Job.find_by_id(job_id, request.app.database)
    try:
        assert job_in_db is not None, f"Job {job_id} not found"
        await job_in_db.set_status(status, request.app.database)
        return JSONResponse(content={"status": "success"})
    except AssertionError as assertion_e:
        return JSONResponse(content={"error": str(assertion_e)}, status_code=400)
    except Exception as general_e:
        LOGGER.exception(general_e)
        return JSONResponse(content={"error": str(general_e)}, status_code=500)


@router.post(path="/stop/{job_id}", response_description="Stops a job")
async def stop_job(job_id: str, request: Request) -> JSONResponse:
    """
    Stop the job with the given ID. The job is stopped by killing all the clients and servers processes.

    :param job_id: (str) The id of the job to stop.
    :param request: (fastapi.Request) the FastAPI request object.

    :return: (JSONResponse) If successful, returns 200. If not successful, returns response with status code 400
        and body: {"error": <error message>}
    """
    job = await Job.find_by_id(job_id, request.app.database)
    try:
        assert job is not None, f"Job {job_id} not found"
        assert job.clients_info is not None

        user_error_message = ""
        for client_info in job.clients_info:
            response = requests.get(url=f"http://{client_info.service_address}/api/client/stop/{client_info.pid}")
            status_code = response.status_code
            if status_code != 200:
                response_data = response.json()
                user_error_message += f"Failed to stop client {client_info.uuid}: {response_data['error']}. "
                msg = f"/api/client/stop returned {status_code} for client {client_info.uuid}: {response_data}."
                LOGGER.error(msg)

        if not job.server_pid:
            user_error_message += f"PID for server {job.server_uuid} is empty or None."
        else:
            try:
                os.kill(int(job.server_pid), signal.SIGTERM)
                LOGGER.info(f"Killed process with PID {job.server_pid}")
            except Exception as e:
                user_error_message += f"Failed to stop server {job.server_uuid}: {str(e)}. "

        await job.set_status(JobStatus.FINISHED_WITH_ERROR, request.app.database)
        user_error_message = f"Training job terminated manually on {datetime.now()}. {user_error_message}"
        await job.set_error_message(user_error_message, request.app.database)

        return JSONResponse(content={"status": "success"})
    except AssertionError as assertion_e:
        return JSONResponse(content={"error": str(assertion_e)}, status_code=400)
    except Exception as general_e:
        LOGGER.exception(general_e)
        return JSONResponse(content={"error": str(general_e)}, status_code=500)


@router.get("/get_server_log/{job_id}")
async def get_server_log(job_id: str, request: Request) -> JSONResponse:
    """
    Return the contents of the server's log file for the given job id.

    :param job_id: (str) the ID of the job to get the server logs for.
    :param request: (fastapi.Request) the FastAPI request object.

    :return: (JSONResponse) if successful, returns the contents of the file as a string.
        If not successful, returns the appropriate error code with a JSON with the format below:
            {"error": <error message>}
    """
    try:
        job = await Job.find_by_id(job_id, request.app.database)

        assert job is not None, f"Job {job_id} not found"
        assert job.server_log_file_path is not None and job.server_log_file_path != "", (
            "Log file path is None or empty"
        )

        with open(job.server_log_file_path, "r") as f:
            content = f.read()
            return JSONResponse(content)

    except AssertionError as assertion_e:
        return JSONResponse(content={"error": str(assertion_e)}, status_code=400)
    except Exception as general_e:
        return JSONResponse(content={"error": str(general_e)}, status_code=500)


@router.get("/get_client_log/{job_id}/{client_index}")
async def get_client_log(job_id: str, client_index: int, request: Request) -> JSONResponse:
    """
    Return the contents of the log file for the client with given index under given job id.

    :param job_id: (str) the ID of the job to get the client logs for.
    :param client_index: (int) the index of the client within the job.
    :param request: (fastapi.Request) the FastAPI request object.

    :return: (JSONResponse) if successful, returns the contents of the file as a string.
        If not successful, returns the appropriate error code with a JSON with the format below:
            {"error": <error message>}
    """
    try:
        job = await Job.find_by_id(job_id, request.app.database)

        assert job is not None, f"Job {job_id} not found"
        assert job.clients_info is not None, "Job has no clients."
        assert 0 <= client_index < len(job.clients_info), (
            f"Client index {client_index} is invalid (total: {len(job.clients_info)})"
        )

        client_info = job.clients_info[client_index]
        assert client_info.log_file_path is not None and client_info.log_file_path != "", (
            "Log file path is None or empty"
        )

        response = requests.get(
            url=f"http://{client_info.service_address}/api/client/get_log",
            params={"log_file_path": client_info.log_file_path},
        )
        json_response = response.json()
        return JSONResponse(json_response)

    except AssertionError as assertion_e:
        return JSONResponse(content={"error": str(assertion_e)}, status_code=400)
    except Exception as general_e:
        return JSONResponse(content={"error": str(general_e)}, status_code=500)
