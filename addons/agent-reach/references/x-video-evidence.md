# Research an obtainable public X video

Use this companion for an X/Twitter post containing video. The Reach channel's
post text, thumbnails, thread result or card is not retrieved or watched media.
Keep the installed method's anonymous, read-only boundaries. No account, cookie,
proxy, alternate identity, third-party mirror or hosted transcription is admitted.
For shared caption/frame/audio handling, read [YouTube evidence](youtube-evidence.md).

## Select the route before the attempt

Resolve the recorded Reach Python and its installed yt-dlp options/source.
Use isolated empty HOME/XDG directories, an allowlisted environment, disabled
ambient config/plugins/remote components, finite time/retries and local-output
bounds. Keep signed stream URLs, headers and tokens out of saved metadata/logs.
Select only the requested post and media, never a profile crawl or unbounded feed.

In reviewed yt-dlp2026.8.19, default Twitter GraphQL extraction automatically
falls back to syndication on HTTP429. Ordinary zero-retry flags do not disable
that cross-API fallback. For a new anonymous attempt, explicit
`--extractor-args twitter:api=syndication` selects the limited public embed route
before the request. This is not a fallback after another tool/API was denied.
Its metadata may omit media, captions or other fields. Source support does not
prove that a particular post is obtainable.

Record the actual canonical post URL/ID, author, media ID/index, retrieval date,
duration and modality obtained. Distinguish original, quoted and externally
linked media. `/video/N` selects the numbered extended media entity; it does not
cover every video-card representation. Removing that suffix can expose cards
or external URL results. A source-supported same-route correction is appropriate
for a representation/format failure, never an access denial. For one post,
bound selected entries, for example `--playlist-items 1`, and inspect the current
exact-extractor selection, such as `--use-extractors '^twitter$'`. Do not silently
follow an external player or expand to broadcast/Spaces/profile extractors.
A rejected downstream extractor is a remaining capability limit.

## Obtain only the evidence needed

Inspect returned formats/tracks before acquisition. Prefer a small low-resolution
interval or a relevant still; obtain audio only when the question needs it.
Verify actual streams, decoded frames, local duration and hashes. Requested
source offset plus local time remains provenance-based until independently
aligned. A post's text is not its speech transcript; a missing caption track
is not silence. Use existing local ASR only for obtainable relevant audio and
its admitted language/model, not an automatic hosted-provider call.

Stop on login, verification, rate-limit or access denial across tools/backends.
API selection prevents one documented fallback, not every nested manifest,
redirect or media retry. Inspect the required path's actual behavior; if it cannot
respect the boundary, report the gap rather than claim enforced request-level
isolation. An empty/card-only or unsupported result is not a successful download,
and public availability is not a redistribution license. Retain valid evidence,
report unseen/unheard intervals and finish without installing another wrapper.
