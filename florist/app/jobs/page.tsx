"use client";

import { useEffect } from "react";
import { ReactElement } from "react/React";

import { refreshJobsByJobStatus, useGetJobsByJobStatus, usePost } from "./hooks";
import { validStatuses, JobData, ClientInfo } from "./definitions";

import Link from "next/link";
import Image from "next/image";

import loading_gif from "../assets/img/loading.gif";

interface StatusProp {
    status: string;
}

export function useGetJobsFromEachJobStatus() {
    // Must be in the same order as the validStatuses object.
    const statusDataFetches = [
        useGetJobsByJobStatus("NOT_STARTED"),
        useGetJobsByJobStatus("IN_PROGRESS"),
        useGetJobsByJobStatus("FINISHED_SUCCESSFULLY"),
        useGetJobsByJobStatus("FINISHED_WITH_ERROR"),
    ];
    return statusDataFetches;
}

export default function Page(): ReactElement {
    const statusKeys = Object.keys(validStatuses);
    const statusDataFetches = useGetJobsFromEachJobStatus();
    if (!statusDataFetches.every(({ isLoading }) => isLoading == false)) {
        return (
            <div className="d-flex justify-content-center align-items-center vh-100">
                <Image data-testid="jobs-page-loading-gif" src={loading_gif} alt="Loading" height={64} width={64} />
            </div>
        );
    }

    const statusComponents = statusDataFetches.map(({ data }, i) => (
        <Status key={i} status={statusKeys[i]} data={data} />
    ));
    return (
        <div>
            <div className="row">
                <div className="col-6 d-flex align-items-center">
                    <h1 className="ps-3">Jobs</h1>
                </div>

                <NewJobButton />

                {statusComponents}
            </div>
        </div>
    );
}

export function NewJobButton(): ReactElement {
    return (
        <div className="col-6 text-end">
            <Link id="new-job-button" className="fixed-plugin-button btn bg-gradient-primary mb-0" href="/jobs/edit">
                <i className="material-icons text-sm">add</i>
                &nbsp;&nbsp;New Job
            </Link>
        </div>
    );
}

export function StartJobButton({ rowId, jobId }: { rowId: number; jobId: string }): ReactElement {
    const { post, response, isLoading, error } = usePost();

    const handleClickStartJobButton = async () => {
        event.preventDefault();

        if (isLoading) {
            // Preventing double submit if already in progress
            return;
        }

        const queryParams = new URLSearchParams({ job_id: jobId });
        const url = `/api/server/training/start?${queryParams.toString()}`;
        await post(url, JSON.stringify({}));
    };

    // Only refresh the job data if there is an error or response
    useEffect(() => refreshJobsByJobStatus(Object.keys(validStatuses)), [error, response]);

    let buttonClasses = "btn btn-sm mb-0 ";
    if (isLoading || response) {
        // If is loading or if a successful response has been received,
        // disable the button to avoid double submit.
        buttonClasses += "btn-secondary disabled";
    } else {
        buttonClasses += "btn-primary";
    }

    return (
        <div>
            <button
                data-testid={`start-training-button-${rowId}`}
                onClick={handleClickStartJobButton}
                className={buttonClasses}
                title="Start"
            >
                {isLoading || response ? (
                    <span className="spinner-border spinner-border-sm align-middle"></span>
                ) : (
                    <i className="material-icons text-sm">play_circle_outline</i>
                )}
            </button>
        </div>
    );
}

export function JobDetailsButton({
    rowId,
    jobId,
    status,
}: {
    rowId: number;
    jobId: string;
    status: string;
}): ReactElement {
    return (
        <div>
            <Link
                data-testid={`job-details-button-${status}-${rowId}`}
                className="btn btn-primary btn-sm mb-0"
                title="Details"
                href={{
                    pathname: "jobs/details",
                    query: { id: jobId },
                }}
            >
                <i className="material-icons text-sm">settings</i>
            </Link>
        </div>
    );
}

export function StopJobButton({ rowId, jobId }: { rowId: number; jobId: string }): ReactElement {
    const { post, response, isLoading, error } = usePost();

    const handleClickStopJobButton = async () => {
        event.preventDefault();

        if (isLoading) {
            // Preventing double submit if already in progress
            return;
        }
        const url = `/api/server/job/stop/${jobId}`;
        await post(url, JSON.stringify({}));
    };

    // Only refresh the job data if there is an error or response
    useEffect(() => refreshJobsByJobStatus(Object.keys(validStatuses)), [error, response]);

    let buttonClasses = "btn btn-sm mb-0 ";
    if (isLoading) {
        // If is loading disable the button to avoid double submit.
        buttonClasses += "btn-secondary disabled";
    } else {
        buttonClasses += "btn-primary";
    }

    return (
        <div>
            <button
                data-testid={`stop-training-button-${rowId}`}
                onClick={handleClickStopJobButton}
                className={buttonClasses}
                title="Stop"
            >
                {isLoading ? (
                    <span className="spinner-border spinner-border-sm align-middle"></span>
                ) : (
                    <i className="material-icons text-sm">stop</i>
                )}
            </button>
        </div>
    );
}

export function Status({ status, data }: { status: StatusProp; data: Object }): ReactElement {
    return (
        <div className="row">
            <div className="col-12">
                <div className="card my-4">
                    <div className="card-header p-0 position-relative mt-n4 mx-3 z-index-2">
                        <div className="bg-gradient-primary shadow-primary border-radius-lg pt-4 pb-3">
                            <h6 data-testid={`status-header-${status}`} className="text-white text-capitalize ps-3">
                                {validStatuses[status]}
                            </h6>
                        </div>
                    </div>
                    <StatusTable data={data} status={status} />
                </div>
            </div>
        </div>
    );
}

export function StatusTable({ data, status }: { data: Array<JobData>; status: StatusProp }): ReactElement {
    if (data.length > 0) {
        return (
            <div className="card-body px-0 pb-2">
                <div className="table-responsive p-0">
                    <table data-testid={`status-table-${status}`} className="table align-items-center mb-0">
                        <thead>
                            <tr>
                                <th className="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">
                                    Model
                                </th>
                                <th className="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">
                                    Server Address
                                </th>
                                <th className="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">
                                    Client Service Addresses
                                </th>
                                <th width="50"></th>
                                <th width="50"></th>
                                <th width="100"></th>
                            </tr>
                        </thead>
                        <TableRows data={data} status={status} />
                    </table>
                </div>
            </div>
        );
    } else {
        return (
            <div className="card-body px-0 pb-2">
                <div className="ps-3">
                    <span data-testid={`status-no-jobs-${status}`}>No jobs to display.</span>
                </div>
            </div>
        );
    }
}

export function TableRows({ data, status }: { data: Array<JobData>; status: StatusProp }): ReactElement {
    const tableRows = data.map((d, i) => (
        <TableRow
            key={i}
            rowId={i}
            model={d.model}
            serverAddress={d.server_address}
            clientsInfo={d.clients_info}
            status={status}
            jobId={d._id}
        />
    ));

    return <tbody>{tableRows}</tbody>;
}

export function TableRow({
    rowId,
    model,
    serverAddress,
    clientsInfo,
    status,
    jobId,
}: {
    rowId: number;
    model: string;
    serverAddress: string;
    clientsInfo: Array<ClientInfo>;
    status: StatusProp;
    jobId: string;
}): ReactElement {
    if (clientsInfo === null) {
        return <td />;
    }

    return (
        <tr>
            <td>
                <div className="d-flex flex-column justify-content-center">
                    <span className="ps-3 text-secondary text-xs font-weight-bold">{model}</span>
                </div>
            </td>
            <td>
                <div className="d-flex flex-column justify-content-center">
                    <span className="ps-3 text-secondary text-xs font-weight-bold">{serverAddress}</span>
                </div>
            </td>
            <td>
                <div className="d-flex flex-column justify-content-center">
                    <span className="ps-3 text-secondary text-xs font-weight-bold">
                        <ClientListTableData clientsInfo={clientsInfo} />
                    </span>
                </div>
            </td>
            <td>
                <JobDetailsButton rowId={rowId} jobId={jobId} status={status} />
            </td>
            <td>
                {validStatuses[status] === "In Progress" ? (
                    <StopJobButton rowId={rowId} jobId={jobId} />
                ) : validStatuses[status] === "Not Started" ? (
                    <StartJobButton rowId={rowId} jobId={jobId} />
                ) : null}
            </td>
        </tr>
    );
}

export function ClientListTableData({ clientsInfo }: { clientsInfo: Array<ClientInfo> }): ReactElement {
    const clientServiceAddressesString = clientsInfo.map((c) => c.service_address).join(", ");
    return <div> {clientServiceAddressesString} </div>;
}
