
import { createHash, randomBytes, scrypt as scryptCallback, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";

const scrypt = promisify(scryptCallback);
const PREFIX = "ilanmatik";

const json = (data, status = 200, extra = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extra
    }
  });

const text = (data, status = 200, extra = {}) =>
  new Response(data, {
    status,
    headers: { "cache-control": "no-store", ...extra }
  });

const readBody = async req => {
  try {
    return await req.json();
  } catch {
    return {};
  }
};

const cleanString = (value, max = 500) =>
  typeof value === "string" ? value.trim().slice(0, max) : "";

const usernameOf = value =>
  cleanString(value, 40).toLowerCase();

const safeUser = user => ({
  username: user.username,
  name: user.name || user.username
});

const cookieValue = (req, key) => {
  const cookies = req.headers.get("cookie") || "";
  const found = cookies.split(";").map(x => x.trim())
    .find(x => x.startsWith(`${key}=`));
  if (!found) return "";
  try {
    return decodeURIComponent(found.slice(key.length + 1));
  } catch {
    return "";
  }
};

const makeCookie = (value, maxAge = 2592000) =>
  `${PREFIX}_s=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;

const clearCookie =
  `${PREFIX}_s=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;

const hashPassword = async password => {
  const salt = randomBytes(16).toString("hex");
  const key = await scrypt(password, salt, 64);
  return `${salt}:${Buffer.from(key).toString("hex")}`;
};

const verifyPassword = async (password, stored) => {
  if (typeof stored !== "string" || !stored.includes(":")) return false;
  const [salt, oldHash] = stored.split(":");
  const key = Buffer.from(await scrypt(password, salt, 64));
  const old = Buffer.from(oldHash, "hex");
  return key.length === old.length && timingSafeEqual(key, old);
};

const randomId = () => randomBytes(12).toString("hex");

const validUsername = value =>
  /^[a-z0-9_.-]{3,40}$/.test(value);

const normalizeListing = (input, id, username) => {
  const source = input && typeof input === "object" ? input : {};
  const S = source.S && typeof source.S === "object" ? source.S : source;

  return {
    id,
    owner: username,
    name: cleanString(source.name || S.title, 100) || "İsimsiz ilan",
    cat: cleanString(source.cat ?? S.cat, 40),
    updated: Date.now(),
    th: cleanString(source.th || (Array.isArray(source.img) ? source.img[0] : ""), 300000),
    cur: cleanString(source.cur, 40),
    S: {
      biz: cleanString(S.biz, 100),
      type: cleanString(S.type, 50),
      title: cleanString(S.title || source.name, 100),
      desc: cleanString(S.desc, 3000),
      price: cleanString(S.price, 50),
      tel: cleanString(S.tel, 40),
      addr: cleanString(S.addr, 200),
      color: cleanString(S.color, 40),
      tone: cleanString(S.tone, 30),
      tpl: cleanString(S.tpl, 40),
      f: Array.isArray(S.f) ? S.f.slice(0, 20).map(v => cleanString(v, 200)) : []
    },
    img: Array.isArray(source.img) ? source.img.slice(0, 5)
      .map(v => cleanString(v, 300000))
      .filter(Boolean) : []
  };
};

export function createApi({ users, limits, ilanlar, env = process.env }) {
  const get = async (store, key) => {
    try {
      return await store.get(key, { type: "json" });
    } catch {
      return null;
    }
  };

  const put = (store, key, value) =>
    store.setJSON(key, value);

  const del = async (store, key) => {
    try {
      await store.delete(key);
    } catch {}
  };

  const getSession = async req => {
    const token = cookieValue(req, `${PREFIX}_s`);
    if (!token) return null;
    const session = await get(users, `session:${token}`);
    if (!session?.username) return null;
    const user = await get(users, `user:${session.username}`);
    return user ? { token, user } : null;
  };

  const requireUser = async req => {
    const session = await getSession(req);
    return session?.user || null;
  };

  const checkOrigin = req => {
    const origin = req.headers.get("origin");
    if (!origin) return true;
    try {
      return new URL(origin).host === new URL(req.url).host;
    } catch {
      return false;
    }
  };

  const publicIndex = async () => {
    const index = await get(ilanlar, "_public_index");
    return Array.isArray(index) ? index : [];
  };

  const updatePublicIndex = async (listing, remove = false) => {
    const index = await publicIndex();
    const next = index.filter(item => item.id !== listing.id);
    if (!remove) {
      next.unshift({
        id: listing.id,
        owner: listing.owner,
        name: listing.name,
        cat: listing.cat,
        updated: listing.updated,
        th: listing.th,
        cur: listing.cur,
        S: listing.S,
        img: listing.img
      });
    }
    await put(ilanlar, "_public_index", next.slice(0, 5000));
  };

  const route = async (req, context) => {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const method = req.method.toUpperCase();

    if (path.startsWith("/api/") && !checkOrigin(req)) {
      return json({ error: "İstek kaynağı kabul edilmedi." }, 403);
    }

    if (path.startsWith("/api/") &&
        !["GET", "HEAD", "OPTIONS"].includes(method) &&
        req.headers.get("x-requested-with") !== "ilanmatik") {
      return json({ error: "Geçersiz istek." }, 403);
    }

    if (method === "OPTIONS") return text("", 204);

    if (path === "/api/register" && method === "POST") {
      const body = await readBody(req);
      const username = usernameOf(body.username);
      const password = cleanString(body.password, 200);
      const name = cleanString(body.name || body.username, 60);

      if (!validUsername(username)) {
        return json({ error: "Kullanıcı adı 3-40 karakter olmalı; İngilizce harf, sayı, nokta, tire ve alt çizgi kullan." }, 400);
      }
      if (password.length < 6) {
        return json({ error: "Şifre en az 6 karakter olmalı." }, 400);
      }
      if (await get(users, `user:${username}`)) {
        return json({ error: "Bu kullanıcı adı zaten kullanılıyor." }, 409);
      }

      const user = {
        username,
        name: name || username,
        password: await hashPassword(password),
        created: Date.now()
      };
      await put(users, `user:${username}`, user);

      const token = randomBytes(32).toString("hex");
      await put(users, `session:${token}`, { username, created: Date.now() });

      return json({ ok: true, user: safeUser(user) }, 201, {
        "set-cookie": makeCookie(token)
      });
    }

    if (path === "/api/login" && method === "POST") {
      const body = await readBody(req);
      const username = usernameOf(body.username);
      const password = cleanString(body.password, 200);
      const user = await get(users, `user:${username}`);

      if (!user || !(await verifyPassword(password, user.password))) {
        return json({ error: "Kullanıcı adı veya şifre yanlış." }, 401);
      }

      const token = randomBytes(32).toString("hex");
      await put(users, `session:${token}`, { username, created: Date.now() });
      return json({ ok: true, user: safeUser(user) }, 200, {
        "set-cookie": makeCookie(token)
      });
    }

    if (path === "/api/logout" && method === "POST") {
      const token = cookieValue(req, `${PREFIX}_s`);
      if (token) await del(users, `session:${token}`);
      return json({ ok: true }, 200, { "set-cookie": clearCookie });
    }

    if (path === "/api/me" && method === "GET") {
      const user = await requireUser(req);
      return user ? json({ user: safeUser(user) }) : json({ user: null }, 401);
    }

    if (path === "/api/password" && method === "POST") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      const body = await readBody(req);
      const oldPassword = cleanString(body.oldPassword, 200);
      const newPassword = cleanString(body.newPassword, 200);

      if (!(await verifyPassword(oldPassword, user.password))) {
        return json({ error: "Mevcut şifre yanlış." }, 400);
      }
      if (newPassword.length < 6) {
        return json({ error: "Yeni şifre en az 6 karakter olmalı." }, 400);
      }

      user.password = await hashPassword(newPassword);
      await put(users, `user:${user.username}`, user);
      return json({ ok: true });
    }

    if (path === "/api/recover" && method === "POST") {
      return json({ error: "Hesap kurtarma bu sürümde yapılandırılmamış. Güvenli kurtarma yöntemi eklenmeli." }, 501);
    }

    if (path === "/api/account" && method === "DELETE") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      const body = await readBody(req);
      if (!(await verifyPassword(cleanString(body.password, 200), user.password))) {
        return json({ error: "Şifre yanlış." }, 400);
      }

      const mine = await get(ilanlar, `${user.username}/index`) || [];
      for (const item of mine) {
        await del(ilanlar, `${user.username}/i_${item.id}`);
        await updatePublicIndex({ id: item.id }, true);
      }
      await del(ilanlar, `${user.username}/index`);
      await del(users, `user:${user.username}`);

      const token = cookieValue(req, `${PREFIX}_s`);
      if (token) await del(users, `session:${token}`);
      return json({ ok: true }, 200, { "set-cookie": clearCookie });
    }

    if (path === "/api/pazar" && method === "GET") {
      const query = cleanString(url.searchParams.get("q"), 100).toLocaleLowerCase("tr-TR");
      const cat = cleanString(url.searchParams.get("cat"), 40);
      const index = await publicIndex();

      const items = index.filter(item => {
        const title = `${item.name || ""} ${item.S?.title || ""} ${item.S?.desc || ""} ${item.S?.addr || ""}`.toLocaleLowerCase("tr-TR");
        return (!query || title.includes(query)) && (!cat || cat === "all" || item.cat === cat);
      });

      return json({ items });
    }

    if (path === "/api/ilanlar" && method === "GET") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      return json({ items: await get(ilanlar, `${user.username}/index`) || [] });
    }

    if (path === "/api/ilanlar" && method === "POST") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      const body = await readBody(req);
      const id = cleanString(body.id, 100) || randomId();
      const listing = normalizeListing(body, id, user.username);
      const key = `${user.username}/i_${id}`;
      const existing = await get(ilanlar, key);

      if (existing && existing.owner && existing.owner !== user.username) {
        return json({ error: "Bu ilanı değiştirme yetkin yok." }, 403);
      }

      await put(ilanlar, key, listing);

      const mine = await get(ilanlar, `${user.username}/index`) || [];
      const nextMine = mine.filter(item => item.id !== id);
      nextMine.unshift({
        id,
        name: listing.name,
        cat: listing.cat,
        updated: listing.updated,
        th: listing.th
      });
      await put(ilanlar, `${user.username}/index`, nextMine.slice(0, 500));

      await updatePublicIndex(listing);
      return json({ ok: true, item: listing }, 201);
    }

    const match = path.match(/^\/api\/ilanlar\/([^/]+)$/);
    if (match && method === "GET") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      const id = decodeURIComponent(match[1]);
      const item = await get(ilanlar, `${user.username}/i_${id}`);
      return item ? json({ item }) : json({ error: "İlan bulunamadı." }, 404);
    }

    if (match && method === "DELETE") {
      const user = await requireUser(req);
      if (!user) return json({ error: "Önce giriş yap." }, 401);
      const id = decodeURIComponent(match[1]);
      const key = `${user.username}/i_${id}`;
      const item = await get(ilanlar, key);
      if (!item) return json({ error: "İlan bulunamadı." }, 404);

      await del(ilanlar, key);
      const mine = await get(ilanlar, `${user.username}/index`) || [];
      await put(ilanlar, `${user.username}/index`, mine.filter(x => x.id !== id));
      await updatePublicIndex(item, true);
      return json({ ok: true });
    }

    return json({ error: "Bulunamadı." }, 404);
  };

  return async (req, context) => {
    try {
      return await route(req, context);
    } catch (error) {
      console.error("API error:", error);
      return json({ error: "Sunucu hatası oluştu." }, 500);
    }
  };
}
