"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, clearToken } from "@/lib/api";
import { ThemeProvider } from "@/components/ThemeProvider";
import ThemeToggle from "@/components/ThemeToggle";
import { Toaster } from "sonner";
import "./globals.css";

const navIcons: Record<string, React.ReactNode> = {
  "/": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>,
  "/knowledge": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>,
  "/keywords": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>,
  "/onboarding": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>,
  "/departments": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4-4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>,
  "/logs": <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/knowledge", label: "Knowledge Base" },
  { href: "/keywords", label: "Keywords" },
  { href: "/onboarding", label: "Onboarding Tasks" },
  { href: "/departments", label: "Departments" },
  { href: "/logs", label: "Logs" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoginPage && !getToken()) {
      router.push("/login");
    }
  }, [isLoginPage, router]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

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
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
      </head>
      <body className="flex h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <ThemeProvider>
          {/* Mobile header */}
          <div className="lg:hidden fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-3 bg-purple-950 text-white">
            <span className="text-base font-bold tracking-wide">Uzum HR Admin</span>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-purple-800 transition-colors cursor-pointer"
              aria-label="Toggle menu"
            >
              {sidebarOpen ? (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
              )}
            </button>
          </div>

          {/* Sidebar overlay (mobile) */}
          {sidebarOpen && (
            <div
              className="lg:hidden fixed inset-0 bg-black/40 z-40 mt-12"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-60 bg-purple-950 text-gray-100 flex flex-col shrink-0
            transform transition-transform duration-200 ease-out
            ${sidebarOpen ? "translate-x-0 mt-12 lg:mt-0" : "-translate-x-full lg:translate-x-0"}`}
          >
            <div className="hidden lg:block px-6 py-5 border-b border-purple-800/60">
              <span className="text-lg font-bold tracking-wide text-white">Uzum HR Admin</span>
            </div>
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                    transition-colors duration-200 cursor-pointer ${
                    pathname === item.href
                      ? "bg-purple-800 text-white shadow-sm"
                      : "text-purple-200 hover:bg-purple-800/60 hover:text-white"
                  }`}
                >
                  {navIcons[item.href]}
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="px-4 py-4 border-t border-purple-800/60 space-y-2">
              <p className="text-xs text-purple-400 truncate">
                API: {process.env.NEXT_PUBLIC_API_URL || "localhost:8000"}
              </p>
              <div className="flex items-center justify-between">
                <button
                  onClick={handleLogout}
                  className="text-xs text-purple-300 hover:text-red-400 transition-colors duration-200 cursor-pointer px-1"
                >
                  Logout
                </button>
                <ThemeToggle />
              </div>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 pt-12 lg:pt-0">
            <div className="p-4 md:p-6 lg:p-8 max-w-7xl">{children}</div>
          </main>

          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
