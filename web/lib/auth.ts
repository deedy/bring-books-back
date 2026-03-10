export function normalizeRedirectUrl(value: string | string[] | undefined) {
  if (typeof value !== "string") return "/";
  return value.startsWith("/") ? value : "/";
}

export function extractBookIdFromRedirect(redirectUrl: string) {
  const pathname = redirectUrl.split("?")[0];
  const segments = pathname.split("/").filter(Boolean);
  if (segments[0] !== "read" || !segments[1]) return null;
  return segments[1];
}
