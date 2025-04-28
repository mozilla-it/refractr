## Refractr PR Checklist

JIRA ticket: [link to relevant JIRA or other system ticket]

When creating a PR for Refractr, confirm you've done the following steps for a smooth CI and CD experience:
- [ ] Have you updated the relevant YAML in the PR?
- [ ] Have you checked the relevant YAML for any possible dupes regarding your domain?
- [ ] Have you checked if there are any TLS cert concerns - e.g. if the domain being redirected already exists, and it is being changed to point at refractr, is a temporary TLS 'outage' while waiting for certification via HTTP challenge okay? If not, add a note to the JIRA ticket.
- [ ] If desired, have you generated the nginx config manually to confirm updates work as expected?

After PR merge, next steps include:
- [ ] A merge to the `main` branch will automatically deploy refractr's stage environment -- deploying the prod environment requires a GitHub release to be created.
- [ ] Once deployed, refractr's certmap must be updated and DNS entries must be changed -- SRE can help with this. Please pull someone in on the JIRA ticket or ask for help in #sre on Slack.
