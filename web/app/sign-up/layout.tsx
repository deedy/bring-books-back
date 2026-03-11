import Providers from "@/components/Providers";

export default function SignUpLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Providers>{children}</Providers>;
}
