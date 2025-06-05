package com.vdt.siem_system.log_generation;

import com.github.javafaker.Faker;
import com.vdt.siem_system.test.ProducerFactory;
import org.apache.kafka.clients.producer.Callback;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.apache.kafka.common.serialization.StringSerializer;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Random;
import java.util.concurrent.Future;
import java.util.function.Supplier;

// ------------------------------------------------------------------------------------------------------------
// (Demo) Window - Security Log Generator (For Login, Logout, Change Password)
// ------------------------------------------------------------------------------------------------------------
public class WindowSecurityLogGenerator {

    private final static Faker faker = new Faker();
    private final static Random rand = new Random();
    private final static SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");

    private static List<Supplier<String>> eventGenerators;

    public WindowSecurityLogGenerator() {
        eventGenerators = List.of(
                this::generateEventId4624,
                this::generateEventId4625,
                this::generateEventId4634,
                this::generateEventId4723
        );
    }


    //////////////////////////////////////// For Array of Values ////////////////////////////////////////

    public enum WindowSecurityLogTemplate {
        EVENT_4624("""
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing"/>
    <EventID>4624</EventID>
    <Level>0</Level>
    <TimeCreated SystemTime="%s"/>
    <EventRecordID>%d</EventRecordID>
    <Channel>Security</Channel>
    <Computer>%s</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserSid">S-1-5-18</Data>
    <Data Name="SubjectUserName">SYSTEM</Data>
    <Data Name="TargetUserName">%s</Data>
    <Data Name="TargetDomainName">WORKGROUP</Data>
    <Data Name="LogonType">%d</Data>
    <Data Name="LogonProcessName">User32</Data>
    <Data Name="AuthenticationPackageName">Negotiate</Data>
    <Data Name="WorkstationName">%s</Data>
    <Data Name="IpAddress">%s</Data>
    <Data Name="IpPort">%d</Data>
    <Data Name="ProcessName">C:\\\\Windows\\\\System32\\\\winlogon.exe</Data>
  </EventData>
</Event>"""),

        EVENT_4625("""
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing"/>
    <EventID>4625</EventID>
    <Level>0</Level>
    <TimeCreated SystemTime="%s"/>
    <EventRecordID>%d</EventRecordID>
    <Channel>Security</Channel>
    <Computer>%s</Computer>
  </System>
  <EventData>
    <Data Name="TargetUserName">%s</Data>
    <Data Name="TargetDomainName">WORKGROUP</Data>
    <Data Name="Status">0xc000006a</Data>
    <Data Name="FailureReason">Unknown user name or bad password.</Data>
    <Data Name="IpAddress">%s</Data>
    <Data Name="IpPort">%d</Data>
  </EventData>
</Event>"""),

        EVENT_4634("""
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing"/>
    <EventID>4634</EventID>
    <Level>0</Level>
    <TimeCreated SystemTime="%s"/>
    <EventRecordID>%d</EventRecordID>
    <Channel>Security</Channel>
    <Computer>%s</Computer>
  </System>
  <EventData>
    <Data Name="TargetUserName">%s</Data>
    <Data Name="TargetDomainName">WORKGROUP</Data>
    <Data Name="LogonID">%s</Data>
  </EventData>
</Event>"""),

        EVENT_4723("""
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing"/>
    <EventID>4723</EventID>
    <Level>0</Level>
    <TimeCreated SystemTime="%s"/>
    <EventRecordID>%d</EventRecordID>
    <Channel>Security</Channel>
    <Computer>%s</Computer>
  </System>
  <EventData>
    <Data Name="TargetUserName">%s</Data>
    <Data Name="TargetDomainName">WORKGROUP</Data>
    <Data Name="SubjectUserName">SYSTEM</Data>
    <Data Name="SubjectDomainName">NT AUTHORITY</Data>
    <Data Name="SubjectUserSid">S-1-5-18</Data>
  </EventData>
</Event>""");

        private final String format;

        WindowSecurityLogTemplate(String format) {
            this.format = format;
        }

        public String getFormat() {
            return format;
        }

    }


    //////////////////////////////////////// For getting values ////////////////////////////////////////

    public String generateTimestamp() {
        long now = System.currentTimeMillis();
        // 5 hours ago
        long offset = rand.nextInt(5 * 60 * 60) * 1000;
        return dateFormat.format(new Date(now + offset));
    }

    public long generateEventRecordId() {
        return rand.nextInt(900000) + 100000;
    }

    public String generateUserName() {
        return faker.name().username();
    }

    public String generateHostName() {
        return faker.internet().domainName();
    }

    public String generateIp() {
        return faker.internet().ipV4Address();
    }

    public int generatePort() {
        return rand.nextInt(64511) + 1024;
    }

    public int generateLogonType() {
        return rand.nextBoolean() ? 2 : (rand.nextBoolean() ? 3 : 10);  // ưu tiên 2, 3, 10
    }

    public String generateLogonIdHex() {
        return String.format("0x%x", rand.nextInt(999999));
    }


    //////////////////////////////////////// For generating logs //////////////////////////////////////

    // Event 4624: An account was successfully logged on
    public String generateEventId4624() {
        String timestamp = generateTimestamp();
        String user = generateUserName();
        String host = generateHostName();
        int logonType = generateLogonType();
        long recordId = generateEventRecordId();
        String ip = generateIp();
        int port = generatePort();

        return String.format(WindowSecurityLogTemplate.EVENT_4624.getFormat(),
                timestamp,recordId,
                host, user, logonType, host, ip, port
        );
    }


    // Event 4625: An account failed to log on
    public String generateEventId4625() {
        String timestamp = generateTimestamp();
        String user = generateUserName();
        String host = generateHostName();
        long recordId = generateEventRecordId();
        String ip = generateIp();
        int port = generatePort();

        return String.format(WindowSecurityLogTemplate.EVENT_4625.getFormat(),
        timestamp, recordId, host, user, ip, port);
    }

    // Event 4634: An account was logged off (session ended)
    public String generateEventId4634() {
        String timestamp = generateTimestamp();
        String user = generateUserName();
        String host = generateHostName();
        long recordId = generateEventRecordId();
        String logonIdHex = generateLogonIdHex();

        return String.format(WindowSecurityLogTemplate.EVENT_4634.getFormat(),
                timestamp, recordId, host, user, logonIdHex
        );
    }

    // Event 4723: An attempt was made to change an account’s password
    public String generateEventId4723() {
        String timestamp = generateTimestamp();
        String user = generateUserName();
        String host = generateHostName();
        long recordId = generateEventRecordId();

        return String.format(WindowSecurityLogTemplate.EVENT_4723.getFormat(),
                timestamp,
                recordId,
                host, user
        );
    }

    public String generateLog() {
        return eventGenerators.get(rand.nextInt(eventGenerators.size())).get();
    }



    public static void main(String[] args) {
        WindowSecurityLogGenerator generator = new WindowSecurityLogGenerator();

//        for(int i = 0; i < 20; i++) {
//            System.out.println(generator.generateLog() + "\n");
//        }

        ProducerFactory factory = new ProducerFactory();
        try (Producer<String, String> producer = factory.createProducer(StringSerializer.class, StringSerializer.class)) {
            String topic = "window_log";
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
