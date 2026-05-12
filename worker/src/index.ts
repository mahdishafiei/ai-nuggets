/**
 * Podcast analytics + serve Worker.
 *
 * Route: GET|HEAD /p/:podcast/u/:user_id/:episode_id.mp3
 *   - logs one row to D1 and one data point to Analytics Engine (both via
 *     ctx.waitUntil so they don't block the response)
 *   - serves the mp3 directly from R2 (with Range support). Missing objects
 *     return 404.
 *
 * Anything else -> 404 plain text.
 *
 * IP hashing: sha256(ip | IP_SALT | YYYYMM-bucket). The same listener gets the
 * same hash within a calendar month and a fresh hash across months. The
 * IP_SALT secret should still be rotated periodically as defense in depth.
 */

export interface Env {
  DB: D1Database;
  AE: AnalyticsEngineDataset;
  BUCKET: R2Bucket;
  IP_SALT: string;
  ALLOWED_PODCASTS: string;
}

const ROUTE = /^\/p\/([a-zA-Z0-9_-]+)\/u\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+)\.mp3$/;

const BOT_PATTERNS = [
  "bot", "crawler", "spider", "preview", "facebookexternalhit",
  "curl", "wget", "python-requests", "okhttp", "go-http-client",
  "headlesschrome", "scraper",
];

function isBot(ua: string | null): boolean {
  if (!ua) return true;
  const lower = ua.toLowerCase();
  return BOT_PATTERNS.some((p) => lower.includes(p));
}

async function hashIp(ip: string, salt: string, ts: number): Promise<string> {
  const d = new Date(ts * 1000);
  const monthBucket = `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
  const data = new TextEncoder().encode(`${ip}|${salt}|${monthBucket}`);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function parseRange(header: string | null): R2Range | undefined {
  if (!header) return undefined;
  const m = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!m || (!m[1] && !m[2])) return undefined;
  const start = m[1] ? parseInt(m[1], 10) : undefined;
  const end = m[2] ? parseInt(m[2], 10) : undefined;
  if (start !== undefined && end !== undefined) return { offset: start, length: end - start + 1 };
  if (start !== undefined) return { offset: start };
  return { suffix: end! };
}

async function serveFromR2(req: Request, bucket: R2Bucket, key: string): Promise<Response | null> {
  try {
    if (req.method === "HEAD") {
      const head = await bucket.head(key);
      if (!head) return null;
      const headers = new Headers();
      head.writeHttpMetadata(headers);
      headers.set("etag", head.httpEtag);
      headers.set("accept-ranges", "bytes");
      headers.set("cache-control", "public, max-age=86400");
      headers.set("content-length", String(head.size));
      if (!headers.has("content-type")) headers.set("content-type", "audio/mpeg");
      return new Response(null, { status: 200, headers });
    }

    const range = parseRange(req.headers.get("range"));
    const obj = await bucket.get(key, range ? { range } : undefined);
    if (!obj) return null;

    const headers = new Headers();
    obj.writeHttpMetadata(headers);
    headers.set("etag", obj.httpEtag);
    headers.set("accept-ranges", "bytes");
    headers.set("cache-control", "public, max-age=86400");
    if (!headers.has("content-type")) headers.set("content-type", "audio/mpeg");

    if (range) {
      // R2 honors the range when requested, but obj.range is not always
      // populated, so compute headers from the requested range and obj.size.
      let offset: number;
      let length: number;
      if ("suffix" in range) {
        offset = Math.max(0, obj.size - range.suffix);
        length = Math.min(range.suffix, obj.size);
      } else {
        offset = range.offset ?? 0;
        length = range.length ?? obj.size - offset;
      }
      length = Math.min(length, obj.size - offset);
      const end = offset + length - 1;
      headers.set("content-length", String(length));
      headers.set("content-range", `bytes ${offset}-${end}/${obj.size}`);
      return new Response(obj.body, { status: 206, headers });
    }

    headers.set("content-length", String(obj.size));
    return new Response(obj.body, { status: 200, headers });
  } catch (err) {
    console.error("R2 serve failed for", key, err);
    return null;
  }
}

async function resolveTarget(
  req: Request,
  env: Env,
  podcast: string,
  _userId: string,
  episodeId: string,
): Promise<Response> {
  const key = `podcasts/${podcast}/episodes/${episodeId}.mp3`;
  const r2Response = await serveFromR2(req, env.BUCKET, key);
  if (r2Response) return r2Response;
  return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain" } });
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const method = req.method;

    if (method !== "GET" && method !== "HEAD") {
      return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain" } });
    }

    const m = ROUTE.exec(url.pathname);
    if (!m) {
      return new Response("Not Found", { status: 404, headers: { "content-type": "text/plain" } });
    }

    const [, podcast, userId, episodeId] = m;
    const allowed = env.ALLOWED_PODCASTS.split(",").map((s) => s.trim()).filter(Boolean);
    if (!allowed.includes(podcast)) {
      return new Response("Unknown podcast", { status: 404, headers: { "content-type": "text/plain" } });
    }

    const ts = Math.floor(Date.now() / 1000);
    const ip = req.headers.get("cf-connecting-ip") ?? "0.0.0.0";
    const ua = req.headers.get("user-agent");
    const cf: any = (req as any).cf ?? {};
    const country = (cf.country as string | undefined) ?? null;
    const colo = (cf.colo as string | undefined) ?? null;
    const asn = (cf.asn as number | undefined) ?? null;
    const bot = isBot(ua);
    const ipHash = await hashIp(ip, env.IP_SALT, ts);

    ctx.waitUntil((async () => {
      try {
        await env.DB.prepare(
          `INSERT INTO requests
             (ts, podcast, user_id, episode_id, method, ip_hash, user_agent, country, colo, asn, is_bot)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        )
          .bind(ts, podcast, userId, episodeId, method, ipHash, ua, country, colo, asn, bot ? 1 : 0)
          .run();
      } catch (err) {
        console.error("D1 insert failed", err);
      }
      try {
        env.AE.writeDataPoint({
          blobs: [podcast, userId, episodeId, method, country ?? "", colo ?? "", ua ?? "", ipHash],
          doubles: [bot ? 1 : 0, asn ?? 0],
          indexes: [podcast],
        });
      } catch (err) {
        console.error("AE write failed", err);
      }
    })());

    return resolveTarget(req, env, podcast, userId, episodeId);
  },
};
