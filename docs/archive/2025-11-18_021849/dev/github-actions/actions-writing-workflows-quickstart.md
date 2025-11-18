<!-- Source: https://docs.github.com/actions/writing-workflows/quickstart -->

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
* [Get started](/en/actions/get-started "Get started")/
* [Quickstart](/en/actions/get-started/quickstart "Quickstart")

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
* [Get started](/en/actions/get-started "Get started")/
* [Quickstart](/en/actions/get-started/quickstart "Quickstart")

# Quickstart for GitHub Actions

Try out the core features of GitHub Actions in minutes.

## In this article

* [Introduction](#introduction)
* [Using workflow templates](#using-workflow-templates)
* [Prerequisites](#prerequisites)
* [Creating your first workflow](#creating-your-first-workflow)
* [Viewing your workflow results](#viewing-your-workflow-results)
* [Next steps](#next-steps)

## [Introduction](#introduction)

GitHub Actions is a continuous integration and continuous delivery (CI/CD) platform that allows you to automate your build, test, and deployment pipeline. You can create workflows that run tests whenever you push a change to your repository, or that deploy merged pull requests to production.

This quickstart guide shows you how to use the user interface of GitHub to add a workflow that demonstrates some of the essential features of GitHub Actions.

To get started with preconfigured workflows, browse through the list of templates in the [actions/starter-workflows](https://github.com/actions/starter-workflows) repository. For more information, see [Using workflow templates](/en/actions/writing-workflows/using-starter-workflows).

For an overview of GitHub Actions workflows, see [Workflows](/en/actions/using-workflows/about-workflows). If you want to learn about the various components that make up GitHub Actions, see [Understanding GitHub Actions](/en/actions/learn-github-actions/understanding-github-actions).

## [Using workflow templates](#using-workflow-templates)

GitHub provides preconfigured workflow templates that you can use as-is or customize to create your own workflow. GitHub analyzes your code and shows you workflow templates that might be useful for your repository. For example, if your repository contains Node.js code, you'll see suggestions for Node.js projects.

These workflow templates are designed to help you get up and running quickly, offering a range of configurations such as:

* CI: [Continuous Integration workflows](https://github.com/actions/starter-workflows/tree/main/ci)
* Deployments: [Deployment workflows](https://github.com/actions/starter-workflows/tree/main/deployments)
* Automation: [Automating workflows](https://github.com/actions/starter-workflows/tree/main/automation)
* Code Scanning: [Code Scanning workflows](https://github.com/actions/starter-workflows/tree/main/code-scanning)
* Pages: [Pages workflows](https://github.com/actions/starter-workflows/tree/main/pages)

Use these workflows as a starting place to build your custom workflow or use them as-is. You can browse the full list of workflow templates in the [actions/starter-workflows](https://github.com/actions/starter-workflows) repository.

## [Prerequisites](#prerequisites)

This guide assumes that:

* You have at least a basic knowledge of how to use GitHub. If you don't, you'll find it helpful to read some of the articles in the documentation for repositories and pull requests first. For example, see [Quickstart for repositories](/en/repositories/creating-and-managing-repositories/quickstart-for-repositories), [About branches](/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches), and [About pull requests](/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).
* You have a repository on GitHub where you can add files.
* You have access to GitHub Actions.

  Note

  If the  **Actions** tab is not displayed under the name of your repository on GitHub, it may be because Actions is disabled for the repository. For more information, see [Managing GitHub Actions settings for a repository](/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

## [Creating your first workflow](#creating-your-first-workflow)

1. In your repository on GitHub, create a workflow file called `github-actions-demo.yml` in the `.github/workflows` directory. To do this:

   * If the `.github/workflows` directory already exists, navigate to that directory on GitHub, click **Add file**, then click **Create new file**, and name the file `github-actions-demo.yml`.
   * If your repository doesn't have a `.github/workflows` directory, go to the main page of the repository on GitHub, click **Add file**, then click **Create new file**, and name the file `.github/workflows/github-actions-demo.yml`. This creates the `.github` and `workflows` directories and the `github-actions-demo.yml` file in a single step.

   Note

   For GitHub to discover any GitHub Actions workflows in your repository, you must save the workflow files in a directory called `.github/workflows`.

   You can give the workflow file any name you like, but you must use `.yml` or `.yaml` as the file name extension. YAML is a markup language that's commonly used for configuration files.
2. Copy the following YAML contents into the `github-actions-demo.yml` file:

   YAML

   ```
   name: GitHub Actions Demo
   run-name: ${{ github.actor }} is testing out GitHub Actions 🚀
   on: [push]
   jobs:
     Explore-GitHub-Actions:
       runs-on: ubuntu-latest
       steps:
         - run: echo "🎉 The job was automatically triggered by a ${{ github.event_name }} event."
         - run: echo "🐧 This job is now running on a ${{ runner.os }} server hosted by GitHub!"
         - run: echo "🔎 The name of your branch is ${{ github.ref }} and your repository is ${{ github.repository }}."
         - name: Check out repository code
           uses: actions/checkout@v5
         - run: echo "💡 The ${{ github.repository }} repository has been cloned to the runner."
         - run: echo "🖥️ The workflow is now ready to test your code on the runner."
         - name: List files in the repository
           run: |
             ls ${{ github.workspace }}
         - run: echo "🍏 This job's status is ${{ job.status }}."
   ```

   ```
   name: GitHub Actions Demo
   run-name: ${{ github.actor }} is testing out GitHub Actions 🚀
   on: [push]
   jobs:
     Explore-GitHub-Actions:
       runs-on: ubuntu-latest
       steps:
         - run: echo "🎉 The job was automatically triggered by a ${{ github.event_name }} event."
         - run: echo "🐧 This job is now running on a ${{ runner.os }} server hosted by GitHub!"
         - run: echo "🔎 The name of your branch is ${{ github.ref }} and your repository is ${{ github.repository }}."
         - name: Check out repository code
           uses: actions/checkout@v5
         - run: echo "💡 The ${{ github.repository }} repository has been cloned to the runner."
         - run: echo "🖥️ The workflow is now ready to test your code on the runner."
         - name: List files in the repository
           run: |
             ls ${{ github.workspace }}
         - run: echo "🍏 This job's status is ${{ job.status }}."
   ```

   At this stage you don't need to understand the details of this workflow. For now, you can just copy and paste the contents into the file. After completing this quickstart guide, you can learn about the syntax of workflow files in [Workflows](/en/actions/using-workflows/about-workflows#understanding-the-workflow-file), and for an explanation of GitHub Actions contexts, such as `${{ github.actor }}` and `${{ github.event_name }}`, see [Contexts reference](/en/actions/learn-github-actions/contexts).
3. Click **Commit changes**.
4. In the "Propose changes" dialog, select either the option to commit to the default branch or the option to create a new branch and start a pull request. Then click **Commit changes** or **Propose changes**.

   ![Screenshot of the "Propose changes" dialog with the areas mentioned highlighted with an orange outline.](/assets/cb-71777/images/help/repository/actions-quickstart-commit-new-file.png)

Committing the workflow file to a branch in your repository triggers the `push` event and runs your workflow.

If you chose to start a pull request, you can continue and create the pull request, but this is not necessary for the purposes of this quickstart because the commit has still been made to a branch and will trigger the new workflow.

## [Viewing your workflow results](#viewing-your-workflow-results)

1. On GitHub, navigate to the main page of the repository.
2. Under your repository name, click  **Actions**.

   ![Screenshot of the tabs for the "github/docs" repository. The "Actions" tab is highlighted with an orange outline.](/assets/cb-12958/images/help/repository/actions-tab-global-nav-update.png)
3. In the left sidebar, click the workflow you want to display, in this example "GitHub Actions Demo."

   ![Screenshot of the "Actions" page. The name of the example workflow, "GitHub Actions Demo", is highlighted by a dark orange outline.](/assets/cb-64036/images/help/repository/actions-quickstart-workflow-sidebar.png)
4. From the list of workflow runs, click the name of the run you want to see, in this example "USERNAME is testing out GitHub Actions."
5. In the left sidebar of the workflow run page, under **Jobs**, click the **Explore-GitHub-Actions** job.

   ![Screenshot of the "Workflow run" page. In the left sidebar, the "Explore-GitHub-Actions" job is highlighted with a dark orange outline.](/assets/cb-53820/images/help/repository/actions-quickstart-job.png)
6. The log shows you how each of the steps was processed. Expand any of the steps to view its details.

   ![Screenshot of steps run by the workflow.](/assets/cb-95207/images/help/repository/actions-quickstart-logs.png)

   For example, you can see the list of files in your repository:

   ![Screenshot of the "List files in the repository" step expanded to show the log output. The output for the step is highlighted with an orange outline.](/assets/cb-53977/images/help/repository/actions-quickstart-log-detail.png)

The example workflow you just added is triggered each time code is pushed to the branch, and shows you how GitHub Actions can work with the contents of your repository. For an in-depth tutorial, see [Understanding GitHub Actions](/en/actions/learn-github-actions/understanding-github-actions).

## [Next steps](#next-steps)

GitHub Actions can help you automate nearly every aspect of your application development processes. Ready to get started? Here are some helpful resources for taking your next steps with GitHub Actions:

* To create a GitHub Actions workflow, see [Using workflow templates](/en/actions/learn-github-actions/using-starter-workflows).
* For continuous integration (CI) workflows, see [Building and testing your code](/en/actions/automating-builds-and-tests).
* For building and publishing packages, see [Publishing packages](/en/actions/publishing-packages).
* For deploying projects, see [Deploying to third-party platforms](/en/actions/deployment).
* For automating tasks and processes on GitHub, see [Managing your work with GitHub Actions](/en/actions/managing-issues-and-pull-requests).
* For examples that demonstrate more complex features of GitHub Actions, see [Managing your work with GitHub Actions](/en/actions/examples). These detailed examples explain how to test your code on a runner, access the GitHub CLI, and use advanced features such as concurrency and test matrices.
* To certify your proficiency in automating workflows and accelerating development with GitHub Actions, earn a GitHub Actions certificate with GitHub Certifications. For more information, see [About GitHub Certifications](/en/get-started/showcase-your-expertise-with-github-certifications/about-github-certifications).

## Help and support

### Did you find what you needed?

Yes No

[Privacy policy](/en/site-policy/privacy-policies/github-privacy-statement)

### Help us make these docs great!

All GitHub docs are open source. See something that's wrong or unclear? Submit a pull request.

[Make a contribution](https://github.com/github/docs/blob/main/content/actions/get-started/quickstart.md)

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