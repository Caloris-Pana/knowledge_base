#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DEEPSEEK_BASE = "https://chat.deepseek.com/api/v0";
const TOKEN_PATH = join(__dirname, "token.txt");

const TOKEN_MISSING_MSG = "❌ 未检测到 Token。首次使用请运行 setup-token.ps1 完成配置";
const TOKEN_EXPIRED_MSG = "❌ Token 已过期，请重新运行 setup-token.ps1 更新 Token";

function loadToken() {
  if (!existsSync(TOKEN_PATH)) return null;
  return readFileSync(TOKEN_PATH, "utf-8").trim();
}

function getHeaders() {
  const token = loadToken();
  if (!token) return null;
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    "X-Client-Version": "1.0.0-always",
    "X-Client-Platform": "web",
    "X-Client-Locale": "en_US",
    Origin: "https://chat.deepseek.com",
    Referer: "https://chat.deepseek.com/",
  };
}

class TokenMissingError extends Error {
  constructor() {
    super(TOKEN_MISSING_MSG);
    this.name = "TokenMissingError";
  }
}

class TokenExpiredError extends Error {
  constructor() {
    super(TOKEN_EXPIRED_MSG);
    this.name = "TokenExpiredError";
  }
}

async function apiFetch(url) {
  const headers = getHeaders();
  if (!headers) {
    return { error: "missing" };
  }
  const res = await fetch(url, { headers });
  if (res.status === 401) {
    return { error: "expired" };
  }
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  const body = await res.json();
  if (body.code && body.code !== 0) {
    console.error(`[apiFetch] API error: code=${body.code} msg=${body.msg}`);
    throw new Error(`API error: ${body.msg || `code=${body.code}`}`);
  }
  if (body.data?.biz_code && body.data.biz_code !== 0) {
    console.error(`[apiFetch] biz error: code=${body.data.biz_code} msg=${body.data.biz_msg}`);
    throw new Error(`API biz error: ${body.data.biz_msg || `code=${body.data.biz_code}`}`);
  }
  return { ok: true, data: body.data };
}

const MAX_PAGES = 50;

async function fetchSessions() {
  const allSessions = [];
  let cursor = null;
  let pages = 0;
  while (true) {
    pages++;
    if (pages > MAX_PAGES) {
      console.error(`[fetchSessions] Exceeded max ${MAX_PAGES} pages, got ${allSessions.length} sessions`);
      break;
    }
    const url = cursor
      ? `${DEEPSEEK_BASE}/chat_session/fetch_page?before_seq_id=${cursor}`
      : `${DEEPSEEK_BASE}/chat_session/fetch_page`;
    const result = await apiFetch(url);
    if (result.error === "missing") {
      throw new TokenMissingError();
    }
    if (result.error === "expired") {
      throw new TokenExpiredError();
    }
    const bizData = result.data?.biz_data;
    if (!bizData) {
      console.error(`[fetchSessions] Page ${pages}: missing biz_data in response`);
      throw new Error("API returned empty data");
    }
    const sessions = bizData.chat_sessions || [];
    if (sessions.length === 0) {
      console.error(`[fetchSessions] Page ${pages}: empty sessions list, has_more=${bizData.has_more}`);
      if (!bizData.has_more) break;
      throw new Error("API returned empty session list but indicates more pages");
    }
    allSessions.push(...sessions);
    if (!bizData.has_more) break;
    cursor = sessions[sessions.length - 1]?.seq_id;
    if (!cursor) {
      console.error(`[fetchSessions] Page ${pages}: has_more=true but no cursor`);
      break;
    }
  }
  return allSessions;
}

async function fetchMessages(sessionId) {
  const url = `${DEEPSEEK_BASE}/chat/history_messages?chat_session_id=${sessionId}`;
  const result = await apiFetch(url);
  if (result.error === "missing") {
    throw new TokenMissingError();
  }
  if (result.error === "expired") {
    throw new TokenExpiredError();
  }
  const bizData = result.data?.biz_data;
  if (!bizData) {
    console.error(`[fetchMessages] missing biz_data for session ${sessionId}`);
    throw new Error("API returned empty data");
  }
  return bizData.chat_messages || [];
}

function formatSession(s) {
  const ts = (s.updated_at || s.created_at) * 1000;
  const date = new Date(ts);
  return `[${s.id}] ${s.title || "(无标题)"}  —  ${date.toLocaleString()}`;
}

function formatSessionsGrouped(sessions) {
  const groups = {};
  let counter = 0;

  for (const s of sessions) {
    const ts = (s.updated_at || s.created_at) * 1000;
    const d = new Date(ts);
    const y = d.getFullYear();
    const m = d.getMonth() + 1;
    const day = d.getDate();
    const key = `${y}-${String(m).padStart(2, '0')}`;

    if (!groups[key]) {
      groups[key] = { year: y, month: m, days: {} };
    }
    if (!groups[key].days[day]) {
      groups[key].days[day] = [];
    }
    counter++;
    groups[key].days[day].push({ num: counter, id: s.id, title: s.title || "(无标题)" });
  }

  const sortedKeys = Object.keys(groups).sort();
  const output = [];

  for (const key of sortedKeys) {
    const g = groups[key];
    const total = Object.values(g.days).reduce((sum, arr) => sum + arr.length, 0);
    output.push(`${g.year}年${g.month}月：共${total}条对话`);
    output.push("");
    output.push("| 序号 | 日期 | 对话内容概要 |");
    output.push("|------|------|------|");

    const sortedDays = Object.keys(g.days).sort((a, b) => a - b);
    for (const day of sortedDays) {
      const items = g.days[day];
      for (const item of items) {
        const dateLabel = `${g.month}月${day}日`;
        output.push(`| ${item.num} | ${dateLabel} | ${item.title} |`);
      }
    }
    output.push("");
  }

  return output.join("\n").trimEnd();
}

function formatOverview(sessions) {
  const groups = {};

  for (const s of sessions) {
    const ts = (s.updated_at || s.created_at) * 1000;
    const d = new Date(ts);
    const y = d.getFullYear();
    const m = d.getMonth() + 1;
    const key = `${y}-${String(m).padStart(2, "0")}`;

    if (!groups[key]) {
      groups[key] = { year: y, month: m, count: 0 };
    }
    groups[key].count++;
  }

  const sortedKeys = Object.keys(groups).sort();
  const total = sessions.length;
  const lines = [`共计 ${total} 条对话`, ""];

  for (const key of sortedKeys) {
    const g = groups[key];
    lines.push(`${g.year}年${g.month}月：${g.count}条对话`);
  }

  return lines.join("\n");
}

function formatMessages(messages) {
  const lines = [];
  for (const m of messages) {
    const role = m.role === "user" ? "🧑 User" : "🤖 Assistant";
    lines.push("─".repeat(60));
    lines.push(`${role}:`);
    lines.push("");
    lines.push(m.content || "(空)");
    lines.push("");
  }
  return lines.join("\n");
}

function getSessionsByMonth(sessions, month) {
  return sessions.filter((s) => {
    const ts = (s.updated_at || s.created_at) * 1000;
    const d = new Date(ts);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    return key === month;
  }).sort((a, b) => {
    const ta = (a.updated_at || a.created_at) * 1000;
    const tb = (b.updated_at || b.created_at) * 1000;
    return ta - tb;
  });
}

const server = new Server(
  {
    name: "deepseek-chat-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "ds_list_sessions",
        description:
          "查看 DeepSeek 对话总览（按年月分组统计），或使用 month 参数查看某月详情",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description:
                "可选，在 month 详情模式下按标题模糊搜索（大小写不敏感）；总览模式忽略此参数",
            },
            limit: {
              type: "number",
              description: "可选，详情模式下最多返回的对话数，默认 100",
            },
            month: {
              type: "string",
              description:
                "可选，格式 YYYY-MM（如 2026-05），查看该月的详细对话列表",
            },
          },
        },
      },
      {
        name: "ds_get_session",
        description:
          "获取会话消息内容。可通过 session_id 直接获取，或通过 month + number（列表中的序号）获取",
        inputSchema: {
          type: "object",
          properties: {
            session_id: {
              type: "string",
              description: "会话 ID（与 month+number 二选一）",
            },
            month: {
              type: "string",
              description: "月份，格式 YYYY-MM（与 session_id 二选一）",
            },
            number: {
              type: "number",
              description: "月详情列表中的序号（与 session_id 二选一）",
            },
          },
        },
      },
      {
        name: "ds_get_session_by_title",
        description:
          "按标题模糊搜索会话，如果唯一匹配则直接返回完整内容，否则返回匹配列表供选择",
        inputSchema: {
          type: "object",
          properties: {
            title: {
              type: "string",
              description: "要搜索的标题关键词（模糊匹配）",
            },
          },
          required: ["title"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "ds_list_sessions") {
      const month = args?.month;
      const sessions = await fetchSessions();

      if (month) {
        const query = (args?.query || "").toLowerCase();
        const limit = args?.limit || 100;
        const filtered = getSessionsByMonth(sessions, month).filter((s) => {
          if (query && !(s.title && s.title.toLowerCase().includes(query))) return false;
          return true;
        });
        if (filtered.length === 0) {
          return {
            content: [{ type: "text", text: `${month} 没有匹配的对话` }],
          };
        }
        const top = filtered.slice(0, limit);
        const text = formatSessionsGrouped(top);
        return {
          content: [{ type: "text", text: text }],
        };
      }

      const text = formatOverview(sessions);
      return {
        content: [{ type: "text", text: text }],
      };
    }

    if (name === "ds_get_session") {
      const sessionId = args?.session_id;
      const month = args?.month;
      const num = args?.number;

      let targetId = sessionId;
      if (!targetId) {
        if (!month || !num) {
          throw new Error("请提供 session_id，或提供 month + number 组合");
        }
        const sessions = await fetchSessions();
        const monthSessions = getSessionsByMonth(sessions, month);
        if (monthSessions.length === 0) {
          throw new Error(`${month} 没有对话记录`);
        }
        if (num < 1 || num > monthSessions.length) {
          throw new Error(`序号 ${num} 超出范围，${month} 共有 ${monthSessions.length} 条对话`);
        }
        targetId = monthSessions[num - 1].id;
      }

      const messages = await fetchMessages(targetId);
      if (messages.length === 0) {
        return {
          content: [{ type: "text", text: "该会话中没有消息" }],
        };
      }
      return {
        content: [{ type: "text", text: formatMessages(messages) }],
      };
    }

    if (name === "ds_get_session_by_title") {
      const titleQuery = (args?.title || "").toLowerCase();
      if (!titleQuery) {
        throw new Error("title 参数必填");
      }
      const sessions = await fetchSessions();
      const matches = sessions.filter(
        (s) => s.title && s.title.toLowerCase().includes(titleQuery)
      );

      if (matches.length === 0) {
        return {
          content: [{ type: "text", text: `未找到标题包含 "${args.title}" 的会话` }],
        };
      }

      if (matches.length === 1) {
        const messages = await fetchMessages(matches[0].id);
        const header = `📌 会话: ${matches[0].title}\n${"═".repeat(60)}\n`;
        return {
          content: [
            {
              type: "text",
              text: header + formatMessages(messages),
            },
          ],
        };
      }

      const list = matches.map((s, i) => `${i + 1}. ${formatSession(s)}`).join("\n");
      return {
        content: [
          {
            type: "text",
            text: `找到 ${matches.length} 个匹配会话，请用 ds_get_session 指定 session_id 获取:\n\n${list}`,
          },
        ],
      };
    }

    throw new Error(`未知工具: ${name}`);
  } catch (err) {
    console.error(`[handler] Error in ${name}:`, err.message);
    return {
      content: [{ type: "text", text: `错误: ${err.message}` }],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("DeepSeek Chat MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
