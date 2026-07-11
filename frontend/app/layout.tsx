import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from "./components/ClientLayout";
import { AuthProvider } from "./context/AuthContext";
import AuthModal from "./components/AuthModal";

export const metadata: Metadata = {
  title: "Veriq AI - Professional AI Mock Interview Platform",
  description: "Practice realistic technical mock interviews with an adaptive AI coach.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ClientLayout>
            {children}
          </ClientLayout>
          <AuthModal />
        </AuthProvider>
      </body>
    </html>
  );
}
