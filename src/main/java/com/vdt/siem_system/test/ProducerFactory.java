package com.vdt.siem_system.test;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.Serializer;

import java.util.Properties;

public class ProducerFactory {

    private final String bootstrapServers = "localhost:9092,localhost:9093,localhost:9094";

    public <K, V> Producer<K, V> createProducer(
            Class<? extends Serializer<K>> keySerializerClass,
            Class<? extends Serializer<V>> valueSerializerClass
    ) {
        Properties properties = new Properties();
        properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, this.bootstrapServers);
        properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, keySerializerClass);
        properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, valueSerializerClass);
        properties.put(ProducerConfig.ACKS_CONFIG, "1");


        return new KafkaProducer<>(properties);
    }
}
