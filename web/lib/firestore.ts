/**
 * Server-only Firestore REST helper.
 * Uses GCP metadata server on Cloud Run, GOOGLE_APPLICATION_CREDENTIALS locally.
 */

const PROJECT_ID = "grandoldbooks";
const BASE_URL = `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents`;

export interface CloudReaderPrefs {
  darkMode: boolean;
  fontSize: "small" | "medium" | "large";
}

export interface CloudUserProfile {
  email: string;
  name: string | null;
  imageUrl: string | null;
  createdAt: string;
}

export interface CloudUserData {
  progress: Record<
    string,
    {
      currentChapter: number;
      scrollPercent: number;
      lastReadAt: string;
      finished: boolean;
    }
  >;
  languages: Record<string, string>;
  readerPrefs?: CloudReaderPrefs;
  profile?: CloudUserProfile;
  updatedAt: string;
}

async function getAccessToken(): Promise<string> {
  // Cloud Run: use metadata server
  const metadataUrl =
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token";
  try {
    const res = await fetch(metadataUrl, {
      headers: { "Metadata-Flavor": "Google" },
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      const data = await res.json();
      return data.access_token;
    }
  } catch {
    // Not on Cloud Run, fall through to local auth
  }

  // Local dev: use gcloud CLI
  const { execSync } = await import("child_process");
  const token = execSync("gcloud auth print-access-token", {
    encoding: "utf-8",
  }).trim();
  return token;
}

function docToData(doc: Record<string, unknown>): CloudUserData | null {
  const fields = doc.fields as Record<string, unknown> | undefined;
  if (!fields) return null;

  const progress: CloudUserData["progress"] = {};
  const languages: CloudUserData["languages"] = {};

  const progressMap = fields.progress as
    | { mapValue?: { fields?: Record<string, unknown> } }
    | undefined;
  if (progressMap?.mapValue?.fields) {
    for (const [bookId, val] of Object.entries(progressMap.mapValue.fields)) {
      const m = (val as { mapValue?: { fields?: Record<string, unknown> } })
        ?.mapValue?.fields;
      if (m) {
        progress[bookId] = {
          currentChapter: Number(
            (m.currentChapter as { integerValue?: string })?.integerValue ?? 0
          ),
          scrollPercent: Number(
            (m.scrollPercent as { doubleValue?: number; integerValue?: string })
              ?.doubleValue ??
              (m.scrollPercent as { integerValue?: string })?.integerValue ??
              0
          ),
          lastReadAt:
            (m.lastReadAt as { stringValue?: string })?.stringValue ?? "",
          finished:
            (m.finished as { booleanValue?: boolean })?.booleanValue ?? false,
        };
      }
    }
  }

  const langMap = fields.languages as
    | { mapValue?: { fields?: Record<string, unknown> } }
    | undefined;
  if (langMap?.mapValue?.fields) {
    for (const [bookId, val] of Object.entries(langMap.mapValue.fields)) {
      languages[bookId] =
        (val as { stringValue?: string })?.stringValue ?? "";
    }
  }

  const updatedAt =
    (fields.updatedAt as { stringValue?: string })?.stringValue ?? "";

  let readerPrefs: CloudReaderPrefs | undefined;
  const prefsMap = fields.readerPrefs as
    | { mapValue?: { fields?: Record<string, unknown> } }
    | undefined;
  if (prefsMap?.mapValue?.fields) {
    const pf = prefsMap.mapValue.fields;
    readerPrefs = {
      darkMode:
        (pf.darkMode as { booleanValue?: boolean })?.booleanValue ?? true,
      fontSize:
        ((pf.fontSize as { stringValue?: string })?.stringValue as
          | "small"
          | "medium"
          | "large") ?? "medium",
    };
  }

  let profile: CloudUserProfile | undefined;
  const profileMap = fields.profile as
    | { mapValue?: { fields?: Record<string, unknown> } }
    | undefined;
  if (profileMap?.mapValue?.fields) {
    const pf = profileMap.mapValue.fields;
    profile = {
      email: (pf.email as { stringValue?: string })?.stringValue ?? "",
      name: (pf.name as { stringValue?: string })?.stringValue ?? null,
      imageUrl: (pf.imageUrl as { stringValue?: string })?.stringValue ?? null,
      createdAt: (pf.createdAt as { stringValue?: string })?.stringValue ?? "",
    };
  }

  return { progress, languages, readerPrefs, profile, updatedAt };
}

function dataToFields(data: CloudUserData): Record<string, unknown> {
  const progressFields: Record<string, unknown> = {};
  for (const [bookId, p] of Object.entries(data.progress)) {
    progressFields[bookId] = {
      mapValue: {
        fields: {
          currentChapter: { integerValue: String(p.currentChapter) },
          scrollPercent: { doubleValue: p.scrollPercent },
          lastReadAt: { stringValue: p.lastReadAt },
          finished: { booleanValue: p.finished },
        },
      },
    };
  }

  const langFields: Record<string, unknown> = {};
  for (const [bookId, lang] of Object.entries(data.languages)) {
    langFields[bookId] = { stringValue: lang };
  }

  const result: Record<string, unknown> = {
    progress: { mapValue: { fields: progressFields } },
    languages: { mapValue: { fields: langFields } },
    updatedAt: { stringValue: data.updatedAt },
  };

  if (data.readerPrefs) {
    result.readerPrefs = {
      mapValue: {
        fields: {
          darkMode: { booleanValue: data.readerPrefs.darkMode },
          fontSize: { stringValue: data.readerPrefs.fontSize },
        },
      },
    };
  }

  if (data.profile) {
    const profileFields: Record<string, unknown> = {
      email: { stringValue: data.profile.email },
      createdAt: { stringValue: data.profile.createdAt },
    };
    if (data.profile.name) {
      profileFields.name = { stringValue: data.profile.name };
    }
    if (data.profile.imageUrl) {
      profileFields.imageUrl = { stringValue: data.profile.imageUrl };
    }
    result.profile = { mapValue: { fields: profileFields } };
  }

  return result;
}

export async function getUserData(
  userId: string
): Promise<CloudUserData | null> {
  const token = await getAccessToken();
  const url = `${BASE_URL}/users/${userId}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Firestore GET failed (${res.status}): ${text}`);
  }
  const doc = await res.json();
  return docToData(doc);
}

export async function setUserData(
  userId: string,
  data: CloudUserData
): Promise<void> {
  const token = await getAccessToken();
  const url = `${BASE_URL}/users/${userId}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ fields: dataToFields(data) }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Firestore PATCH failed (${res.status}): ${text}`);
  }
}
