# SRE Info
This is the SRE_INFO.md file which should be found in the root of any source code that is
administered by the Mozilla Web IT SRE team. We are available on #it-web-sre on slack.

## Infra Access
Currently this is a EKS cluster and requires the ~/.kube/config file to be present
so that k8s commands will work.  This is usually acquired via [MAWS](https://mana.mozilla.org/wiki/display/SECURITY/How+to+login+to+AWS+with+Single+Sign+On)

[SRE aws-vault setup](https://mana.mozilla.org/wiki/display/SRE/aws-vault)

[SRE account guide](https://mana.mozilla.org/wiki/display/SRE/AWS+Account+access+guide)

[SRE AWS accounts](https://github.com/mozilla-it/itsre-accounts/blob/master/accounts/mozilla-itsre/terraform.tfvars#L5)

## Secrets
Secrets are handled via [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

## Source Repos
[refractr](https://github.com/mozilla-it/refractr)

## Infra Repos
[helm-charts](https://github.com/mozilla-it/helm-charts/)
[itse-apps-stage-1-infra](https://github.com/mozilla-it/itse-apps-stage-1-infra)
[itse-apps-prod-1-infra](https://github.com/mozilla-it/itse-apps-prod-1-infra)

## Monitoring
Monitoring is done by the [Mozlenium](https://github.com/mozilla-it/mozlenium)

### Determining app health
* stage
    * `curl -k https://refractr.allizom.org/version`
    * `curl -k https://refractr.allizom.org/deployed`
* prod
    * `curl https://refractr.mozilla.org/version`
    * `curl https://refractr.mozilla.org/deployed`

### SSL Expiry checks in New Relic
[newbie.mozilla-slack.app](https://synthetics.newrelic.com/accounts/2239138/monitors/554cb212-7ab3-494d-af42-73495bf01ac7)

## SSL Certificates
Refractr uses LE certificates via the [cert-manager](https://cert-manager.io/)

## Cloud Account
AWS account itsre-apps 783633885093
