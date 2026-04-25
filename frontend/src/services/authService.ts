import { API_BASE_URL, API_VERSION } from "@/config/config"

type FormData = {
  username: string
  password: string
};

type LoginResponse = {
  access_token: string
  token_type: string
}

export const authService = {
  // Login API call
  signIn: async (data: FormData): Promise<LoginResponse> => {
    const form = new URLSearchParams();
    form.append("username", data.username)
    form.append("password", data.password)

    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form.toString(),
    });
    
    if (!res.ok) throw new Error("Invalid credentials")
    return res.json();
  },
}