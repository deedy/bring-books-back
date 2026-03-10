"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import type { ReactNode } from "react";
import SyncProvider from "./SyncProvider";

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      appearance={{ baseTheme: dark }}
    >
      <SyncProvider />
      {children}
    </ClerkProvider>
  );
}
