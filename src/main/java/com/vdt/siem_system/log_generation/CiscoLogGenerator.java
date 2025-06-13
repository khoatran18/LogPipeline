package com.vdt.siem_system.log_generation;

import com.github.javafaker.Faker;
import com.vdt.siem_system.test.ProducerFactory;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.Objects;
import java.util.Random;
import java.util.concurrent.Future;

// ------------------------------------------------------------------------------------------------------------
// (Demo) Cisco ASA - Connection Log Generator (Severity: 4-warning, 6-informational, 7-debugging)
// ------------------------------------------------------------------------------------------------------------
public class CiscoLogGenerator {

    private final Faker faker = new Faker();
    private final Random rand = new Random();

    //////////////////////////////////////// For Array of Values ////////////////////////////////////////

    private final String[] ZONES = {"inside", "outside"};
    private final String[] PROTOCOLS = {"TCP", "UDP", "ICMP"};
    private final String[] DEBUGLOGS = {
            "%ASA-7-302021: Teardown TCP connection for trace test",
            "%ASA-7-710003: TCP access permitted",
            "%ASA-7-305012: NAT resolved from internal to public IP",
            "%ASA-7-710005: UDP access denied by ACL",
            "%ASA-7-302015: ICMP connection built for echo request",
            "%ASA-7-302016: ICMP connection teardown",
            "%ASA-7-710006: ICMP echo request permitted",
            "%ASA-7-609001: TCP state machine initialized",
            "%ASA-7-609002: TCP handshake completed",
            "%ASA-7-110001: Routing via outside interface",
            "%ASA-7-110002: No route to host",
            "%ASA-7-610001: Security policy check passed",
            "%ASA-7-610002: Packet dropped: failed inspection"
    };

    private static final String[] threatIPs = {"1.14.155.39",
            "1.15.148.9",
            "1.15.80.32",
            "1.162.225.116",
            "1.162.235.166",
            "1.180.189.210",
            "1.180.97.138",
            "1.183.3.58",
            "1.189.209.19",
            "1.189.39.138",
            "1.193.163.2",
            "1.194.238.148",
            "1.197.78.123",
            "1.202.223.2",
            "1.202.8.212",
            "1.212.225.99"};

    enum AsaEventType {
        CONNECTION_BUILD("302013", 6),
        CONNECTION_TEARDOWN("302014", 6),
        CONNECTION_DENIED("106023", 4),
        NAT_TRANSLATION("305011", 6),
        ICMP_CONNECTION("302015", 6);

        String messageId;
        int severity;

        AsaEventType(String messageId, int severity) {
            this.messageId = messageId;
            this.severity = severity;
        }
    }

    //////////////////////////////////////// For getting values ////////////////////////////////////////

//    public String getIp(String zone) {
//        return zone.equals("outside")
//                ? faker.internet().ipV4Address()
//                : "192.168." + rand.nextInt(256) + "." + rand.nextInt(256);
//    }

    public String getIp(String zone) {
        if (zone.equals("outside")) {
            if (rand.nextInt(2) == 0) {
                return threatIPs[rand.nextInt(threatIPs.length)];
            }
            return faker.internet().ipV4Address();
        }
        return "192.168." + rand.nextInt(256) + "." + rand.nextInt(256);
    }

    public int getPort() {
        return faker.number().numberBetween(1, 65535);
    }

    public String getZone() {
        return ZONES[rand.nextInt(ZONES.length)];
    }

    public String getProtocol() {
        return PROTOCOLS[rand.nextInt(PROTOCOLS.length)];
    }

    public String getDirection(String src, String dst) {
        if (src.equals("outside") && dst.equals("inside")) return "inbound";
        if (src.equals("inside") && dst.equals("outside")) return "outbound";
        return rand.nextBoolean() ? "inbound" : "outbound";
    }


    //////////////////////////////////////// For generating logs //////////////////////////////////////

    public String generateLog() {
        AsaEventType[] events = AsaEventType.values();
        AsaEventType event = events[rand.nextInt(events.length)];
        //nAsaEventType event = events[0];

        // % cho log debug
        if (rand.nextInt(5) == 0) {
            return DEBUGLOGS[rand.nextInt(DEBUGLOGS.length)];
        }

        String header = String.format("%%ASA-%d-%s", event.severity, event.messageId);
        String srcZone = getZone();
        String dstZone = getZone();
        String direction = getDirection(srcZone, dstZone);

        String srcIP = getIp(srcZone);
        String dstIP = getIp(dstZone);
        int srcPort = getPort();
        int dstPort = getPort();

        String protocol = getProtocol();
        int connId = 10000 + rand.nextInt(90000);
        boolean useNat = srcZone.equals("inside") && dstZone.equals("outside") && !protocol.equals("ICMP") && rand.nextBoolean();
        String natIp = getIp("outside");
        int natPort = getPort();

        switch (event) {
            case CONNECTION_BUILD:
                if (Objects.equals(protocol, "ICMP")) {
                    return "%ASA-7-999999: Debug trace — NAT translation skipped for ICMP";
                }
                return useNat
                        ? String.format("%s: Built %s %s connection %d for %s:%s/%d (%s/%d) to %s:%s/%d",
                            header, direction, protocol, connId,
                            srcZone, srcIP, srcPort, natIp, natPort, dstZone, dstIP, dstPort)
                        : String.format("%s: Built %s %s connection %d for %s:%s/%d to %s:%s/%d",
                            header, direction, protocol, connId,
                            srcZone, srcIP, srcPort, dstZone, dstIP, dstPort);

            case CONNECTION_TEARDOWN:
                return String.format("%s: Teardown %s connection %d for %s:%s/%d to %s:%s/%d duration 0:%02d:%02d bytes %d",
                            header, protocol, connId,
                            srcZone, srcIP, srcPort, dstZone, dstIP, dstPort, rand.nextInt(60), rand.nextInt(60),
                            faker.number().numberBetween(500, 20000));

            case CONNECTION_DENIED:
                /////////////////////////////// Kafka: " instead of \" //////////////////////////////////////////////
                return String.format("%s: Deny %s src %s:%s/%d dst %s:%s/%d by access-group \"outside_access_in\"",
                            header, protocol, srcZone, srcIP, srcPort, dstZone, dstIP, dstPort);

            case NAT_TRANSLATION:
                if (protocol.equals("ICMP")) {
                    return "%ASA-7-999999: Debug trace — NAT translation skipped for ICMP";
                }
                return String.format("%s: Built dynamic %s translation from %s:%s/%d to %s:%s/%d",
                            header, protocol, srcZone, srcIP, srcPort, dstZone, dstIP, dstPort);

            case ICMP_CONNECTION:
                return String.format("%s: Built ICMP connection for faddr %s/0 gaddr %s/0 laddr %s/0",
                            header, dstIP, natIp, srcIP);

            default:
                return header + "unknown event: " + event.messageId + " " + event.severity;
        }

    }

    public static void main(String[] args) {
        CiscoLogGenerator generator = new CiscoLogGenerator();

//        for(int i = 0; i < 50; i++) {
//            System.out.println(generator.generateLog());
//        }

        ProducerFactory factory = new ProducerFactory();
        try (Producer<String, String> producer = factory.createProducer(StringSerializer.class, StringSerializer.class)) {
            String topic = "cisco_log";
            producer.partitionsFor(topic);
            for(int i = 0; i < 100; i++) {
                String log = generator.generateLog();
                System.out.println(log);
                ProducerRecord<String, String> record = new ProducerRecord<>(topic, log);

                Callback callback = (recordMetadata, e) -> {
                    System.out.println(recordMetadata.offset() + " " + recordMetadata.partition() + " " + recordMetadata.timestamp());
                };
                Future<RecordMetadata> result = producer.send(record, callback);
            }
        }



    }

}
