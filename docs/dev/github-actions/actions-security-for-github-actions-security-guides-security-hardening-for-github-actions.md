<!-- Source: https://docs.github.com/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions -->

[Skip to main content](#main-content)

[GitHub Docs](/en)

Version: Free, Pro, & Team

Search or ask Copilot

Search or askCopilot

Select language: current language is English

Search or ask Copilot

Search or askCopilot

Open menu

Open Sidebar

* [GitHub Actions](/en/actions "GitHub Actions")/
* [Reference](/en/actions/reference "Reference")/
* [Security](/en/actions/reference/security "Security")/
* [Secure use](/en/actions/reference/security/secure-use "Secure use")

[Home](/en)

## [GitHub Actions](/en/actions)

* Get started
  + [Quickstart](/en/actions/get-started/quickstart)
  + [Understand GitHub Actions](/en/actions/get-started/understand-github-actions)
  + [Continuous integration](/en/actions/get-started/continuous-integration)
  + [Continuous deployment](/en/actions/get-started/continuous-deployment)
  + [Actions vs Apps](/en/actions/get-started/actions-vs-apps)
* Concepts
  + Workflows and actions
    - [Workflows](/en/actions/concepts/workflows-and-actions/workflows)
    - [Variables](/en/actions/concepts/workflows-and-actions/variables)
    - [Contexts](/en/actions/concepts/workflows-and-actions/contexts)
    - [Expressions](/en/actions/concepts/workflows-and-actions/expressions)
    - [Reusing workflow configurations](/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations)
    - [Custom actions](/en/actions/concepts/workflows-and-actions/custom-actions)
    - [Deployment environments](/en/actions/concepts/workflows-and-actions/deployment-environments)
    - [Concurrency](/en/actions/concepts/workflows-and-actions/concurrency)
    - [Workflow artifacts](/en/actions/concepts/workflows-and-actions/workflow-artifacts)
    - [Dependency caching](/en/actions/concepts/workflows-and-actions/dependency-caching)
    - [Notifications for workflow runs](/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)
  + Runners
    - [GitHub-hosted runners](/en/actions/concepts/runners/github-hosted-runners)
    - [Larger runners](/en/actions/concepts/runners/larger-runners)
    - [Self-hosted runners](/en/actions/concepts/runners/self-hosted-runners)
    - [Private networking](/en/actions/concepts/runners/private-networking)
    - [Runner groups](/en/actions/concepts/runners/runner-groups)
    - [Runner scale sets](/en/actions/concepts/runners/runner-scale-sets)
    - [Actions Runner Controller](/en/actions/concepts/runners/actions-runner-controller)
    - [Support for ARC](/en/actions/concepts/runners/support-for-arc)
  + Security
    - [Secrets](/en/actions/concepts/security/secrets)
    - [GITHUB\_TOKEN](/en/actions/concepts/security/github_token)
    - [OpenID Connect](/en/actions/concepts/security/openid-connect)
    - [Artifact attestations](/en/actions/concepts/security/artifact-attestations)
    - [Script injections](/en/actions/concepts/security/script-injections)
    - [Compromised runners](/en/actions/concepts/security/compromised-runners)
    - [Kubernetes admissions controller](/en/actions/concepts/security/kubernetes-admissions-controller)
  + [Metrics](/en/actions/concepts/metrics)
  + [Billing and usage](/en/actions/concepts/billing-and-usage)
* How-tos
  + Write workflows
    - [Use workflow templates](/en/actions/how-tos/write-workflows/use-workflow-templates)
    - Choose when workflows run
      * [Trigger a workflow](/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
      * [Control jobs with conditions](/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions)
      * [Control workflow concurrency](/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
    - Choose where workflows run
      * [Choose the runner for a job](/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)
      * [Run jobs in a container](/en/actions/how-tos/write-workflows/choose-where-workflows-run/run-jobs-in-a-container)
    - Choose what workflows do
      * [Use jobs](/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs)
      * [Find and customize actions](/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions)
      * [Use GitHub CLI](/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli)
      * [Add scripts](/en/actions/how-tos/write-workflows/choose-what-workflows-do/add-scripts)
      * [Use secrets](/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
      * [Use variables](/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables)
      * [Pass job outputs](/en/actions/how-tos/write-workflows/choose-what-workflows-do/pass-job-outputs)
      * [Set default values for jobs](/en/actions/how-tos/write-workflows/choose-what-workflows-do/set-default-values-for-jobs)
      * [Deploy to environment](/en/actions/how-tos/write-workflows/choose-what-workflows-do/deploy-to-environment)
      * [Run job variations](/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)
  + Reuse automations
    - [Reuse workflows](/en/actions/how-tos/reuse-automations/reuse-workflows)
    - [Create workflow templates](/en/actions/how-tos/reuse-automations/create-workflow-templates)
    - [Share across private repositories](/en/actions/how-tos/reuse-automations/share-across-private-repositories)
    - [Share with your organization](/en/actions/how-tos/reuse-automations/share-with-your-organization)
  + Secure your work
    - Use artifact attestations
      * [Use artifact attestations](/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
      * [Increase security rating](/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating)
      * [Enforce artifact attestations](/en/actions/how-tos/secure-your-work/use-artifact-attestations/enforce-artifact-attestations)
      * [Verify attestations offline](/en/actions/how-tos/secure-your-work/use-artifact-attestations/verify-attestations-offline)
      * [Manage attestations](/en/actions/how-tos/secure-your-work/use-artifact-attestations/manage-attestations)
    - Security harden deployments
      * [OIDC in AWS](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
      * [OIDC in Azure](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
      * [OIDC in Google Cloud Platform](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform)
      * [OIDC in HashiCorp Vault](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-hashicorp-vault)
      * [OIDC in JFrog](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-jfrog)
      * [OIDC in PyPI](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi)
      * [OIDC in cloud providers](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-cloud-providers)
      * [OIDC with reusable workflows](/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows)
  + Deploy
    - Configure and manage deployments
      * [Control deployments](/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)
      * [View deployment history](/en/actions/how-tos/deploy/configure-and-manage-deployments/view-deployment-history)
      * [Manage environments](/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
      * [Review deployments](/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments)
      * [Create custom protection rules](/en/actions/how-tos/deploy/configure-and-manage-deployments/create-custom-protection-rules)
      * [Configure custom protection rules](/en/actions/how-tos/deploy/configure-and-manage-deployments/configure-custom-protection-rules)
    - Deploy to third-party platforms
      * [Node.js to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/nodejs-to-azure-app-service)
      * [Python to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/python-to-azure-app-service)
      * [Java to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/java-to-azure-app-service)
      * [.NET to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/net-to-azure-app-service)
      * [PHP to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/php-to-azure-app-service)
      * [Docker to Azure App Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/docker-to-azure-app-service)
      * [Azure Static Web App](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/azure-static-web-app)
      * [Azure Kubernetes Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/azure-kubernetes-service)
      * [Amazon Elastic Container Service](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/amazon-elastic-container-service)
      * [Google Kubernetes Engine](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/google-kubernetes-engine)
      * [Sign Xcode applications](/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications)
  + Create and publish actions
    - [Manage custom actions](/en/actions/how-tos/create-and-publish-actions/manage-custom-actions)
    - [Create a CLI action](/en/actions/how-tos/create-and-publish-actions/create-a-cli-action)
    - [Set exit codes](/en/actions/how-tos/create-and-publish-actions/set-exit-codes)
    - [Publish in GitHub Marketplace](/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
    - [Release and maintain actions](/en/actions/how-tos/create-and-publish-actions/release-and-maintain-actions)
    - [Use immutable releases](/en/actions/how-tos/create-and-publish-actions/using-immutable-releases-and-tags-to-manage-your-actions-releases)
  + Manage workflow runs
    - [Manually run a workflow](/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
    - [Re-run workflows and jobs](/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
    - [Cancel a workflow run](/en/actions/how-tos/manage-workflow-runs/cancel-a-workflow-run)
    - [Disable and enable workflows](/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)
    - [Skip workflow runs](/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)
    - [Delete a workflow run](/en/actions/how-tos/manage-workflow-runs/delete-a-workflow-run)
    - [Download workflow artifacts](/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)
    - [Remove workflow artifacts](/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts)
    - [Manage caches](/en/actions/how-tos/manage-workflow-runs/manage-caches)
    - [Approve runs from forks](/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)
  + Manage runners
    - GitHub-hosted runners
      * [Use GitHub-hosted runners](/en/actions/how-tos/manage-runners/github-hosted-runners/use-github-hosted-runners)
      * [Customize runners](/en/actions/how-tos/manage-runners/github-hosted-runners/customize-runners)
      * [View current jobs](/en/actions/how-tos/manage-runners/github-hosted-runners/view-current-jobs)
      * Connect to a private network
        + [Connect with OIDC](/en/actions/how-tos/manage-runners/github-hosted-runners/connect-to-a-private-network/connect-with-oidc)
        + [Connect with WireGuard](/en/actions/how-tos/manage-runners/github-hosted-runners/connect-to-a-private-network/connect-with-wireguard)
    - Self-hosted runners
      * [Add runners](/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)
      * [Run scripts](/en/actions/how-tos/manage-runners/self-hosted-runners/run-scripts)
      * [Customize containers](/en/actions/how-tos/manage-runners/self-hosted-runners/customize-containers)
      * [Configure the application](/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application)
      * [Apply labels](/en/actions/how-tos/manage-runners/self-hosted-runners/apply-labels)
      * [Use in a workflow](/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow)
      * [Manage access](/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access)
      * [Monitor and troubleshoot](/en/actions/how-tos/manage-runners/self-hosted-runners/monitor-and-troubleshoot)
      * [Remove runners](/en/actions/how-tos/manage-runners/self-hosted-runners/remove-runners)
    - Larger runners
      * [Manage larger runners](/en/actions/how-tos/manage-runners/larger-runners/manage-larger-runners)
      * [Control access](/en/actions/how-tos/manage-runners/larger-runners/control-access)
      * [Use larger runners](/en/actions/how-tos/manage-runners/larger-runners/use-larger-runners)
      * [Use custom images](/en/actions/how-tos/manage-runners/larger-runners/use-custom-images)
    - [Use proxy servers](/en/actions/how-tos/manage-runners/use-proxy-servers)
  + Monitor workflows
    - [Use the visualization graph](/en/actions/how-tos/monitor-workflows/use-the-visualization-graph)
    - [View workflow run history](/en/actions/how-tos/monitor-workflows/view-workflow-run-history)
    - [View job execution time](/en/actions/how-tos/monitor-workflows/view-job-execution-time)
    - [Add a status badge](/en/actions/how-tos/monitor-workflows/add-a-status-badge)
    - [Use workflow run logs](/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)
    - [Enable debug logging](/en/actions/how-tos/monitor-workflows/enable-debug-logging)
  + [Troubleshoot workflows](/en/actions/how-tos/troubleshoot-workflows)
  + Administer
    - [View metrics](/en/actions/how-tos/administer/view-metrics)
  + [Get support](/en/actions/how-tos/get-support)
* Reference
  + Workflows and actions
    - [Workflow syntax](/en/actions/reference/workflows-and-actions/workflow-syntax)
    - [Events that trigger workflows](/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
    - [Workflow commands](/en/actions/reference/workflows-and-actions/workflow-commands)
    - [Variables](/en/actions/reference/workflows-and-actions/variables)
    - [Expressions](/en/actions/reference/workflows-and-actions/expressions)
    - [Contexts](/en/actions/reference/workflows-and-actions/contexts)
    - [Deployments and environments](/en/actions/reference/workflows-and-actions/deployments-and-environments)
    - [Dependency caching](/en/actions/reference/workflows-and-actions/dependency-caching)
    - [Reusing workflow configurations](/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
    - [Metadata syntax](/en/actions/reference/workflows-and-actions/metadata-syntax)
    - [Workflow cancellation](/en/actions/reference/workflows-and-actions/workflow-cancellation)
    - [Dockerfile support](/en/actions/reference/workflows-and-actions/dockerfile-support)
  + Runners
    - [GitHub-hosted runners](/en/actions/reference/runners/github-hosted-runners)
    - [Larger runners](/en/actions/reference/runners/larger-runners)
    - [Self-hosted runners](/en/actions/reference/runners/self-hosted-runners)
  + Security
    - [Secure use](/en/actions/reference/security/secure-use)
    - [Secrets](/en/actions/reference/security/secrets)
    - [OIDC](/en/actions/reference/security/oidc)
  + [Limits](/en/actions/reference/limits)
  + GitHub Actions Importer
    - [Supplemental arguments and settings](/en/actions/reference/github-actions-importer/supplemental-arguments-and-settings)
    - [Custom transformers](/en/actions/reference/github-actions-importer/custom-transformers)
* Tutorials
  + [Create an example workflow](/en/actions/tutorials/create-an-example-workflow)
  + Build and test code
    - [Go](/en/actions/tutorials/build-and-test-code/go)
    - [Java with Ant](/en/actions/tutorials/build-and-test-code/java-with-ant)
    - [Java with Gradle](/en/actions/tutorials/build-and-test-code/java-with-gradle)
    - [Java with Maven](/en/actions/tutorials/build-and-test-code/java-with-maven)
    - [.NET](/en/actions/tutorials/build-and-test-code/net)
    - [Node.js](/en/actions/tutorials/build-and-test-code/nodejs)
    - [PowerShell](/en/actions/tutorials/build-and-test-code/powershell)
    - [Python](/en/actions/tutorials/build-and-test-code/python)
    - [Ruby](/en/actions/tutorials/build-and-test-code/ruby)
    - [Rust](/en/actions/tutorials/build-and-test-code/rust)
    - [Swift](/en/actions/tutorials/build-and-test-code/swift)
    - [Xamarin apps](/en/actions/tutorials/build-and-test-code/xamarin-apps)
  + [Authenticate with GITHUB\_TOKEN](/en/actions/tutorials/authenticate-with-github_token)
  + Create actions
    - [Create a JavaScript action](/en/actions/tutorials/create-actions/create-a-javascript-action)
    - [Create a composite action](/en/actions/tutorials/create-actions/create-a-composite-action)
  + Publish packages
    - [Publish Docker images](/en/actions/tutorials/publish-packages/publish-docker-images)
    - [Publish Java packages with Gradle](/en/actions/tutorials/publish-packages/publish-java-packages-with-gradle)
    - [Publish Java packages with Maven](/en/actions/tutorials/publish-packages/publish-java-packages-with-maven)
    - [Publish Node.js packages](/en/actions/tutorials/publish-packages/publish-nodejs-packages)
  + Manage your work
    - [Add labels to issues](/en/actions/tutorials/manage-your-work/add-labels-to-issues)
    - [Close inactive issues](/en/actions/tutorials/manage-your-work/close-inactive-issues)
    - [Add comments with labels](/en/actions/tutorials/manage-your-work/add-comments-with-labels)
    - [Schedule issue creation](/en/actions/tutorials/manage-your-work/schedule-issue-creation)
  + [Store and share data](/en/actions/tutorials/store-and-share-data)
  + Use containerized services
    - [Create a Docker container action](/en/actions/tutorials/use-containerized-services/create-a-docker-container-action)
    - [Use Docker service containers](/en/actions/tutorials/use-containerized-services/use-docker-service-containers)
    - [Create PostgreSQL service containers](/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers)
    - [Create Redis service containers](/en/actions/tutorials/use-containerized-services/create-redis-service-containers)
  + Migrate to GitHub Actions
    - Automated migrations
      * [Use GitHub Actions Importer](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/use-github-actions-importer)
      * [Azure DevOps migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/azure-devops-migration)
      * [Bamboo migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/bamboo-migration)
      * [Bitbucket Pipelines migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/bitbucket-pipelines-migration)
      * [CircleCI migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/circleci-migration)
      * [GitLab migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/gitlab-migration)
      * [Jenkins migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/jenkins-migration)
      * [Travis CI migration](/en/actions/tutorials/migrate-to-github-actions/automated-migrations/travis-ci-migration)
    - Manual migrations
      * [Migrate from Azure Pipelines](/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-azure-pipelines)
      * [Migrate from CircleCI](/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-circleci)
      * [Migrate from GitLab CI/CD](/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-gitlab-cicd)
      * [Migrate from Jenkins](/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-jenkins)
      * [Migrate from Travis CI](/en/actions/tutorials/migrate-to-github-actions/manual-migrations/migrate-from-travis-ci)
  + Use Actions Runner Controller
    - [Quickstart](/en/actions/tutorials/use-actions-runner-controller/quickstart)
    - [Authenticate to the API](/en/actions/tutorials/use-actions-runner-controller/authenticate-to-the-api)
    - [Deploy runner scale sets](/en/actions/tutorials/use-actions-runner-controller/deploy-runner-scale-sets)
    - [Use ARC in a workflow](/en/actions/tutorials/use-actions-runner-controller/use-arc-in-a-workflow)
    - [Troubleshoot](/en/actions/tutorials/use-actions-runner-controller/troubleshoot)

* [GitHub Actions](/en/actions "GitHub Actions")/
* [Reference](/en/actions/reference "Reference")/
* [Security](/en/actions/reference/security "Security")/
* [Secure use](/en/actions/reference/security/secure-use "Secure use")

# Secure use reference

Security practices for writing workflows and using GitHub Actions features.

## In this article

* [Writing workflows](#writing-workflows)
* [Using third-party actions](#using-third-party-actions)
* [GitHub's security features](#githubs-security-features)

Find information about security best practices when you are writing workflows and using GitHub Actions security features.

## [Writing workflows](#writing-workflows)

### [Use secrets for sensitive information](#use-secrets-for-sensitive-information)

Because there are multiple ways a secret value can be transformed, automatic redaction is not guaranteed. Adhere to the following best practices to limit risks associated with secrets.

* **Principle of least privilege**
  + Any user with write access to your repository has read access to all secrets configured in your repository. Therefore, you should ensure that the credentials being used within workflows have the least privileges required.
  + Actions can use the `GITHUB_TOKEN` by accessing it from the `github.token` context. For more information, see [Contexts reference](/en/actions/learn-github-actions/contexts#github-context). You should therefore make sure that the `GITHUB_TOKEN` is granted the minimum required permissions. It's good security practice to set the default permission for the `GITHUB_TOKEN` to read access only for repository contents. The permissions can then be increased, as required, for individual jobs within the workflow file. For more information, see [Use GITHUB\_TOKEN for authentication in workflows](/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token).
* **Mask sensitive data**
  + Sensitive data should **never** be stored as plaintext in workflow files. Mask all sensitive information that is not a GitHub secret by using `::add-mask::VALUE`. This causes the value to be treated as a secret and redacted from logs. For more information about masking data, see [Workflow commands for GitHub Actions](/en/actions/using-workflows/workflow-commands-for-github-actions#masking-a-value-in-a-log).
* **Delete and rotate exposed secrets**
  + Redacting of secrets is performed by your workflow runners. This means a secret will only be redacted if it was used within a job and is accessible by the runner. If an unredacted secret is sent to a workflow run log, you should delete the log and rotate the secret. For information on deleting logs, see [Using workflow run logs](/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs#deleting-logs).
* **Never use structured data as a secret**
  + Structured data can cause secret redaction within logs to fail, because redaction largely relies on finding an exact match for the specific secret value. For example, do not use a blob of JSON, XML, or YAML (or similar) to encapsulate a secret value, as this significantly reduces the probability the secrets will be properly redacted. Instead, create individual secrets for each sensitive value.
* **Register all secrets used within workflows**
  + If a secret is used to generate another sensitive value within a workflow, that generated value should be formally [registered as a secret](https://github.com/actions/toolkit/tree/main/packages/core#setting-a-secret), so that it will be redacted if it ever appears in the logs. For example, if using a private key to generate a signed JWT to access a web API, be sure to register that JWT as a secret or else it won’t be redacted if it ever enters the log output.
  + Registering secrets applies to any sort of transformation/encoding as well. If your secret is transformed in some way (such as Base64 or URL-encoded), be sure to register the new value as a secret too.
* **Audit how secrets are handled**
  + Audit how secrets are used, to help ensure they’re being handled as expected. You can do this by reviewing the source code of the repository executing the workflow, and checking any actions used in the workflow. For example, check that they’re not sent to unintended hosts, or explicitly being printed to log output.
  + View the run logs for your workflow after testing valid/invalid inputs, and check that secrets are properly redacted, or not shown. It's not always obvious how a command or tool you’re invoking will send errors to `STDOUT` and `STDERR`, and secrets might subsequently end up in error logs. As a result, it is good practice to manually review the workflow logs after testing valid and invalid inputs. For information on how to clean up workflow logs that may unintentionally contain sensitive data, see [Using workflow run logs](/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs#deleting-logs).
* **Audit and rotate registered secrets**
  + Periodically review the registered secrets to confirm they are still required. Remove those that are no longer needed.
  + Rotate secrets periodically to reduce the window of time during which a compromised secret is valid.
* **Consider requiring review for access to secrets**
  + You can use required reviewers to protect environment secrets. A workflow job cannot access environment secrets until approval is granted by a reviewer. For more information about storing secrets in environments or requiring reviews for environments, see [Using secrets in GitHub Actions](/en/actions/security-guides/using-secrets-in-github-actions) and [Managing environments for deployment](/en/actions/deployment/targeting-different-environments/managing-environments-for-deployment).

### [Good practices for mitigating script injection attacks](#good-practices-for-mitigating-script-injection-attacks)

Recommended approaches for mitigating the risk of script injection in your workflows:

#### [Use an action instead of an inline script](#use-an-action-instead-of-an-inline-script)

The recommended approach is to create a JavaScript action that processes the context value as an argument. This approach is not vulnerable to the injection attack, since the context value is not used to generate a shell script, but is instead passed to the action as an argument:

```
uses: fakeaction/checktitle@v3
with:
  title: ${{ github.event.pull_request.title }}
```

#### [Use an intermediate environment variable](#use-an-intermediate-environment-variable)

For inline scripts, the preferred approach to handling untrusted input is to set the value of the expression to an intermediate environment variable. The following example uses Bash to process the `github.event.pull_request.title` value as an environment variable:

```
      - name: Check PR title
        env:
          TITLE: ${{ github.event.pull_request.title }}
        run: |
          if [[ "$TITLE" =~ ^octocat ]]; then
          echo "PR title starts with 'octocat'"
          exit 0
          else
          echo "PR title did not start with 'octocat'"
          exit 1
          fi
```

In this example, the attempted script injection is unsuccessful, which is reflected by the following lines in the log:

```
   env:
     TITLE: a"; ls $GITHUB_WORKSPACE"
PR title did not start with 'octocat'
```

With this approach, the value of the `${{ github.event.pull_request.title }}` expression is stored in memory and used as a variable, and doesn't interact with the script generation process. In addition, consider using double quote shell variables to avoid [word splitting](https://github.com/koalaman/shellcheck/wiki/SC2086), but this is [one of many](https://mywiki.wooledge.org/BashPitfalls) general recommendations for writing shell scripts, and is not specific to GitHub Actions.

#### [Using workflow templates for code scanning](#using-workflow-templates-for-code-scanning)

Code scanning allows you to find security vulnerabilities before they reach production. GitHub provides workflow templates for code scanning. You can use these suggested workflows to construct your code scanning workflows, instead of starting from scratch. GitHub's workflow, the CodeQL analysis workflow, is powered by CodeQL. There are also third-party workflow templates available.

For more information, see [About code scanning](/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning) and [Configuring advanced setup for code scanning](/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/configuring-advanced-setup-for-code-scanning#configuring-code-scanning-using-third-party-actions).

#### [Restricting permissions for tokens](#restricting-permissions-for-tokens)

To help mitigate the risk of an exposed token, consider restricting the assigned permissions. For more information, see [Use GITHUB\_TOKEN for authentication in workflows](/en/actions/security-guides/automatic-token-authentication#modifying-the-permissions-for-the-github_token).

## [Using third-party actions](#using-third-party-actions)

The individual jobs in a workflow can interact with (and compromise) other jobs. For example, a job querying the environment variables used by a later job, writing files to a shared directory that a later job processes, or even more directly by interacting with the Docker socket and inspecting other running containers and executing commands in them.

This means that a compromise of a single action within a workflow can be very significant, as that compromised action would have access to all secrets configured on your repository, and may be able to use the `GITHUB_TOKEN` to write to the repository. Consequently, there is significant risk in sourcing actions from third-party repositories on GitHub. For information on some of the steps an attacker could take, see [Secure use reference](/en/actions/security-guides/security-hardening-for-github-actions#potential-impact-of-a-compromised-runner).

You can help mitigate this risk by following these good practices:

* **Pin actions to a full-length commit SHA**

  Pinning an action to a full-length commit SHA is currently the only way to use an action as an immutable release. Pinning to a particular SHA helps mitigate the risk of a bad actor adding a backdoor to the action's repository, as they would need to generate a SHA-1 collision for a valid Git object payload. When selecting a SHA, you should verify it is from the action's repository and not a repository fork.

  For an example of using a full-length commit SHA in a workflow, see [Using pre-written building blocks in your workflow](/en/actions/how-tos/write-workflows/choose-what-workflows-do/find-and-customize-actions#using-shas).

  GitHub offers policies at the repository and organization level to require actions to be pinned to a full-length commit SHA:

  + To configure the policy at the repository level, see [Managing GitHub Actions settings for a repository](/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#managing-github-actions-permissions-for-your-repository).
  + To configure the policy at the organization level, see [Disabling or limiting GitHub Actions for your organization](/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#managing-github-actions-permissions-for-your-organization).
* **Audit the source code of the action**

  Ensure that the action is handling the content of your repository and secrets as expected. For example, check that secrets are not sent to unintended hosts, or are not inadvertently logged.
* **Pin actions to a tag only if you trust the creator**

  Although pinning to a commit SHA is the most secure option, specifying a tag is more convenient and is widely used. If you’d like to specify a tag, then be sure that you trust the action's creators. The ‘Verified creator’ badge on GitHub Marketplace is a useful signal, as it indicates that the action was written by a team whose identity has been verified by GitHub. Note that there is risk to this approach even if you trust the author, because a tag can be moved or deleted if a bad actor gains access to the repository storing the action.

### [Reusing third-party workflows](#reusing-third-party-workflows)

The same principles described above for using third-party actions also apply to using third-party workflows. You can help mitigate the risks associated with reusing workflows by following the same good practices outlined above. For more information, see [Reuse workflows](/en/actions/using-workflows/reusing-workflows).

## [GitHub's security features](#githubs-security-features)

GitHub provides many features to make your code more secure. You can use GitHub's built-in features to understand the actions your workflows depend on, ensure you are notified about vulnerabilities in the actions you consume, or automate the process of keeping the actions in your workflows up to date. If you publish and maintain actions, you can use GitHub to communicate with your community about vulnerabilities and how to fix them. For more information about security features that GitHub offers, see [GitHub security features](/en/code-security/getting-started/github-security-features#about-githubs-security-features).

### [Using `CODEOWNERS` to monitor changes](#using-codeowners-to-monitor-changes)

You can use the `CODEOWNERS` feature to control how changes are made to your workflow files. For example, if all your workflow files are stored `.github/workflows`, you can add this directory to the code owners list, so that any proposed changes to these files will first require approval from a designated reviewer.

For more information, see [About code owners](/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

### [Using OpenID Connect to access cloud resources](#using-openid-connect-to-access-cloud-resources)

If your GitHub Actions workflows need to access resources from a cloud provider that supports OpenID Connect (OIDC), you can configure your workflows to authenticate directly to the cloud provider. This will let you stop storing these credentials as long-lived secrets and provide other security benefits. For more information, see [OpenID Connect](/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect).

Note

Support for custom claims for OIDC is unavailable in AWS.

### [Using Dependabot version updates to keep actions up to date](#using-dependabot-version-updates-to-keep-actions-up-to-date)

You can use Dependabot to ensure that references to actions and reusable workflows used in your repository are kept up to date. Actions are often updated with bug fixes and new features to make automated processes faster, safer, and more reliable. Dependabot takes the effort out of maintaining your dependencies as it does this automatically for you. For more information, see [Keeping your actions up to date with Dependabot](/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot) and [About Dependabot security updates](/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates).

### [Preventing GitHub Actions from creating or approving pull requests](#preventing-github-actions-from-creating-or-approving-pull-requests)

You can choose to allow or prevent GitHub Actions workflows from creating or approving pull requests. Allowing workflows, or any other automation, to create or approve pull requests could be a security risk if the pull request is merged without proper oversight.

For more information on how to configure this setting, see [Disabling or limiting GitHub Actions for your organization](/en/github/setting-up-and-managing-organizations-and-teams/disabling-or-limiting-github-actions-for-your-organization#preventing-github-actions-from-creating-or-approving-pull-requests), and [Managing GitHub Actions settings for a repository](/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#preventing-github-actions-from-creating-or-approving-pull-requests).

### [Using code scanning to secure workflows](#using-code-scanning-to-secure-workflows)

Code scanning can automatically detect and suggest improvements for common vulnerable patterns used in GitHub Actions workflows.
For more information on how to enable code scanning, see [Configuring default setup for code scanning](/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning).

### [Using OpenSSF Scorecards to secure workflow dependencies](#using-openssf-scorecards-to-secure-workflow-dependencies)

[Scorecards](https://github.com/ossf/scorecard) is an automated security tool that flags risky supply chain practices. You can use the [Scorecards action](https://github.com/marketplace/actions/ossf-scorecard-action) and [workflow template](https://github.com/actions/starter-workflows) to follow best security practices. Once configured, the Scorecards action runs automatically on repository changes, and alerts developers about risky supply chain practices using the built-in code scanning experience. The Scorecards project runs a number of checks, including script injection attacks, token permissions, and pinned actions.

### [Hardening for GitHub-hosted runners](#hardening-for-github-hosted-runners)

GitHub-hosted runners take measures to help you mitigate security risks.

#### [Reviewing the supply chain for GitHub-hosted runners](#reviewing-the-supply-chain-for-github-hosted-runners)

For GitHub-hosted runners created from images maintained by GitHub, you can view a software bill of materials (SBOM) to see what software was pre-installed on the runner. You can provide your users with the SBOM which they can run through a vulnerability scanner to validate if there are any vulnerabilities in the product. If you are building artifacts, you can include this SBOM in your bill of materials for a comprehensive list of everything that went into creating your software.

SBOMs are available for Ubuntu, Windows, and macOS runner images maintained by GitHub. You can locate the SBOM for your build in the release assets at <https://github.com/actions/runner-images/releases>. An SBOM with a filename in the format of `sbom.IMAGE-NAME.json.zip` can be found in the attachments of each release.

For third-party images, such as the images for ARM-powered runners, you can find details of the software that's included in the image in the [`actions/partner-runner-images` repository](https://github.com/actions/partner-runner-images).

#### [Denying access to hosts](#denying-access-to-hosts)

GitHub-hosted runners are provisioned with an `etc/hosts` file that blocks network access to various cryptocurrency mining pools and malicious sites. Hosts such as MiningMadness.com and cpu-pool.com are rerouted to localhost so that they do not present a significant security risk. For more information, see [GitHub-hosted runners](/en/actions/using-github-hosted-runners/about-github-hosted-runners).

### [Hardening for self-hosted runners](#hardening-for-self-hosted-runners)

**GitHub-hosted** runners execute code within ephemeral and clean isolated virtual machines, meaning there is no way to persistently compromise this environment, or otherwise gain access to more information than was placed in this environment during the bootstrap process.

**Self-hosted** runners for GitHub do not have guarantees around running in ephemeral clean virtual machines, and can be persistently compromised by untrusted code in a workflow.

As a result, self-hosted runners should almost [never be used for public repositories](/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) on GitHub, because any user can open pull requests against the repository and compromise the environment. Similarly, be cautious when using self-hosted runners on private or internal repositories, as anyone who can fork the repository and open a pull request (generally those with read access to the repository) are able to compromise the self-hosted runner environment, including gaining access to secrets and the `GITHUB_TOKEN` which, depending on its settings, can grant write access to the repository. Although workflows can control access to environment secrets by using environments and required reviews, these workflows are not run in an isolated environment and are still susceptible to the same risks when run on a self-hosted runner.

Organization owners can choose which repositories are allowed to create repository-level self-hosted runners.

For more information, see [Disabling or limiting GitHub Actions for your organization](/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization#limiting-the-use-of-self-hosted-runners).

When a self-hosted runner is defined at the organization or enterprise level, GitHub can schedule workflows from multiple repositories onto the same runner. Consequently, a security compromise of these environments can result in a wide impact. To help reduce the scope of a compromise, you can create boundaries by organizing your self-hosted runners into separate groups. You can restrict what organizations and repositories can access runner groups. For more information, see [Managing access to self-hosted runners using groups](/en/actions/hosting-your-own-runners/managing-self-hosted-runners/managing-access-to-self-hosted-runners-using-groups).

You should also consider the environment of the self-hosted runner machines:

* What sensitive information resides on the machine configured as a self-hosted runner? For example, private SSH keys, API access tokens, among others.
* Does the machine have network access to sensitive services? For example, Azure or AWS metadata services. The amount of sensitive information in this environment should be kept to a minimum, and you should always be mindful that any user capable of invoking workflows has access to this environment.

Some customers might attempt to partially mitigate these risks by implementing systems that automatically destroy the self-hosted runner after each job execution. However, this approach might not be as effective as intended, as there is no way to guarantee that a self-hosted runner only runs one job. Some jobs will use secrets as command-line arguments which can be seen by another job running on the same runner, such as `ps x -w`. This can lead to secret leaks.

#### [Using just-in-time runners](#using-just-in-time-runners)

To improve runner registration security, you can use the REST API to create ephemeral, just-in-time (JIT) runners. These self-hosted runners perform at most one job before being automatically removed from the repository, organization, or enterprise. For more information about configuring JIT runners, see [REST API endpoints for self-hosted runners](/en/rest/actions/self-hosted-runners#create-configuration-for-a-just-in-time-runner-for-an-organization).

Note

Re-using hardware to host JIT runners can risk exposing information from the environment. Use automation to ensure the JIT runner uses a clean environment. For more information, see [Self-hosted runners reference](/en/actions/hosting-your-own-runners/managing-self-hosted-runners/autoscaling-with-self-hosted-runners#using-ephemeral-runners-for-autoscaling).

Once you have the config file from the REST API response, you can pass it to the runner at startup.

```
./run.sh --jitconfig ${encoded_jit_config}
```

#### [Planning your management strategy for self-hosted runners](#planning-your-management-strategy-for-self-hosted-runners)

A self-hosted runner can be added to various levels in your GitHub hierarchy: the enterprise, organization, or repository level. This placement determines who will be able to manage the runner:

**Centralized management:**

* If you plan to have a centralized team own the self-hosted runners, then the recommendation is to add your runners at the highest mutual organization or enterprise level. This gives your team a single location to view and manage your runners.
* If you only have a single organization, then adding your runners at the organization level is effectively the same approach, but you might encounter difficulties if you add another organization in the future.

**Decentralized management:**

* If each team will manage their own self-hosted runners, then the recommendation is to add the runners at the highest level of team ownership. For example, if each team owns their own organization, then it will be simplest if the runners are added at the organization level too.
* You could also add runners at the repository level, but this will add management overhead and also increases the numbers of runners you need, since you cannot share runners between repositories.

#### [Authenticating to your cloud provider](#authenticating-to-your-cloud-provider)

If you are using GitHub Actions to deploy to a cloud provider, or intend to use HashiCorp Vault for secret management, then it's recommended that you consider using OpenID Connect to create short-lived, well-scoped access tokens for your workflow runs. For more information, see [OpenID Connect](/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect).

### [Auditing GitHub Actions events](#auditing-github-actions-events)

You can use the security log to monitor activity for your user account and the audit log to monitor activity in your organization. The security and audit log records the type of action, when it was run, and which personal account performed the action.

For example, you can use the audit log to track the `org.update_actions_secret` event, which tracks changes to organization secrets.

![Screenshot showing a search for "action:org.update_actions_secret" in the audit log for an organization. Two results are shown.](/assets/cb-82962/images/help/repository/audit-log-entries.png)

For the full list of events that you can find in the audit log for each account type, see the following articles:

* [Security log events](/en/authentication/keeping-your-account-and-data-secure/security-log-events)
* [Audit log events for your organization](/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/audit-log-events-for-your-organization)

### [Understanding dependencies in your workflows](#understanding-dependencies-in-your-workflows)

You can use the dependency graph to explore the actions that the workflows in your repository use. The dependency graph is a summary of the manifest and lock files stored in a repository. It also recognizes files in `./github/workflows/` as manifests, which means that any actions or workflows referenced using the syntax `jobs[*].steps[*].uses` or `jobs.<job_id>.uses` will be parsed as dependencies.

The dependency graph shows the following information about actions used in workflows:

* The account or organization that owns the action.
* The workflow file that references the action.
* The version or SHA the action is pinned to.

In the dependency graph, dependencies are automatically sorted by vulnerability severity. If any of the actions you use have security advisories, they will display at the top of the list. You can navigate to the advisory from the dependency graph and access instructions for resolving the vulnerability.

The dependency graph is enabled for public repositories, and you can choose to enable it on private repositories. For more information about using the dependency graph, see [Exploring the dependencies of a repository](/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exploring-the-dependencies-of-a-repository).

### [Being aware of security vulnerabilities in actions you use](#being-aware-of-security-vulnerabilities-in-actions-you-use)

For actions available on the marketplace, GitHub reviews related security advisories and then adds those advisories to the GitHub Advisory Database. You can search the database for actions that you use to find information about existing vulnerabilities and instructions for how to fix them. To streamline your search, use the GitHub Actions filter in the [GitHub Advisory Database](https://github.com/advisories?query=type%3Areviewed+ecosystem%3Aactions).

You can set up your repositories so that you:

* Receive alerts when actions used in your workflows receive a vulnerability report. For more information, see [Monitoring the actions in your workflows](#monitoring-the-actions-in-your-workflows).
* Are warned about existing advisories when you add or update an action in a workflow. For more information, see [Screening actions for vulnerabilities in new or updated workflows](#screening-actions-for-vulnerabilities-in-new-or-updated-workflows).

#### [Monitoring the actions in your workflows](#monitoring-the-actions-in-your-workflows)

You can use Dependabot to monitor the actions in your workflows and enable Dependabot alerts to notify you when an action you use has a reported vulnerability. Dependabot performs a scan of the default branch of the repositories where it is enabled to detect insecure dependencies. Dependabot generates Dependabot alerts when a new advisory is added to the GitHub Advisory Database or when an action you use is updated.

Note

Dependabot only creates alerts for vulnerable actions that use semantic versioning and will not create alerts for actions pinned to SHA values.

You can enable Dependabot alerts for your personal account, for a repository, or for an organization. For more information, see [Configuring Dependabot alerts](/en/code-security/dependabot/dependabot-alerts/configuring-dependabot-alerts).

You can view all open and closed Dependabot alerts and corresponding Dependabot security updates in your repository's Dependabot alerts tab. For more information, see [Viewing and updating Dependabot alerts](/en/code-security/dependabot/dependabot-alerts/viewing-and-updating-dependabot-alerts).

#### [Screening actions for vulnerabilities in new or updated workflows](#screening-actions-for-vulnerabilities-in-new-or-updated-workflows)

When you open pull requests to update your workflows, it is good practice to use dependency review to understand the security impact of changes you've made to the actions you use. Dependency review helps you understand dependency changes and the security impact of these changes at every pull request. It provides an easily understandable visualization of dependency changes with a rich diff on the "Files Changed" tab of a pull request. Dependency review informs you of:

* Which dependencies were added, removed, or updated, along with the release dates
* How many projects use these components
* Vulnerability data for these dependencies

If any of the changes you made to your workflows are flagged as vulnerable, you can avoid adding them to your project or update them to a secure version.

For more information about dependency review, see [About dependency review](/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review).

The "dependency review action" refers to the specific action that can report on differences in a pull request within the GitHub Actions context. See [`dependency-review-action`](https://github.com/actions/dependency-review-action). You can use the dependency review action in your repository to enforce dependency reviews on your pull requests. The action scans for vulnerable versions of dependencies introduced by package version changes in pull requests, and warns you about the associated security vulnerabilities. This gives you better visibility of what's changing in a pull request, and helps prevent vulnerabilities being added to your repository. For more information, see [About dependency review](/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review#about-the-dependency-review-action).

### [Keeping the actions in your workflows secure and up to date](#keeping-the-actions-in-your-workflows-secure-and-up-to-date)

You can use Dependabot to ensure that references to actions and reusable workflows used in your repository are kept up to date. Actions are often updated with bug fixes and new features to make automated processes faster, safer, and more reliable. Dependabot takes the effort out of maintaining your dependencies as it does this automatically for you. For more information, see [Keeping your actions up to date with Dependabot](/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot) and [About Dependabot security updates](/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates).

The following features can automatically update the actions in your workflows.

* **Dependabot version updates** open pull requests to update actions to the latest version when a new version is released.
* **Dependabot security updates** open pull requests to update actions with reported vulnerabilities to the minimum patched version.

Note

* Dependabot only supports updates to GitHub Actions using the GitHub repository syntax, such as `actions/checkout@v5`. Dependabot will ignore actions or reusable workflows referenced locally (for example, `./.github/actions/foo.yml`).
* Docker Hub and GitHub Packages Container registry URLs are currently not supported. For example, references to Docker container actions using `docker://` syntax aren't supported.
* Dependabot supports both public and private repositories for GitHub Actions. For private registry configuration options, see "`git`" in [Dependabot options reference](/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file#git).

For information on how to configure Dependabot version updates, see [Configuring Dependabot version updates](/en/code-security/dependabot/dependabot-version-updates/configuring-dependabot-version-updates).

For information on how to configure Dependabot security updates, see [Configuring Dependabot security updates](/en/code-security/dependabot/dependabot-security-updates/configuring-dependabot-security-updates).

### [Protecting actions you've created](#protecting-actions-youve-created)

GitHub enables collaboration between people who publish and maintain actions and vulnerability reporters in order to promote secure coding. Repository security advisories allow maintainers of public repositories to privately discuss and fix a security vulnerability in a project. After collaborating on a fix, repository maintainers can publish the security advisory to publicly disclose the security vulnerability to the project's community. By publishing security advisories, repository maintainers make it easier for their community to update package dependencies and research the impact of the security vulnerabilities.

If you are someone who maintains an action that is used in other projects, you can use the following GitHub features to enhance the security of the actions you've published.

* Use the dependants view in the Dependency graph to see which projects depend on your code. If you receive a vulnerability report, this will give you an idea of who you need to communicate with about the vulnerability and how to fix it. For more information, see [Exploring the dependencies of a repository](/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exploring-the-dependencies-of-a-repository#dependents-view).
* Use repository security advisories to create a security advisory, privately collaborate to fix the vulnerability in a temporary private fork, and publish a security advisory to alert your community of the vulnerability once a patch is released. For more information, see [Configuring private vulnerability reporting for a repository](/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository) and [Creating a repository security advisory](/en/code-security/security-advisories/working-with-repository-security-advisories/creating-a-repository-security-advisory).

## Help and support

### Did you find what you needed?

Yes No

[Privacy policy](/en/site-policy/privacy-policies/github-privacy-statement)

### Help us make these docs great!

All GitHub docs are open source. See something that's wrong or unclear? Submit a pull request.

[Make a contribution](https://github.com/github/docs/blob/main/content/actions/reference/security/secure-use.md)

[Learn how to contribute](/contributing)

### Still need help?

[Ask the GitHub community](https://github.com/orgs/community/discussions)

[Contact support](https://support.github.com)

## Legal

* © 2025 GitHub, Inc.
* [Terms](/en/site-policy/github-terms/github-terms-of-service)
* [Privacy](/en/site-policy/privacy-policies/github-privacy-statement)
* [Status](https://www.githubstatus.com/)
* [Pricing](https://github.com/pricing)
* [Expert services](https://services.github.com)
* [Blog](https://github.blog)