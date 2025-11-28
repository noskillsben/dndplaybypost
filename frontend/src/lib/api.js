import { API_URL } from "./config";
import { auth } from "../stores/auth";
import { goto } from "$app/navigation";
import { browser } from "$app/environment";

async function request(method, path, data = null) {
    const token = browser ? localStorage.getItem("token") : null;
    const headers = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers,
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const res = await fetch(`${API_URL}${path}`, options);

        if (res.status === 401) {
            if (browser) {
                localStorage.removeItem("token");
                localStorage.removeItem("is_admin");
                auth.set({ isAuthenticated: false, isAdmin: false, user: null });
                goto("/login");
            }
            throw new Error("Session expired. Please login again.");
        }

        // Handle 204 No Content
        if (res.status === 204) {
            return null;
        }

        const responseData = await res.json();

        if (!res.ok) {
            throw new Error(responseData.detail || "API request failed");
        }

        return responseData;
    } catch (err) {
        throw err;
    }
}

export const api = {
    get: (path) => request("GET", path),
    post: (path, data) => request("POST", path, data),
    patch: (path, data) => request("PATCH", path, data),
    delete: (path) => request("DELETE", path),
};
