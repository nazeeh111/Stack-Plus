# Sessions and the dedicated browser

Upstream routes to this reference for login, logout, account changes or `NEED_LOGIN` results.

The installed SKILL.md's anonymous-access and credential restrictions control this reference. Its session import, login, cookie access, browser backend and configuration routes remain unadmitted here. The following preserves the upstream capability description; it does not authorize those operations.

## Dedicated browser

- All browser channels share one dedicated profile, separate from the user's everyday Chrome. The program does not close or modify the everyday browser.
- CloakBrowser is preferred. A download/install failure falls back to an installed local Chrome and remembers the fallback instead of downloading on every call. Upstream offers `agent-reach browser setup --retry-cloak` once the network is repaired.
- `agent-reach add <channel>` automatically prepares Node, OpenCLI, the engine and extension using versions tested for this release. With the Chrome fallback on Windows, the user may need to click “Add to Chrome” once.
- Headless by default. Only `agent-reach login <channel>` shows a window. Queries use an already open login window without closing it; wait for the user to say login is finished. After the window closes, later queries return to headless mode.
- The browser closes after 10 idle minutes and reopens on the next call. Actual page operations and Reach calls reset the timer. Login progress is saved periodically; the user need not close the window.
- Parallel calls: at most 2 per platform and 4 overall; excess calls queue for at most 2 minutes, then return `BUSY`. Searches on one platform start at least 10 seconds apart. Opening login, logging out and browser reinstallation wait for active queries to finish.
- `agent-reach browser status` reads status; `browser setup` prepares the engine/extension; `browser stop` closes the program-managed browser.

## Automatic reuse of an existing login

1. On first use of a site, if the user's Chrome is connected to the OpenCLI extension, upstream copies that site's login cookies once to the dedicated browser. It does not copy the whole profile, other sites or a password store, or modify the source browser.
2. A successful copy is reused without timed recopying. Cookie presence is not proof of a valid login; inspect actual action results.
3. If Chrome is not connected to the extension, do not promise automatic reuse or infer that the user is logged out. Upstream then uses the saved Reach session.
4. If several local browsers have the site logged in, upstream lists sources with `agent-reach browser profiles` and selects one with `agent-reach browser use <ID>`; it does not switch randomly.
5. `agent-reach login <channel> --import-existing` explicitly recopies only that site's login without opening a window. If no login can be copied or OpenCLI Bridge is not running, it returns `NEED_SETUP` and preserves the saved session.
6. After the user logs in personally in the dedicated window, or runs `logout`/`remove`, automatic copying stops so a logged-out session cannot reappear.

## When personal login is actually required

- Request login only after an actual `NEED_LOGIN` response and only when the remaining task needs that route. A login button beside public body text is not a login requirement.
- Upstream `agent-reach login <channel>` opens the site's login page in the dedicated browser for the user to complete personally. Never log in for them, request a password or print cookies.
- Follow a result's `next` steps where admitted. Some native-tool channels, such as Xueqiu, require `agent-reach login <channel> --sync` after login.
- After the user finishes, repeat the original action to verify its actual effect.

## Platform differences

- BOSS Zhipin's site search uses OpenCLI and the shared dedicated browser. Do not repeatedly ask for login when an upstream job-detail error misreports it as required.
- Bilibili passes an existing login to its official CLI only when reading subtitles; ordinary search does not prepare a browser.
- Xueqiu community actions need login. Sessions expire after several hours; upstream repeats the login flow after expiry.

## Logout and removal

- `agent-reach logout <channel>` clears that site's dedicated-browser login and the channel's own state, preserving other sites.
- `agent-reach remove <channel>` removes the channel and clears that site's login/storage, preserving other sites. If cleanup fails, the channel record remains and an error is returned for a retry.
- Neither operation subsequently recopies an existing login automatically.
