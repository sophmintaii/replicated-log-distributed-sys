# Replicated log
**A task for the Distributed Systems course on the Data Engineering certification**


## Get the code
```bash
git clone git@github.com:sophmintaii/replicated-log-distributed-sys.git
cd replicated-log-distributed-sys
```


## Iteration 0: just an echo server

### Run the setup/demo
```bash
git checkout iteration-0
chmod +x setup.sh
./setup.sh
```

The client sends two messages to an echo server and prints the replies. Server output is in `server.log`.

## Iteration 1


### Run the demo
Start Docker first (through colima or another tool), then:

```bash
chmod +x demo.sh
./demo.sh
```

It runs the harness test first, then starts the master and two secondaries, sends one message, prints the messages on each node, then shuts everything back down.
