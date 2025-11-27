const API_URL = "http://localhost:5000/api";

export const getStatus = async () => {
    try {
        const response = await fetch(`${API_URL}/status`);
        return await response.json();
    } catch (error) {
        return { status: "error", message: error.message };
    }
};

export const getDirectories = async () => {
    const response = await fetch(`${API_URL}/directories`);
    return await response.json();
};

// export const addDirectory = async (paths) => {
//     // Check if input is an array (new bulk add) or string (legacy)
//     const payload = Array.isArray(paths) ? { paths } : { path: paths };

//     const response = await fetch(`${API_URL}/directories`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//     });
//     return await response.json();
// };

export async function addDirectory(path) {
    const res = await fetch(`${API_URL}/directories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
    });
    return await res.json();
}

export const removeDirectory = async (path) => {
    const response = await fetch(`${API_URL}/directories`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
    });
    return await response.json();
};

export const checkIntegrity = async () => {
    const response = await fetch(`${API_URL}/check`, {
        method: "POST",
    });
    return await response.json();
};

export const getLogs = async () => {
    const response = await fetch(`${API_URL}/logs`);
    return await response.json();
};

export const exportLogs = async (logs, shift) => {
    try {
        const response = await fetch(`${API_URL}/logs/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ logs, shift }),
        });
        return await response.json();
    } catch (error) {
        return { error: 'Failed to export logs' };
    }
};

export const decryptText = async (text, shift) => {
    try {
        const response = await fetch(`${API_URL}/decrypt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, shift }),
        });
        return await response.json();
    } catch (error) {
        return { error: 'Failed to decrypt text' };
    }
};
