# Deploying

Vercel deploys glossamer automatically from GitHub. There's no build config.

- **Push to `master`** → production: https://seanmcp-glossamer.vercel.app
- **Push a branch / open a PR** → preview URL
- **Roll back** from the Vercel dashboard

## Good to know

- Vercel loads `app` from `main.py`. Renaming either breaks deploys.
- An unsupported Python version quietly falls back to 3.12. Supported: 3.12–3.14.
- Dependencies come from `uv.lock`, so commit it.
- Each request is a serverless function: no in-memory state, no writable disk, and a time limit per request.
- Env vars go in the Vercel dashboard and only apply after a redeploy.
- Hobby plan: free, non-commercial only.
