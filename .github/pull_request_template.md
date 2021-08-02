## Refractr PR Checklist

JIRA ticket: [link to relevant JIRA or other system ticket]

When creating a PR for Refractr, confirm you've done the following steps for smooth CI and CD experiences:
- [ ] Is this the right place for your redirect (e.g. developer.mozilla.com/* redirects should be managed by MDN; other examples here as known)?
- [ ] Have you updated the relevant YAML in the PR?
- [ ] Have you checked the relevant YAML for any possible dupes regarding your domain?
- [ ] Have you checked if there are any TLS cert concerns - e.g. if the domain being redirected already exists, and it is being changed to point at Refractr, is a temporary TLS 'outage' while waiting for Lets Encrypt certification via HTTP challenge okay? If not, [have you followed these steps for using DNS challenges with our cert-manager setup](https://mana.mozilla.org/wiki/display/SRE/Refractr+-+How+To+-+DNS+Challenges)?
- [ ] If desired, have you generated the Nginx manually to confirm addition works as expected? 
- [ ] If desired, are you able to connect to EKS (cluster itse-apps-prod-1, namespace fluxcd) to more closely monitor the deploys?

After PR merge, next steps include:
- [ ] If going straight from main merge & Stage deploy to a release & production deploy, create the relevant GitHub release with an incremented version / tag applied.
- [ ] Confirm you are ready and able to perform the requested DNS creation or change post-deploy? 
