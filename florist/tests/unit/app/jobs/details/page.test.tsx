import "@testing-library/jest-dom";
import { render, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "@jest/globals";
import { act } from "react-dom/test-utils";

import { useGetJob, useSWRWithKey, getServerLogsKey, getClientLogsKey } from "../../../../../app/jobs/hooks";
import { validStatuses, JobData } from "../../../../../app/jobs/definitions";
import JobDetails, { getTimeString } from "../../../../../app/jobs/details/page";

const testJobId = "test-job-id";

jest.mock("../../../../../app/jobs/hooks");
jest.mock("next/navigation", () => ({
    ...require("next-router-mock"),
    useSearchParams: () => new Map([["id", testJobId]]),
}));
jest.useFakeTimers().setSystemTime(new Date("2020-01-01 12:12:12.1212"));

afterEach(() => {
    jest.clearAllMocks();
    cleanup();
});

function setupGetJobMock(data: JobData, isLoading: boolean = false, error = null) {
    useGetJob.mockImplementation((jobId: string) => {
        return { data, error, isLoading };
    });
}

function setupUseSWRWithKeyMock({ data, isLoading = false, error = null, isValidating = false }) {
    getServerLogsKey.mockImplementation((jobId) => `test server logs key: ${jobId}`);
    getClientLogsKey.mockImplementation((jobId, clientIndex) => `test client logs key: ${jobId}, ${clientIndex}`);

    const mutateMock = jest.fn();
    useSWRWithKey.mockImplementation((apiKey: string) => {
        return { data, error, isLoading, isValidating, mutate: mutateMock };
    });
    return mutateMock;
}

function setupURLSpyMock(urlSpy, testURL: string = "foo") {
    urlSpy = jest.spyOn(window, "URL");
    urlSpy.createObjectURL = jest.fn((_) => testURL);
    return urlSpy;
}

function makeTestJob(): JobData {
    return {
        _id: testJobId,
        status: "NOT_STARTED",
        model: "test-model",
        server_address: "test-server-address",
        redis_host: "test-redis-host",
        redis_port: "test-redis-port",
        server_config: JSON.stringify({
            test_attribute_1: "test-value-1",
            test_attribute_2: "test-value-2",
            n_server_rounds: 4,
            local_epochs: 2,
        }),
        server_metrics: JSON.stringify({
            host_type: "server",
            fit_start: "2020-01-01 12:07:07.0707",
            rounds: {
                "1": {
                    fit_round_start: "2020-01-01 12:08:08.0808",
                    fit_round_end: "2020-01-01 12:09:09.0909",
                    eval_round_start: "2020-01-01 12:08:09.0808",
                    eval_round_end: "2020-01-01 12:08:10.0808",
                    custom_property_value: "133.7",
                    custom_property_array: [1337, 1338],
                    custom_property_object: {
                        custom_property_object_value: "test",
                    },
                },
                "2": {
                    fit_round_start: "2020-01-01 12:10:10.1010",
                    fit_round_end: "2020-01-01 12:11:11.1111",
                    eval_round_start: "2020-01-01 12:11:09.0808",
                },
                "3": {
                    fit_round_start: "2020-01-01 12:12:00.1212",
                },
            },
            custom_property_value: "133.7",
            custom_property_array: [1337, 1338],
            custom_property_object: {
                custom_property_object_value: "test",
            },
        }),
        clients_info: [
            {
                client: "test-client-1",
                service_address: "test-service-address-1",
                data_path: "test-data-path-1",
                redis_host: "test-redis-host-1",
                redis_port: "test-redis-port-1",
                metrics: JSON.stringify({
                    host_type: "client",
                    initialized: "2024-10-10 15:05:59.025693",
                    shutdown: "2024-10-10 15:12:34.888213",
                    rounds: {
                        "1": {
                            fit_start: "2024-10-10 15:05:34.888213",
                            fit_end: "2024-10-10 15:06:59.032618",
                            eval_start: "2024-10-10 15:07:59.032618",
                            eval_end: "2024-10-10 15:08:34.888213",
                            round_end: "2024-10-10 15:08:34.888213",
                        },
                        "2": {
                            fit_start: "2024-10-10 15:06:59.032618",
                            fit_end: "2024-10-10 15:07:34.888213",
                            eval_start: "2024-10-10 15:08:34.888213",
                            eval_end: "2024-10-10 15:09:59.032618",
                            round_end: "2024-10-10 15:09:59.032618",
                        },
                        "3": {
                            fit_start: "2024-10-10 15:10:59.032618",
                            fit_end: "2024-10-10 15:11:34.888213",
                            eval_start: "2024-10-10 15:12:34.888213",
                            eval_end: "2024-10-10 15:13:59.032618",
                            round_end: "2024-10-10 15:14:59.032618",
                        },
                        "4": {
                            fit_start: "2024-10-10 15:15:59.032618",
                            fit_end: "2024-10-10 15:16:34.888213",
                            eval_start: "2024-10-10 15:17:34.888213",
                            eval_end: "2024-10-10 15:18:59.032618",
                            round_end: "2024-10-10 15:19:59.032618",
                        },
                    },
                }),
            },
            {
                client: "test-client-2",
                service_address: "test-service-address-2",
                data_path: "test-data-path-2",
                redis_host: "test-redis-host-2",
                redis_port: "test-redis-port-2",
                metrics: JSON.stringify({
                    host_type: "client",
                    initialized: "2024-10-10 15:05:59.025693",
                    rounds: {
                        "1": {
                            fit_start: "2024-10-10 15:05:34.888213",
                            fit_end: "2024-10-10 15:05:34.888213",
                            eval_start: "2024-10-10 15:08:34.888213",
                            eval_end: "2024-10-10 15:08:34.888213",
                            round_end: "2024-10-10 15:08:34.888213",
                        },
                        "2": {
                            fit_start: "2024-10-10 15:06:59.032618",
                        },
                    },
                }),
            },
        ],
    };
}

describe("Job Details Page", () => {
    it("Renders correctly", () => {
        const testJob = makeTestJob();
        setupGetJobMock(testJob);
        const { container } = render(<JobDetails />);

        expect(useGetJob).toBeCalledWith(testJobId);

        expect(container.querySelector("h1")).toHaveTextContent("Job Details");
        expect(container.querySelector("#job-details-id")).toHaveTextContent(testJob._id);
        expect(container.querySelector("#job-details-status")).toHaveTextContent(validStatuses[testJob.status]);
        expect(container.querySelector("#job-details-status")).toHaveClass("status-pill");
        expect(container.querySelector("#job-details-server-address")).toHaveTextContent(testJob.server_address);
        expect(container.querySelector("#job-details-redis-host")).toHaveTextContent(testJob.redis_host);
        const testServerConfig = JSON.parse(testJob.server_config);
        const serverConfigNames = Object.keys(testServerConfig);
        for (let i = 0; i < serverConfigNames.length; i++) {
            expect(container.querySelector(`#job-details-server-config-name-${i}`)).toHaveTextContent(
                serverConfigNames[i],
            );
            expect(container.querySelector(`#job-details-server-config-value-${i}`)).toHaveTextContent(
                testServerConfig[serverConfigNames[i]],
            );
        }
        for (let i = 0; i < testJob.clients_info.length; i++) {
            expect(container.querySelector(`#job-details-client-config-client-${i}`)).toHaveTextContent(
                testJob.clients_info[i].client,
            );
            expect(container.querySelector(`#job-details-client-config-service-address-${i}`)).toHaveTextContent(
                testJob.clients_info[i].service_address,
            );
            expect(container.querySelector(`#job-details-client-config-data-path-${i}`)).toHaveTextContent(
                testJob.clients_info[i].data_path,
            );
            expect(container.querySelector(`#job-details-client-config-redis-host-${i}`)).toHaveTextContent(
                testJob.clients_info[i].redis_host,
            );
            expect(container.querySelector(`#job-details-client-config-redis-port-${i}`)).toHaveTextContent(
                testJob.clients_info[i].redis_port,
            );
        }
    });
    describe("Status", () => {
        it("Renders NOT_STARTED correctly", () => {
            const testJob = makeTestJob();
            testJob.status = "NOT_STARTED";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const statusComponent = container.querySelector("#job-details-status");
            expect(statusComponent).toHaveTextContent(validStatuses[testJob.status]);
            expect(statusComponent).toHaveClass("alert-info");
            const iconComponent = statusComponent.querySelector("#job-details-status-icon");
            expect(iconComponent).toHaveTextContent("radio_button_checked");
        });
        it("Renders IN_PROGRESS correctly", () => {
            const testJob = makeTestJob();
            testJob.status = "IN_PROGRESS";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const statusComponent = container.querySelector("#job-details-status");
            expect(statusComponent).toHaveTextContent(validStatuses[testJob.status]);
            expect(statusComponent).toHaveClass("alert-warning");
            const iconComponent = statusComponent.querySelector("#job-details-status-icon");
            expect(iconComponent).toHaveTextContent("sync");
        });
        it("Renders FINISHED_SUCCESSFULLY correctly", () => {
            const testJob = makeTestJob();
            testJob.status = "FINISHED_SUCCESSFULLY";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const statusComponent = container.querySelector("#job-details-status");
            expect(statusComponent).toHaveTextContent(validStatuses[testJob.status]);
            expect(statusComponent).toHaveClass("alert-success");
            const iconComponent = statusComponent.querySelector("#job-details-status-icon");
            expect(iconComponent).toHaveTextContent("check_circle");
        });
        it("Renders FINISHED_WITH_ERROR correctly", () => {
            const testJob = makeTestJob();
            testJob.status = "FINISHED_WITH_ERROR";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const statusComponent = container.querySelector("#job-details-status");
            expect(statusComponent).toHaveTextContent(validStatuses[testJob.status]);
            expect(statusComponent).toHaveClass("alert-danger");
            const iconComponent = statusComponent.querySelector("#job-details-status-icon");
            expect(iconComponent).toHaveTextContent("error");
        });
        it("Renders unknown status correctly", () => {
            const testJob = makeTestJob();
            testJob.status = "some inexistent status";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const statusComponent = container.querySelector("#job-details-status");
            expect(statusComponent).toHaveTextContent(testJob.status);
            expect(statusComponent).toHaveClass("alert-secondary");
            const iconComponent = statusComponent.querySelector("#job-details-status-icon");
            expect(iconComponent).toHaveTextContent("");
        });
    });
    describe("Job progress", () => {
        it("Does not display when there are no server metrics", () => {
            const testJob = makeTestJob();
            testJob.server_metrics = null;
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const jobProgressComponent = container.querySelector("#job-progress");
            expect(jobProgressComponent).toBeNull();
        });
        it("Display progress bar at 0% when there are no information about rounds", () => {
            const testJob = makeTestJob();
            testJob.server_metrics = JSON.stringify({});
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar.getAttribute("style")).toBe("width: 100%;");
            expect(progressBar).toHaveTextContent("0%");
            expect(progressBar).toHaveClass("bg-disabled");
        });
        it("Display progress bar at 0% when rounds list is empty", () => {
            const testJob = makeTestJob();
            testJob.server_metrics = JSON.stringify({ rounds: {} });
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar.getAttribute("style")).toBe("width: 100%;");
            expect(progressBar).toHaveTextContent("0%");
            expect(progressBar).toHaveClass("bg-disabled");
        });
        it("Display progress bar at with correct progress percent", () => {
            setupGetJobMock(makeTestJob());
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar.getAttribute("style")).toBe("width: 50%;");
            expect(progressBar).toHaveTextContent("50%");
        });
        it("Display progress bar with correct class for NOT_STARTED status", () => {
            const testJob = makeTestJob();
            testJob.status = "NOT_STARTED";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar).toHaveClass("progress-bar-striped");
        });
        it("Display progress bar with correct class for IN_PROGRESS status", () => {
            const testJob = makeTestJob();
            testJob.status = "IN_PROGRESS";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar).toHaveClass("bg-warning");
        });
        it("Display progress bar with correct class for FINISHED_SUCCESSFULLY status", () => {
            const testJob = makeTestJob();
            testJob.status = "FINISHED_SUCCESSFULLY";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar).toHaveClass("bg-success");
        });
        it("Display progress bar with correct class for FINISHED_WITH_ERROR status", () => {
            const testJob = makeTestJob();
            testJob.status = "FINISHED_WITH_ERROR";
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const progressBar = container.querySelector("div.progress-bar");
            expect(progressBar).toHaveClass("bg-danger");
        });
        describe("Details", () => {
            let urlSpy;
            afterEach(() => {
                if (urlSpy) {
                    // making sure the mock is clear even on error,
                    // otherwise some weird errors start popping up
                    urlSpy.mockRestore();
                }
            });
            it("Should be collapsed by default", () => {
                setupGetJobMock(makeTestJob());
                const { container } = render(<JobDetails />);
                const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                expect(jobProgressDetailsComponent).toBeNull();
            });
            it("Should open when the toggle button is clicked", () => {
                setupGetJobMock(makeTestJob());
                setupURLSpyMock(urlSpy);
                const { container } = render(<JobDetails />);
                const toggleButton = container.querySelector(".job-details-toggle a");
                expect(toggleButton).toHaveTextContent("Expand");

                act(() => toggleButton.click());

                expect(toggleButton).toHaveTextContent("Collapse");

                const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                expect(jobProgressDetailsComponent).not.toBeNull();
            });
            it("Should render the contents correctly", () => {
                const testJob = makeTestJob();
                const serverMetrics = JSON.parse(testJob.server_metrics);
                setupGetJobMock(testJob);
                setupURLSpyMock(urlSpy);
                const { container } = render(<JobDetails />);
                const toggleButton = container.querySelector(".job-details-toggle a");
                act(() => toggleButton.click());

                const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                const elapsedTime = jobProgressDetailsComponent.children[0];
                expect(elapsedTime.children[0]).toHaveTextContent("Elapsed time:");
                expect(elapsedTime.children[1]).toHaveTextContent("05m 05s");
                const fitStart = jobProgressDetailsComponent.children[1];
                expect(fitStart.children[0]).toHaveTextContent("Start time:");
                expect(fitStart.children[1]).toHaveTextContent(serverMetrics.fit_start);
                const fitEnd = jobProgressDetailsComponent.children[2];
                expect(fitEnd.children[0]).toHaveTextContent("End time:");
                expect(fitEnd.children[1]).toHaveTextContent("");

                // custom properties
                const customPropertyValue = jobProgressDetailsComponent.children[3];
                expect(customPropertyValue.children[0]).toHaveTextContent("custom_property_value");
                expect(customPropertyValue.children[1]).toHaveTextContent(serverMetrics.custom_property_value);
                const customPropertyArray = jobProgressDetailsComponent.children[4];
                expect(customPropertyArray.children[0]).toHaveTextContent("custom_property_array");
                expect(customPropertyArray.children[1]).toHaveTextContent(
                    JSON.stringify(serverMetrics.custom_property_array),
                );
                const customPropertyObject = jobProgressDetailsComponent.children[5];
                expect(customPropertyObject.children[0]).toHaveTextContent("custom_property_object");
                const customPropertyObjectValue = customPropertyObject.children[1];
                expect(customPropertyObjectValue.children[0].children[0]).toHaveTextContent(
                    "custom_property_object_value",
                );
                expect(customPropertyObjectValue.children[0].children[1]).toHaveTextContent(
                    serverMetrics.custom_property_object.custom_property_object_value,
                );

                // rounds
                const round1 = jobProgressDetailsComponent.children[6].children[0];
                expect(round1.children[0]).toHaveTextContent("Round 1");
                expect(round1.children[1]).toHaveClass("job-round-toggle-0");
                const round2 = jobProgressDetailsComponent.children[7].children[0];
                expect(round2.children[0]).toHaveTextContent("Round 2");
                expect(round2.children[1]).toHaveClass("job-round-toggle-1");
                const round3 = jobProgressDetailsComponent.children[8].children[0];
                expect(round3.children[0]).toHaveTextContent("Round 3");
                expect(round3.children[1]).toHaveClass("job-round-toggle-2");

                // show logs
                const showLogs = jobProgressDetailsComponent.children[9];
                expect(showLogs.children[0]).toHaveTextContent("Logs:");
                const showLogsButton = showLogs.children[1].children[0];
                expect(showLogsButton.tagName.toLowerCase()).toBe("a");
                expect(showLogsButton).toHaveTextContent("Show Logs");
            });
            describe("Rounds", () => {
                it("Should be collapsed by default", () => {
                    const testJob = makeTestJob();
                    const serverMetrics = JSON.parse(testJob.server_metrics);
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy);
                    const { container } = render(<JobDetails />);
                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    for (let i = 0; i < Object.keys(serverMetrics.rounds).length; i++) {
                        const jobRoundDetailsComponent = container.querySelector(`#job-round-details-${i}`);
                        expect(jobRoundDetailsComponent).toBeNull();
                    }
                });
                it("Should open when the toggle button is clicked", () => {
                    const testJob = makeTestJob();
                    const serverMetrics = JSON.parse(testJob.server_metrics);
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy);
                    const { container } = render(<JobDetails />);
                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    for (let i = 0; i < Object.keys(serverMetrics.rounds).length; i++) {
                        const toggleButton = container.querySelector(`.job-round-toggle-${i} a`);
                        expect(toggleButton).toHaveTextContent("Expand");

                        act(() => toggleButton.click());

                        expect(toggleButton).toHaveTextContent("Collapse");

                        const jobRoundDetailsComponent = container.querySelector(`.job-round-details-${i}`);
                        expect(jobRoundDetailsComponent).not.toBeNull();
                    }
                });
                it("Should render the contents correctly", () => {
                    const testJob = makeTestJob();
                    const serverMetrics = JSON.parse(testJob.server_metrics);
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy);
                    const { container } = render(<JobDetails />);
                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const serverRounds = serverMetrics.rounds;
                    const expectedTimes = {
                        fit: [
                            ["01m 01s", serverRounds["1"].fit_round_start, serverRounds["1"].fit_round_end],
                            ["01m 01s", serverRounds["2"].fit_round_start, serverRounds["2"].fit_round_end],
                            ["12s", serverRounds["3"].fit_round_start, ""],
                        ],
                        evaluate: [
                            ["01s", serverRounds["1"].eval_round_start, serverRounds["1"].eval_round_end],
                            ["01m 03s", serverRounds["2"].eval_round_start, ""],
                            ["", "", ""],
                        ],
                    };

                    for (let i = 0; i < Object.keys(expectedTimes.fit).length; i++) {
                        const toggleButton = container.querySelector(`.job-round-toggle-${i} a`);
                        act(() => toggleButton.click());

                        const jobRoundDetailsComponent = container.querySelector(`.job-round-details-${i}`);
                        const fitElapsedTime = jobRoundDetailsComponent.children[0];
                        expect(fitElapsedTime.children[0]).toHaveTextContent("Fit elapsed time:");
                        expect(fitElapsedTime.children[1]).toHaveTextContent(expectedTimes.fit[i][0]);
                        const fitStart = jobRoundDetailsComponent.children[1];
                        expect(fitStart.children[0]).toHaveTextContent("Fit start time:");
                        expect(fitStart.children[1]).toHaveTextContent(expectedTimes.fit[i][1]);
                        const fitEnd = jobRoundDetailsComponent.children[2];
                        expect(fitEnd.children[0]).toHaveTextContent("Fit end time:");
                        expect(fitEnd.children[1]).toHaveTextContent(expectedTimes.fit[i][2]);
                        const evaluateElapsedTime = jobRoundDetailsComponent.children[3];
                        expect(evaluateElapsedTime.children[0]).toHaveTextContent("Evaluate elapsed time:");
                        expect(evaluateElapsedTime.children[1]).toHaveTextContent(expectedTimes.evaluate[i][0]);
                        const evaluateStart = jobRoundDetailsComponent.children[4];
                        expect(evaluateStart.children[0]).toHaveTextContent("Evaluate start time:");
                        expect(evaluateStart.children[1]).toHaveTextContent(expectedTimes.evaluate[i][1]);
                        const evaluateEnd = jobRoundDetailsComponent.children[5];
                        expect(evaluateEnd.children[0]).toHaveTextContent("Evaluate end time:");
                        expect(evaluateEnd.children[1]).toHaveTextContent(expectedTimes.evaluate[i][2]);
                    }

                    // custom properties
                    const jobRoundDetailsComponent = container.querySelector(`.job-round-details-${0}`);
                    const customPropertyValue = jobRoundDetailsComponent.children[6];
                    expect(customPropertyValue.children[0]).toHaveTextContent("custom_property_value");
                    expect(customPropertyValue.children[1]).toHaveTextContent(serverMetrics.custom_property_value);
                    const customPropertyArray = jobRoundDetailsComponent.children[7];
                    expect(customPropertyArray.children[0]).toHaveTextContent("custom_property_array");
                    expect(customPropertyArray.children[1]).toHaveTextContent(
                        JSON.stringify(serverMetrics.custom_property_array),
                    );
                    const customPropertyObject = jobRoundDetailsComponent.children[8];
                    expect(customPropertyObject.children[0]).toHaveTextContent("custom_property_object");
                    const customPropertyObjectValue = customPropertyObject.children[1];
                    expect(customPropertyObjectValue.children[0].children[0]).toHaveTextContent(
                        "custom_property_object_value",
                    );
                    expect(customPropertyObjectValue.children[0].children[1]).toHaveTextContent(
                        serverMetrics.custom_property_object.custom_property_object_value,
                    );
                });
            });
            describe("Logs Modal", () => {
                it("Should be hidden by default", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    expect(jobProgressDetailsComponent.querySelector(".log-viewer")).toBeNull();
                });
                it("Should render the server logs modal correctly when clicked", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy, "test url");
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const testLogContents = "[INFO] test log contents\n[INFO] second line";
                    setupUseSWRWithKeyMock({ data: testLogContents });
                    const testURL = "test url";
                    urlSpy = setupURLSpyMock(urlSpy, testURL);

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));
                    expect(urlSpy.createObjectURL).toHaveBeenCalledWith(new Blob([testLogContents]));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    expect(logViewerComponent).toHaveClass("modal", "show");

                    const downloadButton = logViewerComponent.querySelector(".download-button");
                    expect(downloadButton.getAttribute("href")).toBe(testURL);
                    expect(downloadButton.getAttribute("download")).toBe("server.log");

                    const modalBody = logViewerComponent.querySelector(".modal-body");
                    expect(modalBody).toHaveTextContent(testLogContents.replace(/\n/g, " "));
                });
                it("Should render the client logs modal correctly when clicked", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy, "test url");
                    const { container } = render(<JobDetails />);

                    const testClientIndex = 1;
                    let toggleButton = container.querySelectorAll(".job-client-progress .job-details-toggle a")[
                        testClientIndex
                    ];
                    act(() => toggleButton.click());

                    const testLogContents = "[INFO] test log contents\n[INFO] second line";
                    setupUseSWRWithKeyMock({ data: testLogContents });
                    const testURL = "test url";
                    urlSpy = setupURLSpyMock(urlSpy, testURL);

                    const jobProgressDetailsComponent = container.querySelector(
                        `#job-details-client-config-progress-${testClientIndex} .job-progress-detail`,
                    );
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getClientLogsKey(testJob._id, testClientIndex));
                    expect(urlSpy.createObjectURL).toHaveBeenCalledWith(new Blob([testLogContents]));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    expect(logViewerComponent).toHaveClass("modal", "show");

                    const downloadButton = logViewerComponent.querySelector(".download-button");
                    expect(downloadButton.getAttribute("href")).toBe(testURL);
                    expect(downloadButton.getAttribute("download")).toBe(`client-${testClientIndex}.log`);

                    const modalBody = logViewerComponent.querySelector(".modal-body");
                    expect(modalBody).toHaveTextContent(testLogContents.replace(/\n/g, " "));
                });
                it("Should display spinner when loading", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    setupUseSWRWithKeyMock({ data: null, isLoading: true });

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    const modalBody = logViewerComponent.querySelector(".modal-body");
                    const loadingComponent = modalBody.querySelector("div.loading-container > img");
                    expect(loadingComponent.getAttribute("alt")).toBe("Loading Logs");
                });
                it("Should display spinner when validating", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    setupUseSWRWithKeyMock({ data: null, isValidating: true });

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    const modalBody = logViewerComponent.querySelector(".modal-body");
                    const loadingComponent = modalBody.querySelector("div.loading-container > img");
                    expect(loadingComponent.getAttribute("alt")).toBe("Loading Logs");
                });
                it("Should display error message", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy, "test url");
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    setupUseSWRWithKeyMock({ data: null, error: "error!" });

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    const modalBody = logViewerComponent.querySelector(".modal-body");
                    expect(modalBody).toHaveTextContent("Error loading logs");
                });
                it("Clicking refresh should call mutate", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy, "test url");
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const mutateMock = setupUseSWRWithKeyMock({ data: null });

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    const refreshButton = logViewerComponent.querySelector(".refresh-button");
                    act(() => refreshButton.click());

                    expect(mutateMock).toHaveBeenCalledWith(getServerLogsKey(testJob._id));
                });
                it("Clicking close should close the modal", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy, "test url");
                    const { container } = render(<JobDetails />);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const mutateMock = setupUseSWRWithKeyMock({ data: null });

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const showLogsButton = jobProgressDetailsComponent.querySelector(".show-logs-button");
                    act(() => showLogsButton.click());

                    expect(useSWRWithKey).toHaveBeenCalledWith(getServerLogsKey(testJob._id));

                    const logViewerComponent = jobProgressDetailsComponent.querySelector(".log-viewer");
                    const closeButton = logViewerComponent.querySelector(".btn-close");
                    act(() => closeButton.click());

                    expect(jobProgressDetailsComponent.querySelector(".log-viewer")).toBeNull();
                });
            });
            describe("Download metrics", () => {
                it("Should render the download server metrics button correctly", async () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);

                    const testURL = "test url";
                    urlSpy = setupURLSpyMock(urlSpy, testURL);

                    const progressToggleButton = container.querySelector(".job-details-toggle a");
                    act(() => progressToggleButton.click());

                    const expectedServerMetrics = JSON.stringify(JSON.parse(testJob.server_metrics), null, 4);
                    expect(urlSpy.createObjectURL).toHaveBeenCalledWith(new Blob([expectedServerMetrics]));

                    const jobProgressDetailsComponent = container.querySelector(".job-progress-detail");
                    const downloadMetricsButton = jobProgressDetailsComponent.querySelector(".download-metrics-button");
                    expect(downloadMetricsButton.getAttribute("href")).toBe(testURL);
                    expect(downloadMetricsButton.getAttribute("download")).toBe("server-metrics.json");
                });
                it("Should render the download client metrics button correctly", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);

                    const testURL = "test url";
                    urlSpy = setupURLSpyMock(urlSpy, testURL);

                    const testClientIndex = 1;
                    let toggleButton = container.querySelectorAll(".job-client-progress .job-details-toggle a")[
                        testClientIndex
                    ];
                    act(() => toggleButton.click());

                    const expectedClientMetrics = JSON.stringify(
                        JSON.parse(testJob.clients_info[testClientIndex].metrics),
                        null,
                        4,
                    );
                    expect(urlSpy.createObjectURL).toHaveBeenCalledWith(new Blob([expectedClientMetrics]));

                    const clientProgressDetailsComponent = container.querySelector(
                        `#job-details-client-config-progress-${testClientIndex} .job-progress-detail`,
                    );
                    const downloadMetricsButton =
                        clientProgressDetailsComponent.querySelector(".download-metrics-button");
                    expect(downloadMetricsButton.getAttribute("href")).toBe(testURL);
                    expect(downloadMetricsButton.getAttribute("download")).toBe(
                        `client-metrics-${testClientIndex}.json`,
                    );
                });
            });
            describe("Clients", () => {
                it("Renders their progress bars correctly", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    const { container } = render(<JobDetails />);
                    const clientsProgress = container.querySelectorAll(".job-client-progress");

                    let progressBar = clientsProgress[0].querySelector("div.progress-bar");
                    expect(progressBar).toHaveClass("bg-success");
                    expect(progressBar).toHaveTextContent("100%");

                    progressBar = clientsProgress[1].querySelector("div.progress-bar");
                    expect(progressBar).toHaveClass("bg-warning");
                    expect(progressBar).toHaveTextContent("25%");
                });
                it("Renders the progress details correctly", () => {
                    const testJob = makeTestJob();
                    setupGetJobMock(testJob);
                    setupURLSpyMock(urlSpy);
                    const { container } = render(<JobDetails />);

                    let toggleButton = container.querySelectorAll(".job-client-progress .job-details-toggle a")[0];
                    act(() => toggleButton.click());

                    let clientMetrics = JSON.parse(testJob.clients_info[0].metrics);
                    let progressDetailsComponent = container.querySelectorAll(
                        ".job-client-progress .job-progress-detail",
                    )[0];
                    let elapsedTime = progressDetailsComponent.children[0];
                    expect(elapsedTime.children[0]).toHaveTextContent("Elapsed time:");
                    expect(elapsedTime.children[1]).toHaveTextContent("06m 35s");
                    let fitStart = progressDetailsComponent.children[1];
                    expect(fitStart.children[0]).toHaveTextContent("Start time:");
                    expect(fitStart.children[1]).toHaveTextContent(clientMetrics.initialized);
                    let fitEnd = progressDetailsComponent.children[2];
                    expect(fitEnd.children[0]).toHaveTextContent("End time:");
                    expect(fitEnd.children[1]).toHaveTextContent(clientMetrics.shutdown);

                    toggleButton = container.querySelectorAll(".job-client-progress .job-details-toggle a")[1];
                    act(() => toggleButton.click());
                    clientMetrics = JSON.parse(testJob.clients_info[1].metrics);
                    progressDetailsComponent = container.querySelectorAll(
                        ".job-client-progress .job-progress-detail",
                    )[1];
                    elapsedTime = progressDetailsComponent.children[0];
                    expect(elapsedTime.children[0]).toHaveTextContent("Elapsed time:");
                    expect(elapsedTime.children[1]).toHaveTextContent("06m 13s");
                    fitStart = progressDetailsComponent.children[1];
                    expect(fitStart.children[0]).toHaveTextContent("Start time:");
                    expect(fitStart.children[1]).toHaveTextContent(clientMetrics.initialized);
                    fitEnd = progressDetailsComponent.children[2];
                    expect(fitEnd.children[0]).toHaveTextContent("End time:");
                    expect(fitEnd.children[1]).toHaveTextContent("");
                });
            });
        });
    });
    describe("Server config", () => {
        it("Does not break when it's null", () => {
            const testJob = makeTestJob();
            testJob.server_config = null;
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const serverConfigComponent = container.querySelector("#job-details-server-config-empty");
            expect(serverConfigComponent).toHaveTextContent("Empty.");
        });
        it("Does not break when it's an empty dictionary", () => {
            const testJob = makeTestJob();
            testJob.server_config = JSON.stringify({});
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const serverConfigComponent = container.querySelector("#job-details-server-config-empty");
            expect(serverConfigComponent).toHaveTextContent("Empty.");
        });
        it("Does not break when it's not a dictionary", () => {
            const testJob = makeTestJob();
            testJob.server_config = JSON.stringify(["bad server config"]);
            setupGetJobMock(testJob);
            const { container } = render(<JobDetails />);
            const serverConfigComponent = container.querySelector("#job-details-server-config-error");
            expect(serverConfigComponent).toHaveTextContent("Error parsing server configuration.");
        });
    });
    it("Renders loading gif correctly", () => {
        setupGetJobMock(null, true);
        const { container } = render(<JobDetails />);
        const loadingComponent = container.querySelector("img#job-details-loading");
        expect(loadingComponent.getAttribute("alt")).toBe("Loading");
    });
    it("Renders error message when job is null", () => {
        setupGetJobMock(null);
        const { container } = render(<JobDetails />);
        expect(container.querySelector("#job-details-error")).toHaveTextContent("Error retrieving job.");
    });
    it("Renders error message when there is an error", () => {
        setupGetJobMock({}, false, "error");
        const { container } = render(<JobDetails />);
        expect(container.querySelector("#job-details-error")).toHaveTextContent("Error retrieving job.");
    });
    describe("getTimeString function", () => {
        it("Renders time strings correctly", () => {
            expect(getTimeString(123)).toBe("123ms");
            expect(getTimeString(1234)).toBe("01s 234ms");
            expect(getTimeString(9765)).toBe("09s 765ms");
            expect(getTimeString(12349)).toBe("12s");
            expect(getTimeString(123498)).toBe("02m 03s");
            expect(getTimeString(1234987)).toBe("20m 34s");
            expect(getTimeString(12349873)).toBe("03h 25m 49s");
            expect(getTimeString(82349873)).toBe("22h 52m 29s");
            expect(getTimeString(182349873)).toBe("50h 39m 09s");
        });
    });
});
