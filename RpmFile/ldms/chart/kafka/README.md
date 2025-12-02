Files:
---

```console
kafka.kafka_bridge.yaml       Http bridge to kafka
kafka.kafka.yaml              Define k8s Custom Resource Definitions (CRDs) for KafkaNodePool and Kafka 
kafka.topic.nersc-ldms.yaml   Define k8s Custom Resource Definitions (CRDs) for KafkaTopic
README.md                     This file
setup_strimzi_kafka.bash*     script to install and configure strimzi kafka, and create the ldms topic
```

New Kafka does not use zookeeper
---
Instead of doing zookeeper for all the metadata, topics, and elections, over some other message bus,

Kfrat  uses the raft protocol and a special kafka topic __cluster_metadata with one partition and everyone reads from it other than the leader

One can follow the leader by reading the topic
```console
kubectl -n telem exec -it cluster-controller-0 -- /bin/bash bin/kafka-dump-log.sh --cluster-metadata-decoder --files /var/lib/kafka/data-0/kafka-log0/__cluster_metadata-0/00000000000000000000.log
```

All possible kfaft messages:  https://github.com/apache/kafka/tree/trunk/metadata/src/main/resources/common/metadata

There are leaders in kraft.
* a broker hands requests (like write & read to topic)
* a controller handles controller quorum and metadata log replication, and one is a leader (while the others are followers)
* But we can tell each node to do both broker + controller with some 'process.roles: combined' config param

google AI says: kafka kraft process.roles: combined
* "where a single node handles both broker and controller responsibilities, is suitable for development and testing scenarios, it is not recommended for production workloads."
