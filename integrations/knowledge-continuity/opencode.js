// Pinned OpenCode 2.3 Promise API. Passive identity only; no model/vault/receipt API.
import { open, realpath, access } from "node:fs/promises"
import { constants } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const validID = (x) => typeof x === "string" && /^[A-Za-z0-9_-]{1,160}$/.test(x)
const cue = "If a durable decision, correction or lesson emerges, follow the existing Knowledge guidance."

async function boundedJSON(file, bound = 65536) {
  const handle = await open(file, constants.O_RDONLY | constants.O_NONBLOCK | constants.O_NOFOLLOW)
  try {
    const info = await handle.stat()
    if (!info.isFile() || info.size > bound) throw new Error("invalid bounded file")
    const bytes = Buffer.alloc(bound + 1)
    const { bytesRead } = await handle.read(bytes, 0, bytes.length, 0)
    if (bytesRead > bound) throw new Error("input too large")
    return JSON.parse(bytes.subarray(0, bytesRead).toString("utf8"))
  } finally { await handle.close() }
}

export async function setup(ctx) {
  const configured = ctx.options?.settings ?? fileURLToPath(new URL("./settings.json", import.meta.url))
  const cfg = await boundedJSON(configured)
  if (cfg.version !== 1 || cfg.enabled !== true || process.env.NSTACK_KNOWLEDGE_DISABLED === "1" || !/^v?2\.3\.0$/.test(ctx.app?.version ?? "")) return
  const directory = ctx.location?.directory
  if (typeof directory !== "string" || !path.isAbsolute(directory) || ctx.location.workspaceID) return
  if (await realpath(directory) !== directory) return
  await access(directory, constants.R_OK | constants.W_OK)
  const events = new Map() // At most 128 current-session IDs, in memory only.
  let active = true, serial = Promise.resolve()
  const registrations = []
  const guard = (handler) => (event) => {
    const next = serial.then(() => active ? handler(event) : undefined).catch(() => {})
    serial = next
    return next
  }
  registrations.push(await ctx.session.hook("prompt", guard(async (event) => {
    if (!validID(event.sessionID) || !validID(event.messageID)) return
    const response = await ctx.session.get({ sessionID: event.sessionID })
    const session = response?.data
    if (!session || session.id !== event.sessionID || session.parentID) return
    // Only IDs and parent metadata are observed; event.prompt is never accessed.
    events.delete(event.sessionID)
    events.set(event.sessionID, event.messageID)
    if (events.size > 128) events.delete(events.keys().next().value)
  })))
  registrations.push(await ctx.session.hook("context", guard((event) => {
    if (!validID(event.sessionID)) return
    const message = events.get(event.sessionID)
    if (!message) return
    // No messages/tools/models, receipt lookup, persistence or additional work.
    event.system.push({ type: "text", text: `Knowledge event: host=opencode session=${event.sessionID} event=${message}.\n${cue}` })
  })))
  return async () => {
    active = false
    events.clear()
    for (const registration of registrations) await registration.dispose()
  }
}
