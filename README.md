# hls-orchestration

Orchestration for creating a stack to process HLS

### Regular Install
Installs cdk using yarn.
Installs python requirements and hls-orchestration package in a local virtual environment (venv)
```
$ make install
```

### Environment
The following Environment variables must be set
```
$ export STACKNAME=<Name of your stack>
$ export LAADS_TOKEN=<Token used for accessing the Laads Data>
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
