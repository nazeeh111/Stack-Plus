# Capability scope

Read this when the user asks what can be fetched, whether coverage is complete, or you need to assess completeness. These are declared capabilities, not proof that every network, account or content path has been tested.

The installed SKILL.md's anonymous-access and credential restrictions control this reference. Upstream account/browser capabilities below are descriptive; they do not admit those routes here.

## Three levels of evidence

- **Public routes to try**: the agent's existing web tools, native tools or public APIs may already satisfy the task, without browser installation or login. Answer from the evidence actually obtained.
- **Reach additions**: actions declared by this release; see `agent-reach channels`. Upstream describes saved dedicated-browser sessions and user login only when the chosen path actually needs it. Those account routes remain unadmitted in this installation.
- **Locally verified**: only specific actions that recently passed on this machine. Installation, a saved session and network reachability do not establish task acceptance.

## Channels in this release

| Channel | Public routes to try | Reach additions and limits |
|---|---|---|
| GitHub | Public repositories, READMEs, issues and PRs | Repository search; repository/issue/PR reads and returned comments. Assess private access separately. |
| YouTube | Search, titles and descriptions; native tools may obtain some comments or subtitle text | search/read/subtitle/transcribe. No unified comments action. A track list is not subtitle text; transcription without subtitles depends on the required tool. |
| Bilibili | Search and descriptions; some public APIs return comments and parent/child IDs | search/read/hot/subtitle. No unified comments action. Subtitle availability depends on the video and access route. |
| Reddit | Search, post text and some comments; some public JSON includes parent/child IDs | Browser search/read/subreddit; login depends on the route. No promise of a complete comment tree or all replies; no posting comments. |
| X/Twitter | Public posts found in search; some official public embeds return full text | search/profile/tweets/thread. Reading one post does not establish access to its reply stream or a complete comment tree. |
| Xiaohongshu | Public lists or indexes may include note IDs, authors and titles. Never invent missing fields. | search/read/comments; text descriptions, top-level comments and loaded replies. No promise of all comments or understanding images/video. |
| Instagram | Some indexed or shallow profile information; an HTML app shell is not a post | search finds users, profile reads a profile, posts reads a specified user's post descriptions. No unified comments action or claim to understand images/video. |
| Facebook | Some indexed content or HTML summaries; summaries may be truncated | search/profile. No unified detail or comments action. Do not treat a search summary as the full text. |
| LinkedIn | Search public jobs and read public job descriptions | jobs/read first try public pages; an explicitly selected opencli backend goes directly to the site. No promise that every job is readable. |
| BOSS Zhipin | Search indexes may contain job summaries | search/read job lists and descriptions. Never infer salary digits from encoded salary; detail fallback depends on the channel declaration. |
| V2EX | Topics, body text and public replies | hot/node/read/user. Coverage is what this response returns; hidden or missing replies are not guaranteed. |
| Xueqiu | Some public quotes and indexed information | quote/search/hot_posts/hot_stocks. Verify market-data and community paths separately. |
| Web | The agent's own search/read tools | Reach web search/read is an anonymous fallback. Summaries, app shells and verification pages are not full body text. |
| Xiaoyuzhou | Episode titles and descriptions | transcribe converts a full episode to text. Upstream requires a user-supplied Groq key through `agent-reach configure groq-key`; this credential route remains unadmitted here. |

Describe authenticated capabilities as actions that can be enabled or attempted, never as “login gives access to every comment.” If the user skips login, deliver the public evidence already obtained.
