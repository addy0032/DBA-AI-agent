const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function fetchJson(endpoint: string) {
    const res = await fetch(`${API}${endpoint}`, {
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

async function postJson(endpoint: string, body: any = {}) {
    const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

export const observabilityApi = {
    // Server Health
    getServerHealth: () => fetchJson("/server/health"),
    getCpu: () => fetchJson("/server/cpu"),
    getMemory: () => fetchJson("/server/memory"),
    getWaits: () => fetchJson("/server/waits"),

    // Workload
    getSessions: () => fetchJson("/workload/sessions"),
    getBlocking: () => fetchJson("/workload/blocking"),
    getQueries: () => fetchJson("/workload/queries"),

    // I/O
    getIO: () => fetchJson("/io/files"),

    // Indexes
    getIndexes: () => fetchJson("/indexes/health"),

    // Query Store
    getQueryStore: () => fetchJson("/query-store/overview"),

    // Databases
    getDatabases: () => fetchJson("/databases/summary"),

    // Configuration
    getConfiguration: () => fetchJson("/configuration/audit"),

    // Admin
    getActiveDb: () => fetchJson("/admin/active-db"),
    listDatabases: () => fetchJson("/admin/databases"),
    switchDb: (database: string) => postJson("/admin/switch-db", { database }),
    refreshAll: () => postJson("/admin/refresh-all"),
};
