import "@testing-library/jest-dom";
import { getByText, render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { describe, it, expect, afterEach } from "@jest/globals";
import { act } from "react-dom/test-utils";

import Page from "../../../../app/jobs/page";
import { validStatuses } from "../../../../app/jobs/definitions";
import { useGetJobsByJobStatus, usePost } from "../../../../app/jobs/hooks";
import { after } from "node:test";

jest.mock("../../../../app/jobs/hooks");

afterEach(() => {
    jest.clearAllMocks();
    cleanup();
});

function mockJobData(model: string, serverAddress: string, clientServicesAddresses: Array<string>) {
    const data = {
        _id: "test-id",
        model: model,
        server_address: serverAddress,
        clients_info: clientServicesAddresses.map((clientServicesAddress) => ({
            service_address: clientServicesAddress,
        })),
    };
    return data;
}

function mockUseGetJobsByJobStatus(
    status: string,
    validStatuses: Array<string>,
    data: Array<object>,
    error: boolean,
    isLoading: boolean,
) {
    if (validStatuses.includes(status)) {
        return {
            data,
            error,
            isLoading,
        };
    } else {
        return {
            data: [],
            error: false,
            isLoading: false,
        };
    }
}

function mockUsePost(postMock, isLoading) {
    return {
        post: postMock,
        response: null,
        isLoading: isLoading,
        error: null,
    };
}

function setupMock(
    validStatuses: Array<string>,
    data: Array<object>,
    error: boolean,
    isLoading: boolean,
    isPostLoading: boolean,
) {
    useGetJobsByJobStatus.mockImplementation((status: string) =>
        mockUseGetJobsByJobStatus(status, validStatuses, data, error, isLoading),
    );
    const postMock = jest.fn();
    usePost.mockImplementation(() => mockUsePost(postMock, isPostLoading));
    return postMock;
}

describe("List Jobs Page", () => {
    it("Renders Page Header Correctly", () => {
        setupMock([], [], false, false, false);
        const { container } = render(<Page />);
        const h1 = container.querySelector("h1");
        expect(h1).toBeInTheDocument();
        expect(h1).toHaveTextContent("Jobs");
        const newJobButton = container.querySelector("#new-job-button");
        expect(newJobButton).toBeInTheDocument();
        expect(newJobButton.href.endsWith("/jobs/edit")).toBeTruthy();
    });

    it("Renders Status Components Headers", () => {
        const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
        const validStatusesKeys = Object.keys(validStatuses);

        setupMock(validStatusesKeys, data, false, false, false);
        const { getByTestId } = render(<Page />);

        for (const status of validStatusesKeys) {
            const element = getByTestId(`status-header-${status}`);
            expect(element).toBeInTheDocument();
            expect(element).toHaveTextContent(validStatuses[status]);
        }
    });

    it("Renders Status Table With Table with Data", () => {
        const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
        const validStatusesKeys = Object.keys(validStatuses);

        setupMock(validStatusesKeys, data, false, false, false);

        const { getByTestId } = render(<Page />);

        for (const status of validStatusesKeys) {
            const element = getByTestId(`status-table-${status}`);
            expect(getByText(element, "Model")).toBeInTheDocument();
            expect(getByText(element, "Server Address")).toBeInTheDocument();
            expect(getByText(element, "Client Service Addresses")).toBeInTheDocument();
            expect(getByText(element, "MNIST")).toBeInTheDocument();
            expect(getByText(element, "localhost:8080")).toBeInTheDocument();
            expect(getByText(element, "localhost:7080")).toBeInTheDocument();
        }
    });

    it("Renders Status Table without Data", () => {
        setupMock([], [], false, false, false);
        const { getByTestId } = render(<Page />);

        for (const status of Object.keys(validStatuses)) {
            const element = getByTestId(`status-no-jobs-${status}`);
            expect(getByText(element, "No jobs to display.")).toBeInTheDocument();
        }
    });

    it("Renders Loading GIF only when all isLoading", () => {
        setupMock(
            ["NOT_STARTED", "IN_PROGRESS", "FINISHED_SUCCESSFULLY", "FINISHED_WITH_ERROR"],
            [],
            false,
            true,
            false,
        );
        const { getByTestId } = render(<Page />);
        const element = getByTestId("jobs-page-loading-gif");
        expect(element).toBeInTheDocument();
    });

    it("Doesn't Render Loading GIF when not Loading", () => {
        setupMock(
            ["NOT_STARTED", "IN_PROGRESS", "FINISHED_SUCCESSFULLY", "FINISHED_WITH_ERROR"],
            [],
            false,
            false,
            false,
        );
        const { queryByTestId } = render(<Page />);
        const element = queryByTestId("jobs-page-loading-gif");
        expect(element).not.toBeInTheDocument();
    });

    it("Details button is present on all statuses", () => {
        const data = mockJobData("MNIST", "localhost:8080", ["localhost:7080"]);
        const validStatusesKeys = Object.keys(validStatuses);

        setupMock(validStatusesKeys, [data], false, false, false);
        const { queryByTestId } = render(<Page />);

        for (let status of validStatusesKeys) {
            const element = queryByTestId(`job-details-button-${status}-0`);
            expect(element.getAttribute("title")).toBe("Details");
            expect(element.getAttribute("href")).toBe(`jobs/details?id=${data._id}`);
        }
    });

    describe("Start training button", () => {
        it("Is present in NOT_STARTED jobs", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const validStatusesKeys = Object.keys(validStatuses);
            const statuses = ["NOT_STARTED"];

            setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const startTrainingButton = queryByTestId("start-training-button-0");
            const startTrainingIcon = startTrainingButton.querySelector("i");

            expect(startTrainingButton).toBeInTheDocument();
            expect(startTrainingButton).toHaveClass("btn-primary");
            expect(startTrainingIcon).toHaveClass("material-icons");
            expect(startTrainingIcon).toHaveTextContent("play_circle_outline");
        });

        it("Is not present without NOT_STARTED jobs", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["IN_PROGRESS", "FINISHED_WITH_ERROR", "FINISHED_SUCCESSFULLY"];

            setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const startTrainingButton = queryByTestId("start-training-button-0");
            expect(startTrainingButton).not.toBeInTheDocument();
        });

        it("Clicking it will call the backend API", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["NOT_STARTED"];

            const postMock = setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const startTrainingButton = queryByTestId("start-training-button-0");

            act(() => startTrainingButton.click());

            expect(postMock).toHaveBeenCalledWith("/api/server/training/start?job_id=test-id", "{}");
        });

        it("Should be disabled and display a spinner when loading", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["NOT_STARTED"];

            const postMock = setupMock(statuses, data, false, false, true);
            const { queryByTestId } = render(<Page />);
            const startTrainingButton = queryByTestId("start-training-button-0");
            const startTrainingSpinner = startTrainingButton.querySelector("span");

            expect(startTrainingButton).not.toHaveClass("btn-primary");
            expect(startTrainingButton).toHaveClass("btn-secondary", "disabled");
            expect(startTrainingSpinner).toHaveClass("spinner-border");
        });
    });

    describe("Stop training button", () => {
        it("Is present in IN_PROGRESS jobs", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["IN_PROGRESS"];

            setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const stopTrainingButton = queryByTestId("stop-training-button-0");
            const stopTrainingIcon = stopTrainingButton.querySelector("i");

            expect(stopTrainingButton).toBeInTheDocument();
            expect(stopTrainingButton).toHaveClass("btn-primary");
            expect(stopTrainingIcon).toHaveClass("material-icons");
            expect(stopTrainingIcon).toHaveTextContent("stop");
        });

        it("Is not present without IN_PROGRESS jobs", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["NOT_STARTED", "FINISHED_WITH_ERROR", "FINISHED_SUCCESSFULLY"];

            setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const stopTrainingButton = queryByTestId("stop-training-button-0");
            expect(stopTrainingButton).not.toBeInTheDocument();
        });

        it("Clicking it will call the backend API", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["IN_PROGRESS"];

            const postMock = setupMock(statuses, data, false, false, false);
            const { queryByTestId } = render(<Page />);
            const stopTrainingButton = queryByTestId("stop-training-button-0");

            act(() => stopTrainingButton.click());

            expect(postMock).toHaveBeenCalledWith("/api/server/job/stop/test-id", "{}");
        });

        it("Should be disabled and display a spinner when loading", () => {
            const data = [mockJobData("MNIST", "localhost:8080", ["localhost:7080"])];
            const statuses = ["IN_PROGRESS"];

            const postMock = setupMock(statuses, data, false, false, true);
            const { queryByTestId } = render(<Page />);
            const stopTrainingButton = queryByTestId("stop-training-button-0");
            const stopTrainingSpinner = stopTrainingButton.querySelector("span");

            expect(stopTrainingButton).not.toHaveClass("btn-primary");
            expect(stopTrainingButton).toHaveClass("btn-secondary", "disabled");
            expect(stopTrainingSpinner).toHaveClass("spinner-border");
        });
    });
});
