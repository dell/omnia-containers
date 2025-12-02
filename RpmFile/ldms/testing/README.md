Files
---

```console
ldmsauth.conf         Ovis Auth Secret. 
ldmsd_agg.bash        Start Agg ldmsd, which listens to the Producer ldmsd.
ldmsd_agg.conf        Config for Agg ldmsd.
ldmsd_producer.bash   Start Producer ldmsd, which runs sampler plugins
ldmsd_producer.conf   Config for Producer ldmsd.
ldms_ls.agg.bash      Talk to Agg ldmsd.
ldms_ls.producer.bash Talk to Producer ldmsd.
```

Run
---

NOTE: The path to the auth file must be absolute

```console
# Start the producer
./ldmsd_producer.bash

# Talk to the producer
./ldms_ls.producer.bash

# Start the aggregator
./ldmsd_agg.bash

# Talk to the aggregator
./ldms_ls.agg.bash
```


Tmux
---

# Start tmux. Opens 3 panes
1. shell
2. sampler ldmsd: /ldms_sampler.bash
3. agg ldmsd:     /ldmsd_agg.bash
User is place in shell

```console
./tmux.bash
```

# NOTE: tmux cheat sheet

```
Moving between panes
  ctrl+b ArrowUp
  ctrl+b ArrowDown
 Scrolling in a pane
  ctrl+b [ Arrow[Up|Down]
Maximize/UnMaximize Pane
  ctrl+b z
Exit tmux
  ctrl+b d
```

# Interact with sampler ldmsd as a client
```
./ldms_sampler_ls.bash
./ldms_sampler_ls.bash -l
./ldms_sampler_ls.bash -v
./ldms_sampler_ls.bash -d
./ldms_sampler_stats.bash
```
