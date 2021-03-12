#arn:aws:secretsmanager:us-west-2:018923174646:secret:RdsRdsSecretA084F0A0-puzPLkAoCLW7-GRZ2jv hls-orchestration

AWS Stack for processing HLS data.

![Alt text](/docs/HLS_architecture.png)

### Requirements
Python>=3.7 \
tox \
aws-cli \
jq \
An IAM role with sufficient permissions for creating, destroying and modifying the relevant stack resources.

### Environment Settings
Environment variables are set in `environment.sh`. Copy `environment.sh.sample` to `environment.sh` and update the settings prior to running any commands.  The following variables can be overridden from the calling shell's environment
```
$ export HLS_STACKNAME=<Name of your stack>
$ export HLS_LAADS_TOKEN=<Token used for accessing the Laads Data>
$ export HLS_SENTINEL_OUTPUT_BUCKET_ROLE_ARN=<GCC Role for accessing output bucket>
```

### Synth
Display generated cloud formation template that will be used to deploy.
```
$ source ./environment.sh && tox -e dev -r -- synth
```

### Diff
Display a diff of the current deployment and any changes created.
```
$ source ./environment.sh && tox -e dev -r -- diff
```

### Deploy
Deploys current created stack.
```
$ source ./environment.sh && tox -e dev -r -- deploy
```

### Setup Logging Database
After `deploy` is run and the stack is created run
```
$ source ./environment.sh && ./scripts/setupdb.sh
```
To bootstrap the logging database.

### Development
For active stack development run
```
$ source ./environment.sh && tox -e dev -r -- version
```
This creates a local virtualenv in the directory `devenv`.  To use it for development
```
$ source devenv/bin/activate
```

### Tests
To run unit test for all included Lambda functions
```
tox -r
```
