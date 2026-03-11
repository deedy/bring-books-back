import Providers from "@/components/Providers";

export default function ReadLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Providers>{children}</Providers>;
}
