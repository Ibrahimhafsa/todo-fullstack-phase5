/**
 * JWT Token Hook
 *
 * Provides access to the JWT token from localStorage.
 * Used for authenticating API requests to the backend.
 */

"use client";

import { useEffect, useState } from "react";

export function useJwtToken() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Get token from localStorage
    const storedToken = localStorage.getItem("auth_token");
    setToken(storedToken);

    // Listen for token changes (sign in/out events)
    const handleTokenChange = (event: CustomEvent<{ token: string }>) => {
      setToken(event.detail.token);
    };

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === "auth_token") {
        setToken(event.newValue);
      }
    };

    window.addEventListener(
      "auth_token_changed" as any,
      handleTokenChange as EventListener
    );
    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener(
        "auth_token_changed" as any,
        handleTokenChange as EventListener
      );
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  return token;
}
