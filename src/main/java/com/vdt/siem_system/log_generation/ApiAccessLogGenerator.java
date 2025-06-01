package com.vdt.siem_system.log_generation;

import com.github.javafaker.Faker;
import com.google.gson.Gson;

import java.text.SimpleDateFormat;
import java.util.*;

// ------------------------------------------------------------------------------------------------------------
// (Demo) API Access Log - Web Access Log Generator (Json Format)
// ------------------------------------------------------------------------------------------------------------
public class ApiAccessLogGenerator {

    private final Faker faker = new Faker();
    private final Random rand = new Random();
    private final Gson gson = new Gson();

    private static final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS Z");
    static {
        dateFormat.setTimeZone(TimeZone.getTimeZone("GMT+7"));
    }

    //////////////////////////////////////// For Array of Values ////////////////////////////////////////

    private static final String[] METHODS = {"GET", "POST", "PUT", "DELETE"};
    private static final String[] ENDPOINTS = {
            "/api/login", "/api/logout", "/api/users", "/api/users/{id}", "/api/orders",
            "/api/orders/{id}", "/api/products", "/api/products/{id}", "/api/profile",
            "/api/settings", "/api/notifications", "/api/reset-password", "/api/search?q=test"
    };
    private static final String[] APP_NAMES = {
            "auth-service", "payment-service", "user-service", "inventory-service",
            "gateway-api", "reporting-service", "notification-service"
    };
    private static final String[] ENVS = {
            "production", "staging", "development", "qa", "testing"
    };
    private static final String[] NORMAL_USER_AGENTS = {
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Firefox/113.0",
            "Mozilla/5.0 (Linux; Android 11) Mobile Safari/537.36"
    };
    private static final String[] SUSPICIOUS_USER_AGENTS = {
            "curl/7.68.0", "sqlmap/1.6.12", "python-requests/2.31",
            "Wget/1.20.3", "dirb/2.22", "Mozilla/5.0 evil-bot/0.1"
    };
    private static final Map<String, Integer[]> METHOD_STATUS_MAP = new HashMap<>();
    static {
        METHOD_STATUS_MAP.put("GET",     new Integer[]{200, 301, 403, 404, 500});
        METHOD_STATUS_MAP.put("POST",    new Integer[]{200, 201, 400, 403, 422, 500});
        METHOD_STATUS_MAP.put("PUT",     new Integer[]{200, 204, 400, 403, 409});
        METHOD_STATUS_MAP.put("DELETE",  new Integer[]{200, 202, 204, 403, 404});
        METHOD_STATUS_MAP.put("PATCH",   new Integer[]{200, 204, 400, 422});
    }


    //////////////////////////////////////// For getting values ////////////////////////////////////////

    public String generateTimestamp() {
        long now = System.currentTimeMillis();
        long offset = rand.nextInt(7 * 24 * 60 * 60) * 1000;
        return dateFormat.format(new Date(now - offset));
    }

    public String generateMethod() {
        return faker.options().option(METHODS);
    }

    public String generateEndpoint() {
        String endpoint = faker.options().option(ENDPOINTS);
        return endpoint.replace("{id}", String.valueOf(rand.nextInt(1000) + 1));
    }

    public int generateStatus(String method) {
        Integer[] status = METHOD_STATUS_MAP.get(method);
        return faker.options().option(status);
    }

    public int generateResponseTime() {
        return rand.nextInt(1000) + 100;
    }

    public String generateIp() {
        return faker.internet().ipV4Address();
    }

    public String generateUserAgent(boolean isAttack) {
        return isAttack
                ? faker.options().option(SUSPICIOUS_USER_AGENTS)
                : faker.internet().userAgentAny();
    }

    public String generateSessionId() {
        return UUID.randomUUID().toString();
    }

    public String generateUserId() {
        return "u" + faker.number().digits(5);
    }

    public String generateTraceId() {
        return UUID.randomUUID().toString();
    }

    public String generateAppName() {
        return faker.options().option(APP_NAMES);
    }

    public String generateEnv() {
        return faker.options().option(ENVS);
    }

    public String generateLevel(int status) {
        if (status >= 500) return "ERROR";
        if (status >= 400) return "WARN";
        return "INFO";
    }


    //////////////////////////////////////// For generating logs //////////////////////////////////////

    public String generateLog() {
        String method = generateMethod();
        String endpoint = generateEndpoint();
        int statusCode = generateStatus(method);

        Map<String, Object> log = new LinkedHashMap<>();
        log.put("timestamp", generateTimestamp());
        log.put("level", generateLevel(statusCode));
        log.put("method", method);
        log.put("endpoint", endpoint);
        log.put("statusCode", statusCode);
        log.put("responseTime", generateResponseTime());
        log.put("ip", generateIp());
        log.put("userAgent", generateUserAgent(rand.nextBoolean()));
        log.put("sessionId", generateSessionId());
        log.put("userId", generateUserId());
        log.put("traceId", generateTraceId());
        log.put("appName", generateAppName());
        log.put("env", generateEnv());

        return gson.toJson(log);
    }


    public static void main(String[] args) {
        ApiAccessLogGenerator generator = new ApiAccessLogGenerator();
        for(int i = 0; i < 20; i++) {
            System.out.println(generator.generateLog());
        }
    }


}
