<!-- Source: https://docs.github.com/actions/use-cases-and-examples/building-and-testing/building-and-testing-rust -->

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
* [Tutorials](/en/actions/tutorials "Tutorials")/
* [Build and test code](/en/actions/tutorials/build-and-test-code "Build and test code")/
* [Rust](/en/actions/tutorials/build-and-test-code/rust "Rust")

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
* [Tutorials](/en/actions/tutorials "Tutorials")/
* [Build and test code](/en/actions/tutorials/build-and-test-code "Build and test code")/
* [Rust](/en/actions/tutorials/build-and-test-code/rust "Rust")

# Building and testing Rust

Learn how to create a continuous integration (CI) workflow to build and test your Rust project.

## In this article

* [Introduction](#introduction)
* [Prerequisites](#prerequisites)
* [Using a Rust workflow template](#using-a-rust-workflow-template)
* [Specifying a Rust version](#specifying-a-rust-version)
* [Building and testing your code](#building-and-testing-your-code)
* [Publishing your package or library to crates.io](#publishing-your-package-or-library-to-cratesio)
* [Packaging workflow data as artifacts](#packaging-workflow-data-as-artifacts)

## [Introduction](#introduction)

This guide shows you how to build, test, and publish a Rust package.

GitHub-hosted runners have a tools cache with preinstalled software, which includes the dependencies for Rust. For a full list of up-to-date software and the preinstalled versions of Rust, see [GitHub-hosted runners](/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners#preinstalled-software).

## [Prerequisites](#prerequisites)

You should already be familiar with YAML syntax and how it's used with GitHub Actions. For more information, see [Workflow syntax for GitHub Actions](/en/actions/using-workflows/workflow-syntax-for-github-actions).

We recommend that you have a basic understanding of the Rust language. For more information, see [Getting started with Rust](https://www.rust-lang.org/learn).

## [Using a Rust workflow template](#using-a-rust-workflow-template)

To get started quickly, add a workflow template to the `.github/workflows` directory of your repository.

GitHub provides a Rust workflow template that should work for most basic Rust projects. The subsequent sections of this guide give examples of how you can customize this workflow template.

1. On GitHub, navigate to the main page of the repository.
2. Under your repository name, click  **Actions**.

   ![Screenshot of the tabs for the "github/docs" repository. The "Actions" tab is highlighted with an orange outline.](/assets/cb-12958/images/help/repository/actions-tab-global-nav-update.png)
3. If you already have a workflow in your repository, click **New workflow**.
4. The "Choose a workflow" page shows a selection of recommended workflow templates. Search for "Rust".
5. Filter the selection of workflows by clicking **Continuous integration**.
6. On the "Rust - by GitHub Actions" workflow, click **Configure**.

   ![Screenshot of the "Choose a workflow" page. The "Configure" button on the "Rust" workflow is highlighted with an orange outline.](/assets/cb-91615/images/help/actions/starter-workflow-rust.png)
7. Edit the workflow as required. For example, change the version of Rust.
8. Click **Commit changes**.

   The `rust.yml` workflow file is added to the `.github/workflows` directory of your repository.

## [Specifying a Rust version](#specifying-a-rust-version)

GitHub-hosted runners include a recent version of the Rust toolchain. You can use rustup to report on the version installed on a runner, override the version, and to install different toolchains. For more information, see [The rustup book](https://rust-lang.github.io/rustup/).

This example shows steps you could use to setup your runner environment to use the nightly build of rust and to report the version.

YAML

```
      - name: Temporarily modify the rust toolchain version
        run: rustup override set nightly
      - name: Output rust version for educational purposes
        run: rustup --version
```

```
      - name: Temporarily modify the rust toolchain version
        run: rustup override set nightly
      - name: Output rust version for educational purposes
        run: rustup --version
```

### [Caching dependencies](#caching-dependencies)

You can cache and restore dependencies using the Cache action. This example assumes that your repository contains a `Cargo.lock` file.

YAML

```
      - name: Cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
```

```
      - name: Cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
```

If you have custom requirements or need finer controls for caching, you should explore other configuration options for the [`cache` action](https://github.com/marketplace/actions/cache). For more information, see [Dependency caching reference](/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows).

## [Building and testing your code](#building-and-testing-your-code)

You can use the same commands that you use locally to build and test your code. This example workflow demonstrates how to use `cargo build` and `cargo test` in a job:

YAML

```
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        BUILD_TARGET: [release] # refers to a cargo profile
    outputs:
      release_built: ${{ steps.set-output.outputs.release_built }}
    steps:
      - uses: actions/checkout@v5
      - name: Build binaries in "${{ matrix.BUILD_TARGET }}" mode
        run: cargo build --profile ${{ matrix.BUILD_TARGET }}
      - name: Run tests in "${{ matrix.BUILD_TARGET }}" mode
        run: cargo test --profile ${{ matrix.BUILD_TARGET }}
```

```
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        BUILD_TARGET: [release] # refers to a cargo profile
    outputs:
      release_built: ${{ steps.set-output.outputs.release_built }}
    steps:
      - uses: actions/checkout@v5
      - name: Build binaries in "${{ matrix.BUILD_TARGET }}" mode
        run: cargo build --profile ${{ matrix.BUILD_TARGET }}
      - name: Run tests in "${{ matrix.BUILD_TARGET }}" mode
        run: cargo test --profile ${{ matrix.BUILD_TARGET }}
```

The `release` keyword used in this example corresponds to a cargo profile. You can use any [profile](https://doc.rust-lang.org/cargo/reference/profiles.html) you have defined in your `Cargo.toml` file.

## [Publishing your package or library to crates.io](#publishing-your-package-or-library-to-cratesio)

Once you have setup your workflow to build and test your code, you can use a secret to login to [crates.io](https://crates.io/) and publish your package.

YAML

```
      - name: Login into crates.io
        run: cargo login ${{ secrets.CRATES_IO }}
      - name: Build binaries in "release" mode
        run: cargo build -r
      - name: "Package for crates.io"
        run: cargo package # publishes a package as a tarball
      - name: "Publish to crates.io"
        run: cargo publish # publishes your crate as a library that can be added as a dependency
```

```
      - name: Login into crates.io
        run: cargo login ${{ secrets.CRATES_IO }}
      - name: Build binaries in "release" mode
        run: cargo build -r
      - name: "Package for crates.io"
        run: cargo package # publishes a package as a tarball
      - name: "Publish to crates.io"
        run: cargo publish # publishes your crate as a library that can be added as a dependency
```

If there are any errors building and packaging the crate, check the metadata in your manifest, `Cargo.toml` file, see [The Manifest Format](https://doc.rust-lang.org/cargo/reference/manifest.html). You should also check your `Cargo.lock` file, see [Cargo.toml vs Cargo.lock](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html).

## [Packaging workflow data as artifacts](#packaging-workflow-data-as-artifacts)

After a workflow completes, you can upload the resulting artifacts for analysis or to use in another workflow. You could add these example steps to the workflow to upload an application for use by another workflow.

YAML

```
      - name: Upload release artifact
        uses: actions/upload-artifact@v4
        with:
          name: <my-app>
          path: target/${{ matrix.BUILD_TARGET }}/<my-app>
```

```
      - name: Upload release artifact
        uses: actions/upload-artifact@v4
        with:
          name: <my-app>
          path: target/${{ matrix.BUILD_TARGET }}/<my-app>
```

To use the uploaded artifact in a different job, ensure your workflows have the right permissions for the repository, see [Use GITHUB\_TOKEN for authentication in workflows](/en/actions/security-for-github-actions/security-guides/automatic-token-authentication). You could use these example steps to download the app created in the previous workflow and publish it on GitHub.

YAML

```
      - uses: actions/checkout@v5
      - name: Download release artifact
        uses: actions/download-artifact@v5
        with:
          name: <my-app>
          path: ./<my-app>
      - name: Publish built binary to GitHub releases
      - run: |
          gh release create --generate-notes ./<my-app>/<my-project>#<my-app>
```

```
      - uses: actions/checkout@v5
      - name: Download release artifact
        uses: actions/download-artifact@v5
        with:
          name: <my-app>
          path: ./<my-app>
      - name: Publish built binary to GitHub releases
      - run: |
          gh release create --generate-notes ./<my-app>/<my-project>#<my-app>
```

## Help and support

### Did you find what you needed?

Yes No

[Privacy policy](/en/site-policy/privacy-policies/github-privacy-statement)

### Help us make these docs great!

All GitHub docs are open source. See something that's wrong or unclear? Submit a pull request.

[Make a contribution](https://github.com/github/docs/blob/main/content/actions/tutorials/build-and-test-code/rust.md)

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