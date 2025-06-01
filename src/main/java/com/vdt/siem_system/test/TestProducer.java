package com.vdt.siem_system.test;

import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.record.Record;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.Properties;
import java.util.concurrent.Future;

public class TestProducer {
    public static void main(String[] args) throws Exception {
        String bootstrapServers = "localhost:9092,localhost:9093,localhost:9094";
        Properties properties = new Properties(){{
            put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
            put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
            put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
            put(ProducerConfig.ACKS_CONFIG, "1");
        }};

        try (Producer<String, String> producer = new KafkaProducer<>(properties)) {
            for (int i = 0; i < 10; i++) {
                final String key = "my key";
                final String value = "my value " + i;
                final String topic = "first_topic";
                producer.partitionsFor(topic);
                ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, value);

                Callback callback = (recordMetadata, e) ->
                        System.out.println("topic: " + recordMetadata.topic() +
                                " \npartition: " + recordMetadata.partition() +
                                " \noffset: " + recordMetadata.offset());
                Future<RecordMetadata> result =  producer.send(record, callback);
            }

            producer.flush();
        };


    }

}
