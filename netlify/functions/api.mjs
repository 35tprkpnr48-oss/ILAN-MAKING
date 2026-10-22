import {getStore} from "@netlify/blobs";
import {createApi} from "../lib/core.mjs";

const store = name => getStore({name, consistency: "strong"});
let handler;

export default async (req, context) => {
  handler = handler || createApi({users: store("users"), limits: store("limits"), ilanlar: store("ilanlar")});
  return handler(req, context);
};

export const config = {path: "/api/*"};
