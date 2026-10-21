# AI With Georges — Daily AI News Automation

This package extends your existing static website; it does not replace the layout or your assets.

## 1. Upload to GitHub
Create a repository (e.g. `ai-with-georges`) and upload **all contents of this folder** to the repository root, including `.github/workflows/daily-news.yml`, `index.html`, `assets/`, `data/`, `scripts/` and the hidden `.github/` workflow folder.

## 2. OpenAI API key
Create an API key in https://platform.openai.com/api-keys (API billing is separate from ChatGPT). In GitHub repository **Settings → Secrets and variables → Actions → New repository secret**, set `OPENAI_API_KEY` to the key. Never put it in HTML, browser JavaScript or Git files.

## 3. Connect *existing* Netlify site
In Netlify, open **your existing aiwithgeorges.netlify.app project** → Project configuration / Build & deploy / Continuous deployment → Link repository (labels vary). Choose your GitHub repo. Configure `Build command` **empty** and `Publish directory` **.** (repository root), then save. Ensure this is the existing site, not a new project, to preserve its URL. If the dashboard does not allow linking a manually deployed project, use Netlify CLI: `npm install -g netlify-cli`, `netlify login`, `netlify link` (select existing site), then `netlify init` and choose to connect the existing repo, or consult Netlify support docs; do not accidentally create a duplicate site.

## 4. No dependencies
The automation uses Python standard library only; no npm install or Python packages are required.

## 5. Test
In GitHub **Actions → Publish Daily AI News → Run workflow**. Inspect logs for feed/API issues. Once successful, the bot commits `data/news.json`; Netlify detects Git pushes and deploys the news. Open your site and check the News section's Last published timestamp and clickable sources.

## 6. Schedule
Workflow triggers daily at **8:00 AM America/Chicago** using GitHub Actions timezone-aware schedule. Scheduled jobs may be delayed and will run from the default branch. GitHub Actions schedules can become disabled on inactive public repositories.

## 7. Data integrity
The script reads RSS feeds, asks OpenAI to summarize recent article metadata, validates all article URLs and dates against the RSS entries, and preserves the previous feed if too few verified entries are available. RSS headlines may not substantiate full article detail, so summaries are intentionally cautious; editorial review remains recommended. News data is static public JSON; the API key runs only inside GitHub Actions.

## Costs
GitHub/Netlify have free tiers with limits. OpenAI API usage is separately billed. Monitor monthly spending in the OpenAI Platform dashboard. No automatic interview video generation is included in this package.
