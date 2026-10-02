# Publish Ian's Tool Belt with GitHub Pages

The static website lives at `docs/index.html` on `main`. It has no build step, third-party scripts, analytics, secrets or external asset dependency. Keep `docs/.nojekyll` alongside it.

## One-time activation

A repository administrator or maintainer should open **Settings → Pages**:

1. Under Build and deployment, choose **Deploy from a branch**.
2. Select **main** and **/docs**.
3. Save, wait for GitHub's Pages build, and use the live URL shown by GitHub.

The source-file commit does not activate Pages by itself. The assistant's current GitHub connector can publish files but does not expose Pages settings changes. No live URL should be claimed until GitHub reports a successful deployment and the page is fetched.

Future changes to docs on main will publish through this branch source. The template branch is for new belts, not the Pages source. The personalized belt remains under review in PR #1 until merged.

Official reference: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
