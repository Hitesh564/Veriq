import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from "./components/ClientLayout";
import { AuthProvider } from "./context/AuthContext";
import AuthModal from "./components/AuthModal";

export const metadata: Metadata = {
  title: "IntervAI | AI Interview Design",
  description: "A premium AI interview experience with live practice, transcript intelligence, and structured feedback.",
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
