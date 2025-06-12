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
// (Demo) Nginx/Apache - Web Access Log Generator (Text Format)
// ------------------------------------------------------------------------------------------------------------
public class AccessLogGenerator {

    private static final Faker faker = new Faker();
    private static final Random rand = new Random();

    // Timastamp format
    private static final SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy:HH:mm:ss Z", Locale.ENGLISH);
    static {
        dateFormat.setTimeZone(TimeZone.getTimeZone("GMT+7"));
    }


    //////////////////////////////////////// For Array of Values ////////////////////////////////////////

    private static final String[] METHODS = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "CHECK"};
    private static final String[] PROTOCOLS = {"HTTP/1.0", "HTTP/1.1", "HTTP/2.0"};
    private static final String[] URLS = {
            "/index.html", "/login", "/logout", "/admin", "/dashboard", "/api/v1/data",
            "/search?q=test", "/robots.txt", "/favicon.ico", "/wp-login.php", "/.env",
            "/css/style.css", "/js/app.js", "/img/logo.png", "/register", "/reset-password",
            "/blog/post-123", "/admin/settings", "/api/v2/users", "/upload", "/download/file.zip"
    };

    private static final Map<String, String[]> METHOD_STATUS_MAP = new HashMap<>();
    static {
        METHOD_STATUS_MAP.put("GET",     new String[]{"200", "301", "302", "403", "404", "500"});
        METHOD_STATUS_MAP.put("POST",    new String[]{"200", "201", "400", "403", "422", "500"});
        METHOD_STATUS_MAP.put("PUT",     new String[]{"200", "201", "204", "400", "403", "409"});
        METHOD_STATUS_MAP.put("DELETE",  new String[]{"200", "202", "204", "403", "404"});
        METHOD_STATUS_MAP.put("HEAD",    new String[]{"200", "403", "404", "500"});
        METHOD_STATUS_MAP.put("OPTIONS", new String[]{"204", "200", "403", "501"});
        METHOD_STATUS_MAP.put("PATCH",   new String[]{"200", "204", "400", "422"});
    }

    private static final String[] NORMAL_REFERRES = {
            "-", "https://google.com", "https://facebook.com", "https://youtube.com",
            "https://github.com", "https://example.com/article", "https://bing.com"
    };
    private static final String[] SUSPICIOUS_REFERRES = {
            "-", "http://evil.com/spam", "http://malware.biz/track", "http://phish.site/fake"
    };
    private static final String[] NORMAL_USER_AGENTS = {
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Firefox/113.0",
            "Mozilla/5.0 (Linux; Android 11) Mobile Safari/537.36"
    };
    private static final String[] SUSPICIOUS_USER_AGENTS = {
            "curl/7.68.0",
            "sqlmap/1.6.12",
            "python-requests/2.31",
            "Wget/1.20.3",
            "dirb/2.22",
            "Mozilla/5.0 evil-bot/0.1"
    };


    //////////////////////////////////////// For getting values ////////////////////////////////////////

    public String generateIp() {
        return faker.internet().ipV4Address();
        // return "2.119.161.42";
    }

    public String generateTimestamp() {
        long now = System.currentTimeMillis();
        // 5 hours ago
        long offset = rand.nextInt(5 * 60 * 60) * 1000;
        return "[" + dateFormat.format(new Date(now - offset)) + "]";
    }

    public String generateMethod() {
        return faker.options().option(METHODS);
    }

    public String generateUrl() {
        return URLS[rand.nextInt(URLS.length)];
    }

    public String generateProtocol() {
        return PROTOCOLS[rand.nextInt(PROTOCOLS.length)];
    }

    public String generateStatusCodeForMethod(String method) {
        String[] status = METHOD_STATUS_MAP.getOrDefault(method, new String[] {"200"});
        return status[rand.nextInt(status.length)];
    }

    public int generateSize() {
        return faker.number().numberBetween(100, 10000);
    }

    public String generateReferrer(Boolean isAttack) {
        return isAttack
                ? SUSPICIOUS_REFERRES[rand.nextInt(SUSPICIOUS_REFERRES.length)]
                : NORMAL_REFERRES[rand.nextInt(NORMAL_REFERRES.length)];
    }

    public String generateUserAgent(Boolean isAttack) {
        return  isAttack
                ? SUSPICIOUS_USER_AGENTS[rand.nextInt(SUSPICIOUS_USER_AGENTS.length)]
                : faker.internet().userAgentAny();
                // : NORMAL_USER_AGENTS[rand.nextInt(NORMAL_USER_AGENTS.length)];
    }


    //////////////////////////////////////// For generating logs //////////////////////////////////////

    public String generateLog() {
        String ip = generateIp();
        String timestamp = generateTimestamp();
        String method = generateMethod();
        String url = generateUrl();
        String protocol = generateProtocol();
        String status = generateStatusCodeForMethod(method);
        int size = generateSize();
        String userAgent = generateUserAgent(rand.nextBoolean());
        String referrer = generateReferrer(rand.nextBoolean());

        return String.format("%s - - %s \"%s %s %s\" %s %d \"%s\" \"%s\"",
                ip, timestamp, method, url, protocol, status, size, userAgent, referrer);
    }

    public static void main(String[] args) {
        AccessLogGenerator generator = new AccessLogGenerator();
//        for (int i = 0; i < 50; i++) {
//            String log = generator.generateLog();
//            System.out.println(log);
//        }

        ProducerFactory factory = new ProducerFactory();
        try (Producer<String, String> producer = factory.createProducer(StringSerializer.class, StringSerializer.class)) {
            String topic = "access_log";
            producer.partitionsFor(topic);
            for(int i = 0; i < 10000; i++) {
                // String log = "1.119.161.42 - - [27/05/2025:14:06:39 +0700] \"GET /api/v2/users HTTP/2.0\" 200 950 \"Mozilla/5.001 (windows; U; NT4.0; en-US; rv:1.0) Gecko/25250101\" \"-\"";
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
