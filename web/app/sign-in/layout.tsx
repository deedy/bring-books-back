import Providers from "@/components/Providers";

export default function SignInLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Providers>{children}</Providers>;
}
