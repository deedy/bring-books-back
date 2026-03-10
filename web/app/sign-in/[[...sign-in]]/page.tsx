import type { Metadata } from "next";
import { SignIn } from "@clerk/nextjs";
import AuthShell from "@/components/auth/AuthShell";
import { authAppearance } from "@/components/auth/clerkAppearance";
import { normalizeRedirectUrl } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Sign In",
  description:
    "Sign in to Grand Old Books, verify your email link, and continue from the exact chapter where you stopped.",
  alternates: { canonical: "/sign-in" },
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedSearchParams = await searchParams;
  const redirectUrl = normalizeRedirectUrl(resolvedSearchParams.redirect_url);
  const signUpUrl = redirectUrl === "/"
    ? "/sign-up"
    : `/sign-up?redirect_url=${encodeURIComponent(redirectUrl)}`;

  return (
    <AuthShell mode="sign-in" redirectUrl={redirectUrl}>
      <SignIn
        path="/sign-in"
        routing="path"
        signUpUrl={signUpUrl}
        fallbackRedirectUrl={redirectUrl}
        forceRedirectUrl={redirectUrl}
        appearance={authAppearance}
      />
    </AuthShell>
  );
}
