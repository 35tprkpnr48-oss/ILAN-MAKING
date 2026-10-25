
import {
  randomBytes,
  scrypt as sc,
  timingSafeEqual,
  createHmac,
  createHash
} from "node:crypto";
import { promisify } from "node:util";

const scrypt = promisify(sc);
const OPT = {
  N: 16384,
  r: 8,
  p: 1,
  maxmem: 64 * 1024 * 1024
};

const HDR = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff"
};

const UN = /^[a-z0-9][a-z0-9_.-]{2,19}$/;
const ID = /^[a-f0-9]{12}$/;
const JPG = /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/;

const WEAK = new Set([
  "12345678", "123456789", "1234567890", "password",
  "password1", "qwertyui", "11111111", "iloveyou",
  "12341234", "sifre123", "parola123"
]);

const MAX_ILAN = 50;
const SESSION_MS = 30 * 864e5;
const FIFTEEN = 15 * 60e3;

const rd = (s, k) => s.get(k, { type: "json" });
const wr = (s, k, v) => s.setJSON(k, v);
const STR = (v, n) => typeof v === "string" ? v.slice(0, n) : "";

export function createApi({ users, limits, ilanlar, env = process.env }) {
  let SEC = null;

  async function secret() {
    if (SEC) return SEC;

    let s = env.AUTH_SECRET;

    if (!s) {
      let m = await rd(users, "_secret");

      if (!m) {
        m = { s: randomBytes(32).toString("hex") };
        await wr(users, "_secret", m);
      }

      s = m.s;
    }

    return SEC = s;
  }

  const hp = async (pw, salt) => {
    salt = salt || randomBytes(16);
    const h = await scrypt(pw.normalize("NFKC"), salt, 64, OPT);

    return {
      salt: salt.toString("hex"),
      hash: h.toString("hex")
    };
  };

  const vp = async (pw, r) => {
    const h = await scrypt(
      pw.normalize("NFKC"),
      Buffer.from(r.salt, "hex"),
      64,
      OPT
    );

    const b = Buffer.from(r.hash, "hex");

    return h.length === b.length && timingSafeEqual(h, b);
  };

  const b64 = b => Buffer.from(b).toString("base64url");

  async function sign(p) {
    const d = b64(JSON.stringify(p));
    const sig = createHmac("sha256", await secret())
      .update(d)
      .digest("base64url");

    return d + "." + sig;
  }

  async function unsign(t) {
    if (!t || t.length > 400) return null;

    const [i, m] = t.split(".");
    if (!i || !m) return null;

    const e = createHmac("sha256", await secret())
      .update(i)
      .digest("base64url");

    const a = Buffer.from(m);
    const b = Buffer.from(e);

    if (a.length !== b.length || !timingSafeEqual(a, b)) {
      return null;
    }

    try {
      const p = JSON.parse(
        Buffer.from(i, "base64url").toString()
      );

      return p.exp > Date.now() ? p : null;
    } catch {
      return null;
    }
  }

  const ck = (t, age) =>
    `im_s=${t}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${age}`;

  const tokOf = req => {
    const m = (req.headers.get("cookie") || "")
      .match(/(?:^|;\s*)im_s=([^;]+)/);

    return m && m[1];
  };

  const R = (st, o, cookie) => {
    const h = new Headers(HDR);

    if (cookie) h.append("set-cookie", cookie);

    return new Response(JSON.stringify(o), {
      status: st,
      headers: h
    });
  };

  const ERR = (st, m) => R(st, { error: m });

  const session = async u =>
    ck(
      await sign({
        u: u.u,
        v: u.tv,
        exp: Date.now() + SESSION_MS
      }),
      SESSION_MS / 1000
    );

  async function who(req) {
    const p = await unsign(tokOf(req));
    if (!p) return null;

    const u = await rd(users, p.u);

    return u && u.tv === p.v ? u : null;
  }

  const blocked = async (k, max, win = FIFTEEN) => {
    const r = await rd(limits, k);

    return !!(r && Date.now() - r.t < win && r.n >= max);
  };

  const bump = async (k, win = FIFTEEN) => {
    const now = Date.now();
    let r = await rd(limits, k);

    if (!r || now - r.t >= win) {
      r = { n: 0, t: now };
    }

    r.n++;
    await wr(limits, k, r);
  };

  const pwErr = (p, u) =>
    typeof p !== "string" || p.length < 8
      ? "Şifre en az 8 karakter olmalı."
      : p.length > 128
        ? "Şifre en fazla 128 karakter olabilir."
        : (p.toLowerCase() === u || WEAK.has(p.toLowerCase()))
          ? "Bu şifre çok kolay tahmin edilir."
          : null;

  const AL = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

  const genCode = () => {
    const b = randomBytes(16);
    let s = "";

    for (let i = 0; i < 16; i++) {
      s += AL[b[i] & 31];
    }

    return s.match(/.{4}/g).join("-");
  };

  const normCode = c =>
    String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, "");

  function clean(b) {
    const s = b.S || {};

    const o = {
      name: STR(b.name, 60).trim() || "Adsız",
      cur: Math.min(5, Math.max(0, b.cur | 0)),
      S: {
        biz: STR(s.biz, 40),
        type: STR(s.type, 20),
        title: STR(s.title, 70),
        desc: STR(s.desc, 280),
        price: STR(s.price, 20),
        tel: STR(s.tel, 20),
        addr: STR(s.addr, 90),
        color: /^#[0-9a-f]{6}$/i.test(s.color) ? s.color : "",
        tone: ["auto", "light", "dark"].includes(s.tone)
          ? s.tone
          : "auto",
        tpl: ["cat", "modern", "editorial", "luxe"].includes(s.tpl)
          ? s.tpl
          : "cat",
        f: [0, 1, 2, 3, 4, 5].map(i =>
          STR(Array.isArray(s.f) ? s.f[i] : "", 28)
        )
      },
      img: {}
    };

    for (const k of ["main", "d0", "d1", "d2"]) {
      const v = b.img && b.img[k];

      if (
        typeof v === "string" &&
        v.length <= 1.4e6 &&
        JPG.test(v)
      ) {
        o.img[k] = v;
      }
    }

    o.th =
      typeof b.th === "string" &&
      b.th.length <= 30000 &&
      JPG.test(b.th)
        ? b.th
        : "";

    return o;
  }

  // Ortak ilan listesinde gösterilecek güvenli alanlar.
  function publicMeta(item) {
    return {
      id: item.id,
      name: item.name,
      title: item.title || "",
      price: item.price || "",
      cat: item.cat,
      updated: item.updated,
      th: item.th || ""
    };
  }

  return async function handle(req, ctx) {
    try {
      const url = new URL(req.url);
      const seg = url.pathname
        .replace(/^\/api\/?/, "")
        .split("/")
        .filter(Boolean);

      const m = req.method;

      const ip =
        "ip:" +
        createHash("sha256")
          .update(
            String(
              (ctx && ctx.ip) ||
              req.headers.get("x-nf-client-connection-ip") ||
              "?"
            )
          )
          .digest("hex")
          .slice(0, 16);

      if (m !== "GET") {
        const o = req.headers.get("origin");

        if (
          (o && new URL(o).host !== url.host) ||
          req.headers.get("x-requested-with") !== "ilanmatik"
        ) {
          return ERR(403, "Geçersiz istek.");
        }
      }

      let b = {};

      if (m === "POST" || m === "DELETE") {
        const raw = await req.text();

        if (
          raw.length >
          (seg[0] === "ilanlar" ? 5.8e6 : 8192)
        ) {
          return ERR(413, "İstek çok büyük.");
        }

        try {
          b = raw ? JSON.parse(raw) : {};
        } catch {
          return ERR(400, "Geçersiz veri.");
        }

        if (!b || typeof b !== "object") b = {};
      }

      const uname = () =>
        String(b.username || "").toLowerCase().trim();

      const route = seg[0];

      // HERKESE AÇIK ORTAK İLAN LİSTESİ
      // Giriş yapmadan GET /api/pazar çağrılabilir.
      if (route === "pazar" && m === "GET") {
        const all = (await rd(ilanlar, "_public_index")) || [];

        if (!seg[1]) {
          return R(200, {
            items: all
              .slice()
              .sort((a, b) => b.updated - a.updated)
              .map(publicMeta)
          });
        }

        if (ID.test(seg[1])) {
          const item = all.find(x => x.id === seg[1]);

          if (!item) return ERR(404, "İlan bulunamadı.");

          const full = await rd(
            ilanlar,
            `${item.owner}/i_${item.id}`
          );

          if (!full) return ERR(404, "İlan bulunamadı.");

          return R(200, {
            id: full.id,
            name: full.name,
            cur: full.cur,
            S: full.S,
            img: full.img
          });
        }

        return ERR(404, "İlan bulunamadı.");
      }

      if (route === "me" && m === "GET") {
        const u = await who(req);

        return u
          ? R(200, { user: { username: u.u } })
          : ERR(401, "Giriş yapılmamış.");
      }

      if (route === "logout" && m === "POST") {
        return R(200, { ok: true }, ck("", 0));
      }

      if (route === "register" && m === "POST") {
        if (await blocked(ip + ":reg", 5, 3600e3)) {
          return ERR(
            429,
            "Çok fazla kayıt denemesi. Bir süre sonra tekrar deneyin."
          );
        }

        const u = uname();

        if (!UN.test(u)) {
          return ERR(
            400,
            "Kullanıcı adı 3–20 karakter olmalı (harf, rakam, _ . -)."
          );
        }

        const pe = pwErr(b.password, u);
        if (pe) return ERR(400, pe);

        if (await rd(users, u)) {
          return ERR(409, "Bu kullanıcı adı alınmış.");
        }

        await bump(ip + ":reg", 3600e3);

        const code = genCode();

        const rec = {
          u,
          pw: await hp(b.password),
          rc: await hp(normCode(code)),
          tv: 1,
          created: Date.now()
        };

        await wr(users, u, rec);

        return R(
          200,
          { user: { username: u }, code },
          await session(rec)
        );
      }

      if (route === "login" && m === "POST") {
        const u = uname();
        const uk = "u:" + u;

        if (
          !UN.test(u) ||
          typeof b.password !== "string" ||
          b.password.length > 128
        ) {
          return ERR(401, "Kullanıcı adı veya şifre hatalı.");
        }

        if (
          (await blocked(uk, 5)) ||
          (await blocked(ip, 25))
        ) {
          return ERR(
            429,
            "Çok fazla hatalı deneme. 15 dakika sonra tekrar deneyin."
          );
        }

        const rec = await rd(users, u);

        const ok = rec
          ? await vp(b.password, rec.pw)
          : (await hp(b.password), false);

        if (!ok) {
          if (rec) await bump(uk);
          await bump(ip);

          return ERR(401, "Kullanıcı adı veya şifre hatalı.");
        }

        await limits.delete(uk);

        return R(
          200,
          { user: { username: u } },
          await session(rec)
        );
      }

      if (route === "recover" && m === "POST") {
        const u = uname();
        const uk = "rc:" + u;

        if (!UN.test(u)) {
          return ERR(
            401,
            "Kullanıcı adı veya kurtarma kodu hatalı."
          );
        }

        if (
          (await blocked(uk, 5)) ||
          (await blocked(ip, 25))
        ) {
          return ERR(
            429,
            "Çok fazla hatalı deneme. 15 dakika sonra tekrar deneyin."
          );
        }

        const pe = pwErr(b.password, u);
        if (pe) return ERR(400, pe);

        const rec = await rd(users, u);

        const ok = rec
          ? await vp(normCode(b.code), rec.rc)
          : (await hp("x"), false);

        if (!ok) {
          if (rec) await bump(uk);
          await bump(ip);

          return ERR(
            401,
            "Kullanıcı adı veya kurtarma kodu hatalı."
          );
        }

        await limits.delete(uk);

        const code = genCode();

        rec.pw = await hp(b.password);
        rec.rc = await hp(normCode(code));
        rec.tv++;

        await wr(users, u, rec);

        return R(
          200,
          { user: { username: u }, code },
          await session(rec)
        );
      }

      const me = await who(req);

      if (!me) return ERR(401, "Önce giriş yapın.");

      if (route === "password" && m === "POST") {
        const uk = "u:" + me.u;

        if (await blocked(uk, 5)) {
          return ERR(
            429,
            "Çok fazla hatalı deneme. 15 dakika sonra tekrar deneyin."
          );
        }

        if (
          typeof b.old !== "string" ||
          !(await vp(b.old, me.pw))
        ) {
          await bump(uk);
          return ERR(401, "Şu anki şifre hatalı.");
        }

        const pe = pwErr(b.password, me.u);
        if (pe) return ERR(400, pe);

        const code = genCode();

        me.pw = await hp(b.password);
        me.rc = await hp(normCode(code));
        me.tv++;

        await wr(users, me.u, me);

        return R(
          200,
          { ok: true, code },
          await session(me)
        );
      }

      if (route === "account" && m === "DELETE") {
        const uk = "u:" + me.u;

        if (await blocked(uk, 5)) {
          return ERR(
            429,
            "Çok fazla hatalı deneme. 15 dakika sonra tekrar deneyin."
          );
        }

        if (
          typeof b.password !== "string" ||
          !(await vp(b.password, me.pw))
        ) {
          await bump(uk);
          return ERR(401, "Şifre hatalı.");
        }

        const idx =
          (await rd(ilanlar, me.u + "/_index")) || [];

        for (const i of idx) {
          await ilanlar.delete(`${me.u}/i_${i.id}`);
        }

        await ilanlar.delete(me.u + "/_index");
        await users.delete(me.u);

        // Kullanıcı hesabı silinince ortak listeden de temizle.
        const publicIndex =
          (await rd(ilanlar, "_public_index")) || [];

        await wr(
          ilanlar,
          "_public_index",
          publicIndex.filter(item => item.owner !== me.u)
        );

        return R(200, { ok: true }, ck("", 0));
      }

      if (route === "ilanlar") {
        const ik = me.u + "/_index";
        const idx = (await rd(ilanlar, ik)) || [];

        // Kullanıcının kendi ilan listesi
        if (m === "GET" && !seg[1]) {
          return R(200, { items: idx });
        }

        // Kullanıcının kendi ilan detayı
        if (m === "GET" && ID.test(seg[1] || "")) {
          const it = await rd(
            ilanlar,
            `${me.u}/i_${seg[1]}`
          );

          return it
            ? R(200, it)
            : ERR(404, "Kayıt bulunamadı.");
        }

        // İlan silme: kişisel listeden ve ortak listeden kaldır.
        if (m === "DELETE" && ID.test(seg[1] || "")) {
          const id = seg[1];

          await ilanlar.delete(`${me.u}/i_${id}`);

          await wr(
            ilanlar,
            ik,
            idx.filter(i => i.id !== id)
          );

          const publicIndex =
            (await rd(ilanlar, "_public_index")) || [];

          await wr(
            ilanlar,
            "_public_index",
            publicIndex.filter(
              item => !(item.id === id && item.owner === me.u)
            )
          );

          return R(200, { ok: true });
        }

        // Yeni ilan kaydetme veya mevcut ilanı güncelleme
        if (m === "POST" && !seg[1]) {
          const it = clean(b);

          let id =
            typeof b.id === "string" &&
            ID.test(b.id) &&
            idx.some(i => i.id === b.id)
              ? b.id
              : null;

          const upd = !!id;

          if (!id) {
            if (idx.length >= MAX_ILAN) {
              return ERR(
                400,
                `En fazla ${MAX_ILAN} ilan kaydedebilirsiniz. Eskilerden birini silin.`
              );
            }

            id = randomBytes(6).toString("hex");
          }

          const meta = {
            id,
            owner: me.u,
            name: it.name,
            title: it.S.title,
            price: it.S.price,
            cat: it.cur,
            updated: Date.now(),
            th: it.th
          };

          // Tam ilan bilgisi, yalnızca sahibinin alanında saklanır.
          await wr(
            ilanlar,
            `${me.u}/i_${id}`,
            {
              id,
              name: it.name,
              cur: it.cur,
              S: it.S,
              img: it.img
            }
          );

          // Kullanıcının kişisel ilan listesi
          await wr(
            ilanlar,
            ik,
            [meta, ...idx.filter(i => i.id !== id)]
          );

          // Herkesin görebildiği ortak ilan listesi
          const publicIndex =
            (await rd(ilanlar, "_public_index")) || [];

          await wr(
            ilanlar,
            "_public_index",
            [
              meta,
              ...publicIndex.filter(
                item => !(item.id === id && item.owner === me.u)
              )
            ]
          );

          return R(200, { id, updated: upd });
        }
      }

      return ERR(404, "Bulunamadı.");
    } catch (e) {
      console.error(e);
      return ERR(500, "Sunucu hatası. Biraz sonra tekrar deneyin.");
    }
  };
}
