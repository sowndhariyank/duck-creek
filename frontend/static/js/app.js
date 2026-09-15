/**
 * Main Application Controller & Reactive SSE Parser.
 * Connects the UI to the backend streaming pipeline and animates the multi-agent mesh visualizer.
 * Wires topology nodes to the Agent Mesh I/O Dossier.
 */

document.addEventListener("DOMContentLoaded", () => {
    const componentFactory = new DynamicA2uiComponentFactory("dynamicA2uiContainer", "evidenceDrawer", "drawerBody");
    window.workbench = componentFactory;

    const btnRun = document.getElementById("btnRunUnderwriting");
    const submissionSelect = document.getElementById("submissionSelect");
    const telemetryFeed = document.getElementById("telemetryFeed");
    const btnCloseDrawer = document.getElementById("btnCloseDrawer");

    btnCloseDrawer.addEventListener("click", () => {
        document.getElementById("evidenceDrawer").classList.add("hidden");
    });

    btnRun.addEventListener("click", () => {
        const submissionId = submissionSelect.value;
        startUnderwritingStream(submissionId);
    });

    // Make all topology nodes clickable to inspect their I/O dossier
    document.querySelectorAll(".mesh-node").forEach(node => {
        node.addEventListener("click", () => {
            const rawId = node.id.replace("node_", "");
            window.workbench.focusAgentCard(rawId);
        });
    });

    function startUnderwritingStream(submissionId) {
        telemetryFeed.innerHTML = "";
        resetMeshNodes();
        
        btnRun.disabled = true;
        btnRun.innerText = "Underwriting in Progress...";

        const streamUrl = `/api/chat/stream?submission_id=${encodeURIComponent(submissionId)}`;
        const eventSource = new EventSource(streamUrl);

        eventSource.onmessage = (event) => {
            try {
                const rpcFrame = JSON.parse(event.data);
                handleRpcFrame(rpcFrame);
            } catch (err) {
                console.error("Error parsing SSE frame:", err);
            }
        };

        eventSource.onerror = (err) => {
            console.log("Stream completed or closed.");
            eventSource.close();
            btnRun.disabled = false;
            btnRun.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Re-Run Underwriting`;
        };
    }

    function handleRpcFrame(frame) {
        const { method, params } = frame;

        switch (method) {
            case "onAgentThought":
                appendTelemetry(params.author, params.message, "telemetry-thought");
                break;
            case "onAgentDelegation":
                appendTelemetry(params.author, `Delegating to [${params.target}]: ${params.message}`, "telemetry-thought");
                highlightAgentNode(params.target);
                break;
            case "onToolCall":
                appendTelemetry(params.author, `Executing Tool: [${params.tool}]`, "telemetry-tool");
                break;
            case "onSubagentCompleted":
                appendTelemetry(params.role_title, `Turn Finished. Emitted structured output.`, "telemetry-delivery");
                break;
            case "onUiComponentDelivery":
                appendTelemetry(params.author, "Delivering Dynamic A2UI Schema components.", "telemetry-delivery");
                componentFactory.render(params.payload);
                break;
            case "onStreamError":
                appendTelemetry("System", `Stream Error: ${params.error}`, "telemetry-item");
                break;
            default:
                console.warn("Unknown RPC method:", method);
        }
    }

    function appendTelemetry(author, message, cssClass) {
        const item = document.createElement("div");
        item.className = `telemetry-item ${cssClass}`;
        item.innerHTML = `<strong>${author}:</strong> ${message}`;
        telemetryFeed.appendChild(item);
        telemetryFeed.scrollTop = telemetryFeed.scrollHeight;
    }

    function highlightAgentNode(agentName) {
        document.querySelectorAll(".node-worker").forEach(n => n.classList.remove("node-active"));
        
        const targetNode = document.getElementById(`node_${agentName}`);
        if (targetNode) {
            targetNode.classList.add("node-active");
        }
    }

    function resetMeshNodes() {
        document.querySelectorAll(".node-worker").forEach(n => n.classList.remove("node-active"));
    }
});
