# hls-orchestration

Orchestration for creating a stack to process HLS

### Regular Install
Installs cdk using yarn.
Installs python requirements and hls-orchestration package in a local virtual environment (venv)
```
$ make install
```

### Environment
Environment variables are set in env.sh. A sample env.sh is at env.sh.sample, you must copy this file 
to env.sh before running make synth, make diff, or make deploy
The following variables can be overridden from the calling shell's environment
```
$ export HLS_STACKNAME=<Name of your stack>
$ export HLS_LAADS_TOKEN=<Token used for accessing the Laads Data>
$ export HLS_SENTINEL_BUCKET_ROLE_ARN=<GCC Role for accessing output bucket>
```

### Synth
Display generated cloud formation template that will be used to deploy.
```
$ make synth
```

### Diff
Display a diff of the current deployment and any changes created.
```
$ make synth
```

### Deploy
Deploys current created stack.
```
$ make deploy
```

### Cleanup
Cleans out all files and prereqs created in the installation process.
You will need to reinstall after running this.
```
$ make clean
```
