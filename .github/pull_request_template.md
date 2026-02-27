## Refractr PR Checklist

JIRA ticket: [link to relevant JIRA or other system ticket]

When creating a PR for Refractr, confirm you've done the following steps for a smooth CI and CD experience:
- [ ] Have you updated the relevant YAML in the PR?
- [ ] Have you checked the relevant YAML for any possible dupes regarding your domain?
- [ ] Have you checked if there are any TLS cert concerns - e.g. if the domain being redirected already exists, and it is being changed to point at refractr, is a temporary TLS 'outage' while waiting for certification via HTTP challenge okay? If not, add a note to the JIRA ticket.
- [ ] If desired, have you generated the nginx config manually to confirm updates work as expected?

After PR merge:
- [ ] A merge to `main` automatically deploys both stage and prod.
- [ ] TLS certificates are created automatically by [Spacelift](https://mozilla.app.spacelift.io/stack/refractr-prod). DNS changes may still require SRE or IT to make changes in other systems (e.g. Markmonitor, Route53) -- ask in #mozcloud-support on Slack or in the JIRA ticket.
