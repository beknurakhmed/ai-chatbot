import type { Metadata, Viewport } from "next";
import { Poppins, Open_Sans } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
});

const openSans = Open_Sans({
  variable: "--font-open-sans",
  subsets: ["latin", "cyrillic"],
  weight: ["300", "400", "500", "600", "700"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export const metadata: Metadata = {
  title: "Uzumchi — Uzum Onboarding",
  description: "Onboarding and well-being platform for Uzum IT employees",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${poppins.variable} ${openSans.variable} h-full antialiased`}>
      <body className="h-screen w-screen overflow-hidden flex flex-col bg-gradient-to-b from-violet-50 via-white to-purple-50 font-[var(--font-open-sans)]">
        {children}
      </body>
    </html>
  );
}
