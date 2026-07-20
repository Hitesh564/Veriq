import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from "./components/ClientLayout";
import { AuthProvider } from "./context/AuthContext";
import AuthModal from "./components/AuthModal";

export const metadata: Metadata = {
  title: "Veriq | AI Interview Design",
  description: "A premium AI interview experience with live practice, transcript intelligence, and structured feedback.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght@400;500;700&display=swap"
        />
      </head>
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
