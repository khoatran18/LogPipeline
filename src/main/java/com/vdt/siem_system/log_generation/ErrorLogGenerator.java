package com.vdt.siem_system.log_generation;

import com.github.javafaker.Faker;
import com.vdt.siem_system.test.ProducerFactory;
import org.apache.kafka.clients.producer.Callback;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.apache.kafka.common.serialization.StringSerializer;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.Future;

// ------------------------------------------------------------------------------------------------------------
// (Demo) Nginx/Apache - Web Error Log Generator
// ------------------------------------------------------------------------------------------------------------
public class ErrorLogGenerator {

    private static final Faker faker = new Faker();
    private static final Random rand = new Random();

    private static final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
    static {
        dateFormat.setTimeZone(TimeZone.getTimeZone("GMT+7"));
    }

    //////////////////////////////////////// For Array of Values ////////////////////////////////////////

    static class ErrorProfile {
        int code;
        String reason;
        String level;

        public ErrorProfile(int code, String reason, String level) {
            this.code = code;
            this.reason = reason;
            this.level = level;
        }
    }

    private static final Map<String, List<ErrorProfile>> FILE_ERROR_MAP = new HashMap<>();
    static {
        FILE_ERROR_MAP.put("/var/www/html/index.html", List.of(
                new ErrorProfile(2, "No such file or directory", "[warn]"),
                new ErrorProfile(13, "Permission denied", "[error]"),
                new ErrorProfile(30, "Read-only file system", "[crit]")
        ));
        FILE_ERROR_MAP.put("/favicon.ico", List.of(
                new ErrorProfile(2, "No such file or directory", "[notice]"),
                new ErrorProfile(21, "Is a directory", "[warn]")
        ));
        FILE_ERROR_MAP.put("/etc/nginx/nginx.conf", List.of(
                new ErrorProfile(13, "Permission denied", "[error]"),
                new ErrorProfile(30, "Read-only file system", "[crit]"),
                new ErrorProfile(40, "Symbolic link loop", "[warn]")
        ));
        FILE_ERROR_MAP.put("/etc/passwd", List.of(
                new ErrorProfile(13, "Permission denied", "[alert]"),
                new ErrorProfile(32, "Broken pipe", "[crit]"),
                new ErrorProfile(110, "Connection timed out", "[error]")
        ));
        FILE_ERROR_MAP.put("/var/www/html/.env", List.of(
                new ErrorProfile(2, "No such file or directory", "[warn]"),
                new ErrorProfile(13, "Permission denied", "[error]"),
                new ErrorProfile(30, "Read-only file system", "[crit]")
        ));
        FILE_ERROR_MAP.put("/tmp/shell.php", List.of(
                new ErrorProfile(2, "No such file or directory", "[notice]"),
                new ErrorProfile(13, "Permission denied", "[error]"),
                new ErrorProfile(21, "Is a directory", "[warn]")
        ));
        FILE_ERROR_MAP.put("/usr/share/nginx/html/wp-config.php", List.of(
                new ErrorProfile(13, "Permission denied", "[crit]"),
                new ErrorProfile(30, "Read-only file system", "[alert]"),
                new ErrorProfile(40, "Symbolic link loop", "[warn]")
        ));
        FILE_ERROR_MAP.put("/.git/config", List.of(
                new ErrorProfile(13, "Permission denied", "[alert]"),
                new ErrorProfile(40, "Symbolic link loop", "[error]"),
                new ErrorProfile(2, "No such file or directory", "[warn]")
        ));
        FILE_ERROR_MAP.put("/opt/app/storage/logs/laravel.log", List.of(
                new ErrorProfile(30, "Read-only file system", "[crit]"),
                new ErrorProfile(110, "Connection timed out", "[error]"),
                new ErrorProfile(32, "Broken pipe", "[warn]")
        ));
        FILE_ERROR_MAP.put("/var/log/nginx/error.log", List.of(
                new ErrorProfile(30, "Read-only file system", "[crit]"),
                new ErrorProfile(13, "Permission denied", "[error]"),
                new ErrorProfile(2, "No such file or directory", "[warn]")
        ));
        FILE_ERROR_MAP.put("/backup/db.sqlite", List.of(
                new ErrorProfile(13, "Permission denied", "[alert]"),
                new ErrorProfile(30, "Read-only file system", "[crit]"),
                new ErrorProfile(110, "Connection timed out", "[warn]")
        ));
    }

    private static final Map<Integer, List<String>> ERROR_ACTIONS = new HashMap<>();
    static {
        ERROR_ACTIONS.put(2, List.of("open", "stat", "read", "unlink"));
        ERROR_ACTIONS.put(13, List.of("access", "read", "write", "execute"));
        ERROR_ACTIONS.put(21, List.of("open", "load", "list"));
        ERROR_ACTIONS.put(30, List.of("write", "flush", "sync"));
        ERROR_ACTIONS.put(32, List.of("send", "write", "pipe", "flush"));
        ERROR_ACTIONS.put(40, List.of("lookup", "access", "resolve"));
        ERROR_ACTIONS.put(110, List.of("connect", "send", "recv", "handshake"));
    }


    //////////////////////////////////////// For getting values ////////////////////////////////////////

    public String generateTimestamp() {
        long now = System.currentTimeMillis();
        // 5 hours ago
        long offset = rand.nextInt(5 * 60 * 60) * 1000;
        return dateFormat.format(new Date(now - offset));
    }

    public int generatePid() {
        return faker.number().numberBetween(1000, 9999);
    }

    public int generateTid() {
        return faker.number().numberBetween(0, 10);
    }

    public int generateRequestId() {
        return faker.number().numberBetween(1, 999);
    }

    public String generateIp() {
        return faker.internet().ipV4Address();
    }

    public String generateFilePath(Boolean isAttack) {
        List<String> files = new ArrayList<>(FILE_ERROR_MAP.keySet());
        if (isAttack) {
            files.removeIf(f -> f.contains("index.html") || f.contains(".css") || f.contains("favicon"));
        } else {
            files.removeIf(f -> f.contains("passwd") || f.contains(".env") || f.contains("wp-config"));
        }
        return faker.options().option(files.toArray(new String[0]));
    }

    public String generateErrorMessage(String filePath, ErrorProfile error) {
        List<String> actions = ERROR_ACTIONS.getOrDefault(error.code, List.of("access"));
        String action = faker.options().option(actions.toArray(new String[0]));

        switch(error.code) {

            // Connection timed out
            case 110:
                return String.format("%s() to \"%s\" failed (%d: %s)", action, filePath, error.code, error.reason);

            // Broken pipe
            case 32:
                return String.format("%s() \"%s\" aborted (%d: %s)", action, filePath, error.code, error.reason);

            // Link loop
            case 40:
                return String.format("%s() on \"%s\" failed (%d: %s)", action, filePath, error.code, error.reason);

            // Is a directory
            case 21:
                return String.format("%s() on directory \"%s\" failed (%d: %s)", action, filePath, error.code, error.reason);

            default:
                return String.format("%s() \"%s\" failed (%d: %s)", action, filePath, error.code, error.reason);
        }
    }


    //////////////////////////////////////// For generating logs //////////////////////////////////////

    public String generateLog() {
        String timestamp = generateTimestamp();
        int pid = generatePid();
        int tid = generateTid();
        int requestId = generateRequestId();
        String ip = generateIp();
        String filePath = generateFilePath(rand.nextBoolean());

        List<ErrorProfile> errors = FILE_ERROR_MAP.getOrDefault(filePath,
                List.of(new ErrorProfile(2, "No such file or directory", "[warn]")));
        ErrorProfile error = faker.options().option(errors.toArray(new ErrorProfile[0]));

        String message = generateErrorMessage(filePath, error);

        return String.format("%s %s %d#%d: *%d %s, client: %s",
                timestamp, error.level, pid, tid, requestId, message, ip);
    }

    public static void main(String[] args) {
        ErrorLogGenerator generator = new ErrorLogGenerator();
//        for (int i = 0; i < 50; i++) {
//            System.out.println(generator.generateLog());
//        }


        ProducerFactory factory = new ProducerFactory();
        try (Producer<String, String> producer = factory.createProducer(StringSerializer.class, StringSerializer.class)) {
            String topic = "error_log";
            // String key = "asa";
            producer.partitionsFor(topic);
            for(int i = 0; i < 100; i++) {
                String log = generator.generateLog();
                // String log = "2025/06/05 08:04:42 [crit] 4285#5: *119 flush() \"/etc/nginx/nginx.conf\" failed (30: Read-only file system), client: 245.156.153.219";
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
