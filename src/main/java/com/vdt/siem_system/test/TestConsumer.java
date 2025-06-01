package com.vdt.siem_system.test;

import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.StringDeserializer;

import java.time.Duration;
import java.util.List;
import java.util.Properties;

public class TestConsumer {
    public static void main(String[] args) {
        final String bootstrapServers = "localhost:9092,localhost:9093,localhost:9094";
        final String consumerGroupId = "my_group_id_test";
        Properties properties = new Properties(){{
            put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
            put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
            put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
            put(ConsumerConfig.GROUP_ID_CONFIG, consumerGroupId);
            put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
            // Lưu ý ////////////////////////
            put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        }};

        Consumer<String, String> consumer = new KafkaConsumer<>(properties);
        consumer.subscribe(List.of("asa_log"));

        try {
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
                for (ConsumerRecord<String, String> record : records) {
                    System.out.printf("Key: %s, Value: %s, Partition: %d, Offset: %d%n",
                            record.key(), record.value(), record.partition(), record.offset());
                }
            }
        } finally {
            consumer.close();
        }

    }
}
