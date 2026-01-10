import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout";
import { ToastProvider } from "@/hooks/useToast";
import { ToastContainer } from "@/components/ui";

export const metadata: Metadata = {
  title: "FastAPI Auth",
  description: "FastAPI User Authentication Demo",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased min-h-screen flex flex-col" suppressHydrationWarning>
        <ToastProvider>
          <Navbar />
          <main className="flex-1">
            {children}
          </main>
          <footer className="bg-gray-100 py-4 text-center text-gray-600 text-sm">
            FastAPI User Authentication Demo
          </footer>
          <ToastContainer />
        </ToastProvider>
      </body>
    </html>
  );
}
