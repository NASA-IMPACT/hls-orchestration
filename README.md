# HLS Orchestration

AWS Stack for processing HLS data.

![Alt text](/docs/HLS_architecture.png)

For more detailed data flow diagrams and architecture see
[architecture](/docs/architecture.md).

For more details about all of the HLS project's components see
[hls-project](https://github.com/nasa-impact/hls-project).

## Requirements

- Python>=3.9
- tox
- aws-cli
- jq
- An IAM role with sufficient permissions for creating, destroying, and
  modifying the relevant stack resources.

## Environment Settings

Environment variables are set in `environment.sh`.  Copy `environment.sh.sample`
to `environment.sh` and update the settings prior to running any commands.  The
following variables can be overridden from the calling shell's environment:

```plain
export HLS_STACKNAME=<Name of your stack>
export HLS_LAADS_TOKEN=<Token used for accessing the Laads Data>
export HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN=<GCC Role for accessing output bucket>
```

## Synth

Display generated cloud formation template that will be used to deploy.

```plain
source environment.sh && tox -e dev -r -- synth
```

## Diff

Display a diff of the current deployment and any changes created.

```plain
source environment.sh && tox -e dev -r -- diff
```

## Deploy

Deploy current version of stack:

```plain
source environment.sh && tox -e dev -r -- deploy
```

The repository is configured to create automatic deployments to the
`hls-development` stack when PRs are merged into the `dev` branch.  This
deployment uses
[Github Actions Environments](https://docs.github.com/en/actions/reference/environments)
to manage the environment configuration rather than the `environment.sh`.

Deployments to GCC have restrictions over creating VPCs and the types of AMIs
which can be utilized.  To deploy to GCC your shell will require the following
environment settings:

```plain
export GCC=true
export AWS_DEFAULT_REGION=us-west-2
export HLS_GCC_ACCOUNT=<The GCC account id>
export HLS_GCC_VPCID=<The vpc id provided by GCC administrators>
export HLS_GCC_BOUNDARY_ARN=<The boundary policy arn>
```

## Setup Logging Database

After `deploy` is run and the stack is created run:

```plain
source environment.sh && scripts/setupdb.sh
```

To bootstrap the logging database.

## Development

For active stack development run:

```plain
source environment.sh && tox -e dev -r -- version
```

This creates a local virtualenv in the directory `devenv`.  To use it for development:

```plain
source devenv/bin/activate
```

## Tests

To run unit test for all included Lambda functions

```plain
tox -r
```
