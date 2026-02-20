import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Sidebar } from "@/app/components/sidebar/Sidebar";

export const metadata: Metadata = {
  title: "DBA AI Platform",
  description: "Enterprise SQL Server Monitoring & Chat Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#0a0a0a] text-zinc-50 flex h-screen overflow-hidden`}
      >
        <div className="w-64 flex-none hidden md:block border-r border-[#222]">
          <Sidebar />
        </div>
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
