window.addEventListener("DOMContentLoaded", () => {
    const $ = (sel) => document.querySelector(sel);
    const messages = $("#messages");
    const input = $("#userInput");
    const sendBtn = $("#sendBtn");
    const tokenEl = $("#authToken");
    const userEl = $("#userId");
    const saveBtn = $("#saveSettings");

    if (!sendBtn) {
        console.error("sendBtn not found in DOM");
        return;
    }

    // restore settings
    tokenEl && (tokenEl.value = localStorage.getItem("chat_token") || "");
    userEl && (userEl.value = localStorage.getItem("chat_user") || "demo");

    saveBtn && saveBtn.addEventListener("click", () => {
        localStorage.setItem("chat_token", tokenEl?.value || "");
        localStorage.setItem("chat_user", userEl?.value || "demo");
    });

    function addBubble(role, text, meta) {
        const div = document.createElement("div");
        div.className = `bubble ${role}`;
        const metaHtml = meta ? `<div class=\"meta\">${meta}</div>` : "";
        div.innerHTML = `<div class=\"content\"></div>${metaHtml}`;
        div.querySelector(".content").textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }

    async function send() {
        const text = (input?.value || "").trim();
        if (!text) return;
        addBubble("user", text);
        if (input) input.value = "";

        const payload = {
            user_id: (userEl?.value || "demo").trim() || "demo",
            message: text,
        };
        const headers = {
            "Content-Type": "application/json"
        };
        const tok = (tokenEl?.value || "").trim();
        if (tok) headers["Authorization"] = `Bearer ${tok}`;

        try {
            sendBtn.disabled = true;
            sendBtn.setAttribute("aria-busy", "true");
            const res = await fetch("/api/v1/chat", {
                method: "POST",
                headers,
                body: JSON.stringify(payload),
            });
            if (!res.ok) {
                const txt = await res.text();
                addBubble("assistant", `Error: ${res.status} ${res.statusText} — ${txt}`);
                return;
            }
            const data = await res.json();
            const meta = [];
            if (data.used_tool) meta.push(`tool: ${data.used_tool}`);
            if (data.model_latency_ms != null) meta.push(`model: ${Number(data.model_latency_ms).toFixed(0)}ms`);
            if (data.tool_latency_ms != null && Number(data.tool_latency_ms) > 0) meta.push(`tool: ${Number(data.tool_latency_ms).toFixed(0)}ms`);
            addBubble("assistant", data.answer || "(no answer)", meta.join(" • "));
        } catch (e) {
            console.error(e);
            addBubble("assistant", `Network error: ${e}`);
        } finally {
            sendBtn.disabled = false;
            sendBtn.removeAttribute("aria-busy");
        }
    }

    // Wire events after DOM is ready
    sendBtn.addEventListener("click", (e) => {
        e.preventDefault();
        send();
    });
    input && input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });

    console.log("UI wired: handlers attached");
});