import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Chito — AUT Assistant",
  description: "Ajou University in Tashkent AI Chatbot Kiosk",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className={`${geistSans.variable} h-full antialiased`}>
      <body className="h-screen w-screen overflow-hidden flex flex-col">
        {children}
      </body>
    </html>
  );
}
