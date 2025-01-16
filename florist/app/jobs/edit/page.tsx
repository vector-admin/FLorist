"use client";
import yaml from "js-yaml";

import { FormEvent, useRef } from "react";
import { ReactElement } from "react/React";
import { useImmer } from "use-immer";
import { produce } from "immer";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useGetModels, useGetClients, usePost } from "../hooks";

interface Job {
    model: string;
    server_address: string;
    redis_host: string;
    redis_port: string;
    server_config: Array<ServerConfig>;
    client_info: Array<ClientInfo>;
}

interface ServerConfig {
    name: string;
    value: string;
}

interface ClientInfo {
    client: string;
    service_address: string;
    data_path: string;
    redis_host: string;
    redis_port: string;
}

export function makeEmptyJob() {
    return {
        model: "",
        server_address: "",
        redis_host: "",
        redis_port: "",
        server_config: [makeEmptyServerConfig()],
        clients_info: [makeEmptyClientInfo()],
    };
}

export function makeEmptyServerConfig() {
    return {
        name: "",
        value: "",
    };
}

export function makeEmptyClientInfo() {
    return {
        client: "",
        service_address: "",
        data_path: "",
        redis_host: "",
        redis_port: "",
    };
}

function formatServerConfig(serverConfig: Array<ServerConfig>): string {
    const serverConfigDict = {};
    for (let sc of serverConfig) {
        serverConfigDict[sc.name] = sc.value;
    }
    return JSON.stringify(serverConfigDict);
}

export default function EditJob(): ReactElement {
    return (
        <div className="col-7 align-items-center">
            <EditJobHeader />
            <EditJobForm />
        </div>
    );
}

export function EditJobHeader(): ReactElement {
    return (
        <div className="card-header pb-0 pt-3">
            <div className="float-start">
                <h1 className="mt-3 mb-0">New Job</h1>
                <p>Create a new FL training job</p>
            </div>
        </div>
    );
}

export function EditJobForm(): ReactElement {
    const [state, setState] = useImmer({ job: makeEmptyJob() });
    const router = useRouter();
    const { post, response, isLoading, error } = usePost();

    async function onSubmitJob() {
        event.preventDefault();
        if (isLoading) {
            // Preventing double submit if already in progress
            return;
        }

        const job = { ...state.job };
        // Server config is a json string, so changing it here before sending the data over
        job.server_config = formatServerConfig(job.server_config);
        await post("/api/server/job", JSON.stringify(job));
    }

    if (response) {
        // If the response object is populated, it means it has completed the
        //post request successfully. Then, wait 1s and redirect to the list jobs page
        setTimeout(() => router.push("/jobs"), 1000);
    }

    let buttonClasses = "btn my-4 save-btn ";
    if (isLoading || response) {
        // If is loading or if a successful response has been received,
        // disable the button to avoid double submit.
        buttonClasses += "bg-gradient-secondary disabled";
    } else {
        buttonClasses += "bg-gradient-primary";
    }

    return (
        <form onSubmit={(e) => onSubmitJob()}>
            <EditJobServerAttributes state={state} setState={setState} />

            <EditJobServerConfig state={state} setState={setState} />

            <EditJobClientsInfo state={state} setState={setState} />

            <button id="job-post" className={buttonClasses}>
                {isLoading ? "Saving..." : "Save"}
            </button>

            {response ? ( // Show the success alert if it has a successful response
                <div id="job-saved-successfully" className="alert alert-secondary text-white" role="alert">
                    <span className="text-sm">Job saved successfully.</span>
                </div>
            ) : null}

            {error ? ( // Show the error alert if it has error
                <div id="job-save-error" className="alert alert-danger alert-dismissible text-white show" role="alert">
                    <span className="text-sm">Error saving job. Please review the information and try again.</span>
                    <button
                        type="button"
                        className="btn-close text-lg py-3 opacity-10"
                        aria-label="Close"
                        onClick={(e) => (e.target.parentElement.parentElement.style.display = "none")}
                    >
                        <span aria-hidden="true">×</span>
                    </button>
                </div>
            ) : null}
        </form>
    );
}

export function EditJobServerAttributes({ state, setState }): ReactElement {
    return (
        <div>
            <div className="input-group input-group-outline gray-input-box mb-3">
                <label className="form-label form-row" htmlFor="job-model">
                    Model
                </label>
                <select
                    className="form-control"
                    id="job-model"
                    value={state.job.model}
                    onChange={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.model = e.target.value;
                            }),
                        )
                    }
                >
                    <option value="empty"></option>
                    <EditJobModelOptions />
                </select>
            </div>

            <div className="input-group input-group-outline gray-input-box mb-3">
                <label className="form-label" htmlFor="job-server-address">
                    Server Address
                </label>
                <input
                    className="form-control"
                    type="text"
                    id="job-server-address"
                    value={state.job.server_address}
                    onChange={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.server_address = e.target.value;
                            }),
                        )
                    }
                />
            </div>

            <div className="input-group input-group-outline gray-input-box mb-3">
                <label className="form-label" htmlFor="job-redis-host">
                    Redis Host
                </label>
                <input
                    className="form-control"
                    type="text"
                    id="job-redis-host"
                    value={state.job.redis_host}
                    onChange={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.redis_host = e.target.value;
                            }),
                        )
                    }
                />
            </div>

            <div className="input-group input-group-outline gray-input-box mb-3">
                <label className="form-label" htmlFor="job-redis-port">
                    Redis Port
                </label>
                <input
                    className="form-control"
                    type="text"
                    id="job-redis-port"
                    value={state.job.redis_port}
                    onChange={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.redis_port = e.target.value;
                            }),
                        )
                    }
                />
            </div>
        </div>
    );
}

export function EditJobModelOptions(): ReactElement {
    const { data, error, isLoading } = useGetModels();
    if (!data) {
        return null;
    }
    return data.map((d, i) => (
        <option key={i} value={d}>
            {d}
        </option>
    ));
}

export function EditJobServerConfig({ state, setState }): ReactElement {
    const addServerConfigItem = produce((newState) => {
        newState.job.server_config.push(makeEmptyServerConfig());
    });
    return (
        <div id="job-server-config">
            <div className="input-group-header">
                <h6>Server Configuration</h6>

                <EditJobServerConfigUploader state={state} setState={setState} />

                <i
                    id="job-server-config-add"
                    className="material-icons opacity-10 input-group-action"
                    onClick={() => setState(addServerConfigItem(state))}
                >
                    add
                </i>
            </div>
            {state.job.server_config.map((c, i) => (
                <EditJobServerConfigItem key={i} index={i} state={state} setState={setState} />
            ))}
        </div>
    );
}

export function EditJobServerConfigUploader({ state, setState }): ReactElement {
    const buttonRef = useRef(null);

    const handleFileUpload = async (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            const fileText = await file.text();

            let data;
            if (file.name.endsWith(".json")) {
                data = JSON.parse(fileText);
            } else if (file.name.endsWith(".yaml") || file.name.endsWith(".yml")) {
                data = yaml.load(fileText);
            } else {
                console.error(`file extension not supported: ${file.name}`);
                return;
            }

            const importedServerConfig = [];
            for (let property of Object.keys(data)) {
                const serverConfigItem = makeEmptyServerConfig();
                serverConfigItem.name = property;
                serverConfigItem.value = data[property];
                importedServerConfig.push(serverConfigItem);
            }

            const setServerConfig = produce((newState, newServerConfig) => {
                newState.job.server_config = newServerConfig;
            });
            setState(setServerConfig(state, importedServerConfig));
        }
    };

    return (
        <div>
            <a
                id="job-server-config-import"
                className="btn btn-link"
                title="Import Server Config as JSON or YAML"
                onClick={() => buttonRef.current.click()}
            >
                <i className="material-icons">upload</i>
                Import JSON or YAML
            </a>
            <input type="file" ref={buttonRef} id="job-server-config-uploader" onChange={handleFileUpload} />
        </div>
    );
}

export function EditJobServerConfigItem({ index, state, setState }): ReactElement {
    const changeServerConfigAttribute = produce((newState, attribute, value) => {
        newState.job.server_config[index][attribute] = value;
    });

    let nameFieldClasses = "input-group input-group-outline gray-input-box mb-3 ";
    if (state.job.server_config[index].name) {
        nameFieldClasses += "is-filled";
    }

    let valueFieldClasses = "input-group input-group-outline gray-input-box mb-3 ";
    if (state.job.server_config[index].value) {
        valueFieldClasses += "is-filled";
    }

    return (
        <div className="input-group-flex">
            <div className="input-group-column">
                <div className={nameFieldClasses}>
                    <label className="form-label" htmlFor={"job-server-config-name-" + index}>
                        Name
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-server-config-name-" + index}
                        value={state.job.server_config[index].name}
                        onChange={(e) => setState(changeServerConfigAttribute(state, "name", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column">
                <div className={valueFieldClasses}>
                    <label className="form-label" htmlFor={"job-server-config-value-" + index}>
                        Value
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-server-config-value-" + index}
                        value={state.job.server_config[index].value}
                        onChange={(e) => setState(changeServerConfigAttribute(state, "value", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column-action">
                <i
                    id={"job-server-config-remove-" + index}
                    className="material-icons opacity-10 input-group-action"
                    onClick={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.server_config.splice(index, 1);
                            }),
                        )
                    }
                >
                    remove
                </i>
            </div>
        </div>
    );
}

export function EditJobClientsInfo({ state, setState }): ReactElement {
    const addServerConfigItem = produce((newState) => {
        newState.job.clients_info.push(makeEmptyClientInfo());
    });
    return (
        <div id="job-clients-info">
            <div className="input-group-header">
                <h6>Clients Configuration</h6>
                <i
                    id="job-clients-info-add"
                    className="material-icons opacity-10 input-group-action"
                    onClick={() => setState(addServerConfigItem(state))}
                >
                    add
                </i>
            </div>
            {state.job.clients_info.map((c, i) => (
                <EditJobClientsInfoItem key={i} index={i} state={state} setState={setState} />
            ))}
        </div>
    );
}

export function EditJobClientsInfoItem({ index, state, setState }): ReactElement {
    const changeClientInfoAttribute = produce((newState, attribute, value) => {
        newState.job.clients_info[index][attribute] = value;
    });
    return (
        <div className="input-group-flex">
            <div className="input-group-column">
                <div className="input-group input-group-outline gray-input-box mb-3">
                    <label className="form-label" htmlFor={"job-client-info-client-" + index}>
                        Client
                    </label>
                    <select
                        className="form-control"
                        id={"job-client-info-client-" + index}
                        value={state.job.clients_info[index].client}
                        onChange={(e) => setState(changeClientInfoAttribute(state, "client", e.target.value))}
                    >
                        <option value="empty"></option>
                        <EditJobClientOptions />
                    </select>
                </div>
            </div>
            <div className="input-group-column">
                <div className="input-group input-group-outline gray-input-box mb-3">
                    <label className="form-label" htmlFor={"job-client-info-service-address-" + index}>
                        Address
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-client-info-service-address-" + index}
                        value={state.job.clients_info[index].service_address}
                        onChange={(e) => setState(changeClientInfoAttribute(state, "service_address", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column">
                <div className="input-group input-group-outline gray-input-box mb-3">
                    <label className="form-label" htmlFor={"job-client-info-data-path-" + index}>
                        Data Path
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-client-info-data-path-" + index}
                        value={state.job.clients_info[index].data_path}
                        onChange={(e) => setState(changeClientInfoAttribute(state, "data_path", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column">
                <div className="input-group input-group-outline gray-input-box mb-3">
                    <label className="form-label" htmlFor={"job-client-info-redis-host-" + index}>
                        Redis Host
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-client-info-redis-host-" + index}
                        value={state.job.clients_info[index].redis_host}
                        onChange={(e) => setState(changeClientInfoAttribute(state, "redis_host", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column">
                <div className="input-group input-group-outline gray-input-box mb-3">
                    <label className="form-label" htmlFor={"job-client-info-redis-port-" + index}>
                        Redis Port
                    </label>
                    <input
                        className="form-control"
                        type="text"
                        id={"job-client-info-redis-port-" + index}
                        value={state.job.clients_info[index].redis_port}
                        onChange={(e) => setState(changeClientInfoAttribute(state, "redis_port", e.target.value))}
                    />
                </div>
            </div>
            <div className="input-group-column-action">
                <i
                    id={"job-client-info-remove-" + index}
                    className="material-icons opacity-10 input-group-action"
                    onClick={(e) =>
                        setState(
                            produce((newState) => {
                                newState.job.clients_info.splice(index, 1);
                            }),
                        )
                    }
                >
                    remove
                </i>
            </div>
        </div>
    );
}

export function EditJobClientOptions(): ReactElement {
    const { data, error, isLoading } = useGetClients();
    if (!data) {
        return null;
    }
    return data.map((d, i) => (
        <option key={i} value={d}>
            {d}
        </option>
    ));
}
