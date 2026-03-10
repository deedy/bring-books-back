import type { Metadata } from "next";
import { SignUp } from "@clerk/nextjs";
import AuthShell from "@/components/auth/AuthShell";
import { authAppearance } from "@/components/auth/clerkAppearance";
import { normalizeRedirectUrl } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Sign Up",
  description:
    "Create a Grand Old Books account, verify your email, and return to the exact chapter where you stopped reading.",
  alternates: { canonical: "/sign-up" },
};

export default async function SignUpPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedSearchParams = await searchParams;
  const redirectUrl = normalizeRedirectUrl(resolvedSearchParams.redirect_url);
  const signInUrl = redirectUrl === "/"
    ? "/sign-in"
    : `/sign-in?redirect_url=${encodeURIComponent(redirectUrl)}`;

  return (
    <AuthShell mode="sign-up" redirectUrl={redirectUrl}>
      <SignUp
        path="/sign-up"
        routing="path"
        signInUrl={signInUrl}
        fallbackRedirectUrl={redirectUrl}
        forceRedirectUrl={redirectUrl}
        appearance={authAppearance}
      />
    </AuthShell>
  );
}
