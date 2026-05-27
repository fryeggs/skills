# chatgpt-search Analysis

Source: https://github.com/win4r/chatgpt-search

Core idea:
- Treat ChatGPT web as a browser-controlled search provider rather than a direct API.
- Reuse the user's real logged-in browser session.
- Convert user intent into a search-triggering prompt, usually prefixed with `Search the web for:`.
- Wait using polling instead of fixed sleeps, because ChatGPT web search may take 15-60 seconds.
- Extract the final assistant article, not the whole page.
- Return a concise answer in the user's language.

Useful upgrades for Codex/Claude:
- Make the OpenCLI connectivity check mandatory before claiming results.
- Support multi-turn use by carrying an explicit summary into the next prompt.
- Add a macOS ChatGPT Desktop fallback, but label it separately from browser web automation.
- Keep the skill small and put fragile selectors in one place so they are easy to update.

Known constraints:
- Browser automation needs a connected OpenCLI browser extension.
- ChatGPT web UI selectors may change.
- The skill should not expose cookies, auth files, or browser profile secrets.
- High-frequency calls may hit ChatGPT rate limits.
