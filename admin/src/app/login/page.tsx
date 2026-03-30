"use client";
import { useState } from "react";
import { setToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [token, setTokenInput] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    // Verify token by calling a protected endpoint
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/admin/knowledge`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok || res.status === 200) {
        setToken(token);
        router.push("/");
      } else {
        setError("Invalid token. Please try again.");
      }
    } catch {
      setError("Cannot connect to server.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Admin Panel</h1>
        <p className="text-gray-500 text-sm mb-6">Enter your admin token to continue</p>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="password"
            placeholder="Admin token"
            value={token}
            onChange={(e) => setTokenInput(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
