package com.vdt.siem_system.test;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import org.apache.kafka.streams.state.KeyValueStore;

import java.util.Locale;
import java.util.Properties;


public class TestStream {
    public static void main(String[] args)  {
        String bootstrapServers = "localhost:9092,localhost:9093,localhost:9094";
        Properties properties = new Properties() {{
            put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
            put(StreamsConfig.APPLICATION_ID_CONFIG, "test-" + System.currentTimeMillis());
            put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
            put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        }};

//        StreamsBuilder builder = new StreamsBuilder();
//        KStream<String, String> kstream = builder.stream(
//                "first_topic",
//                Consumed.with(Serdes.String(), Serdes.String())
//        );
//        kstream.peek((key, value) -> System.out.println("Key: " + key + " Value:  " + value))
//                .filter((key, value) -> value.matches(".*\\d+.*"))
//                .mapValues(value -> value.toUpperCase())
//                .peek((key, value) -> System.out.println("New: " + key + " - " + value))
//                .to("second_topic", Produced.with(Serdes.String(), Serdes.String()));
//
//        KafkaStreams kafkaStreams = new KafkaStreams(builder.build(), properties);
//        Runtime.getRuntime().addShutdownHook(new Thread(kafkaStreams::close));
//        kafkaStreams.start();

        StreamsBuilder streamsBuilder = new StreamsBuilder();
        KTable<String, String> ktable = streamsBuilder.table(
                "first_topic",
                Materialized.<String, String, KeyValueStore<Bytes, byte[]>>as("kyable_store")
                        .withKeySerde(Serdes.String())
                        .withValueSerde(Serdes.String())
        );

        ktable.filter((key, value) -> value.contains("value"))
                .mapValues(value -> value.toUpperCase())
                .toStream()
                .peek((key, value) -> System.out.println("key: " + key + " value: " + value))
                .to("second_topic", Produced.with(Serdes.String(), Serdes.String()));

        KafkaStreams kafkaStreams = new KafkaStreams(streamsBuilder.build(), properties);
        kafkaStreams.start();
    }
}
