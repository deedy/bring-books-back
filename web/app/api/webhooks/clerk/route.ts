import { Webhook } from "svix";
import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { setUserData, getUserData } from "@/lib/firestore";

interface ClerkUserEvent {
  data: {
    id: string;
    email_addresses: Array<{ email_address: string }>;
    first_name: string | null;
    last_name: string | null;
    image_url: string | null;
    created_at: number;
  };
  type: string;
}

function logNewUserJoined({
  userId,
  email,
  name,
  createdAt,
  webhookId,
}: {
  userId: string;
  email: string;
  name: string | null;
  createdAt: string;
  webhookId: string;
}) {
  // Emit one-line structured JSON so Cloud Logging can match on
  // jsonPayload.event="new_user_joined".
  console.info(
    JSON.stringify({
      severity: "NOTICE",
      event: "new_user_joined",
      source: "clerk_webhook",
      message: "New user joined",
      clerkUserId: userId,
      email,
      name,
      createdAt,
      webhookId,
    }),
  );

  // Emit a plain-text marker too, so Logs Explorer can match on textPayload
  // if structured parsing doesn't occur in the deployed environment.
  console.info(
    `NEW_USER_JOINED clerkUserId=${userId} email=${email} createdAt=${createdAt} webhookId=${webhookId}${
      name ? ` name=${JSON.stringify(name)}` : ""
    }`,
  );
}

export async function POST(req: Request) {
  const secret = process.env.CLERK_WEBHOOK_SECRET;
  if (!secret) {
    console.error("CLERK_WEBHOOK_SECRET not set");
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  const headerPayload = await headers();
  const svixId = headerPayload.get("svix-id");
  const svixTimestamp = headerPayload.get("svix-timestamp");
  const svixSignature = headerPayload.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return NextResponse.json({ error: "Missing svix headers" }, { status: 400 });
  }

  const body = await req.text();

  let event: ClerkUserEvent;
  try {
    const wh = new Webhook(secret);
    event = wh.verify(body, {
      "svix-id": svixId,
      "svix-timestamp": svixTimestamp,
      "svix-signature": svixSignature,
    }) as ClerkUserEvent;
  } catch (err) {
    console.error("Webhook verification failed:", err);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (event.type === "user.created" || event.type === "user.updated") {
    const { id, email_addresses, first_name, last_name, image_url, created_at } = event.data;
    const email = email_addresses[0]?.email_address ?? "";
    const name = [first_name, last_name].filter(Boolean).join(" ") || null;
    const createdAt = new Date(created_at).toISOString();

    // Merge with existing doc (preserve reading progress)
    const existing = await getUserData(id);

    await setUserData(id, {
      progress: existing?.progress ?? {},
      languages: existing?.languages ?? {},
      readerPrefs: existing?.readerPrefs,
      updatedAt: existing?.updatedAt ?? new Date().toISOString(),
      profile: {
        email,
        name,
        imageUrl: image_url,
        createdAt,
      },
    });

    if (event.type === "user.created") {
      logNewUserJoined({
        userId: id,
        email,
        name,
        createdAt,
        webhookId: svixId,
      });
    }
  }

  return NextResponse.json({ ok: true });
}
