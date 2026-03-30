"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { getToken, clearToken } from "@/lib/api";
import "./globals.css";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/knowledge", label: "Knowledge Base" },
  { href: "/keywords", label: "Keywords" },
  { href: "/news", label: "News" },
  { href: "/staff", label: "Staff" },
  { href: "/timetable", label: "Timetable" },
  { href: "/logs", label: "Logs" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (!isLoginPage && !getToken()) {
      router.push("/login");
    }
  }, [isLoginPage, router]);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (isLoginPage) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="flex h-screen bg-gray-100 text-gray-900">
        {/* Sidebar */}
        <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col shrink-0">
          <div className="px-6 py-5 border-b border-gray-700">
            <span className="text-lg font-bold tracking-wide text-white">Chatbot Admin</span>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.href
                    ? "bg-gray-700 text-white"
                    : "text-gray-300 hover:bg-gray-700 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="px-4 py-4 border-t border-gray-700 space-y-2">
            <p className="text-xs text-gray-500">API: localhost:8000</p>
            <button
              onClick={handleLogout}
              className="w-full text-xs text-gray-400 hover:text-red-400 transition text-left px-1"
            >
              Logout
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <div className="p-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
