/**
 * Chat Page
 *
 * Protected route for the AI chat interface.
 * Requires authentication via Better Auth.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { Navbar } from "@/components/ui/Navbar";
import { LoadingState } from "@/components/ui/LoadingState";
import { ChatContainer } from "@/components/chat/ChatContainer";

export default function ChatPage() {
  const { session, isLoading: authLoading, signOut } = useAuth();
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);

  console.log("[ChatPage] Current state:", {
    authLoading,
    sessionExists: !!session,
    userExists: !!session?.user,
    userId: session?.user?.id,
    userEmail: session?.user?.email,
    isRedirecting,
  });

  // Check authentication and handle redirects
  useEffect(() => {
    console.log("[ChatPage.useEffect] Auth check...", {
      authLoading,
      sessionExists: !!session,
      userExists: !!session?.user,
    });

    // Still loading auth - show loading state
    if (authLoading) {
      console.log("[ChatPage.useEffect] Still loading auth, showing loading state");
      return;
    }

    // Auth loading finished - check if user is authenticated
    if (!session || !session.user) {
      console.log("[ChatPage.useEffect] ❌ NOT AUTHENTICATED - redirecting to signin");
      setIsRedirecting(true);
      router.push("/signin");
      return;
    }

    // Authenticated - success
    console.log("[ChatPage.useEffect] ✅ AUTHENTICATED as:", session.user.email);
  }, [authLoading, session, router]);

  const handleSignOut = async () => {
    console.log("[ChatPage] Sign out clicked");
    signOut();
    router.push("/signin");
  };

  // Show loading while auth is being checked
  if (authLoading) {
    console.log("[ChatPage] Rendering: AUTH LOADING STATE");
    return (
      <main className="min-h-screen flex items-center justify-center">
        <LoadingState message="Loading..." />
      </main>
    );
  }

  // Show loading while redirecting
  if (isRedirecting) {
    console.log("[ChatPage] Rendering: REDIRECTING STATE");
    return (
      <main className="min-h-screen flex items-center justify-center">
        <LoadingState message="Redirecting..." />
      </main>
    );
  }

  // Fallback: Not authenticated (safety check)
  if (!session || !session.user) {
    console.log("[ChatPage] Rendering: NOT AUTHENTICATED (fallback)");
    return (
      <main className="min-h-screen flex items-center justify-center">
        <LoadingState message="Redirecting to sign in..." />
      </main>
    );
  }

  // AUTHENTICATED - Render chat page
  console.log("[ChatPage] Rendering: AUTHENTICATED CHAT PAGE");

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar
        title="TaskFlow"
        userEmail={session.user.email}
        onLogout={handleSignOut}
      />

      <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col">
        {/* Page header */}
        <div className="mb-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">
            AI Chat Assistant
          </h1>
          <p className="text-gray-400 text-sm">
            Ask me anything about your tasks or get help managing your work.
          </p>
        </div>

        {/* Chat container (fills remaining space) */}
        <div className="flex-1 min-h-0">
          <ChatContainer />
        </div>
      </main>
    </div>
  );
}
