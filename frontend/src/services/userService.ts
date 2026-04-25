import { API_BASE_URL, API_VERSION } from "@/config/config"
import { paths } from "@/types/openapi"

type User = paths["/api/v1/auth/users/me/"]["get"]["responses"]["200"]["content"]["application/json"]

export const userService = {
    // Get current user API call
    getCurrentUser: async (token: string | null): Promise<User> => {
        const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/auth/users/me`, {
            headers: {
                Authorization: `Bearer ${token}`
            },
        })
        if (!res.ok) {
            throw new Error (res.status === 401 ? "Token expired" : "Failed to fetch user")
            }
        return res.json()
    }

}