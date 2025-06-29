enrichment_table = {'enrichment_tables': {'geo_ip_db': {'type': 'mmdb', 'path': '/data/GeoLite2-City.mmdb', 'locale': 'en'}, 'threat_ip_csv': {'type': 'file', 'file': {'encoding': {'include_headers': True, 'type': 'csv'}, 'path': '/data/threat_ip.csv'}}}}

source_error_log = {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'error_log', 'topics': ['error_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True}, 'decoding': {'codec': 'bytes'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}
source_access_log = {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'access_log', 'topics': ['access_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True}, 'decoding': {'codec': 'bytes'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}
source_window_log = {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'window_log', 'topics': ['window_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True}, 'decoding': {'codec': 'bytes'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}
source_cisco_log = {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'cisco_log', 'topics': ['cisco_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True}, 'decoding': {'codec': 'bytes'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}
source_enrich = {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'enrich', 'topics': ['access_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True}, 'decoding': {'codec': 'json'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}

parse_error_log = r"""
    type: remap
    inputs:
      - source_kafka
    drop_on_abort: true
    source: |
      .message = decode_charset!(.message, "utf-8")
      .log_type = "error_log"
      check1 = parse_regex!(.message, r'(?P<timestamp>[^\[]+)\[(?P<level>\w+)\] (?P<pid>\d+)#(?P<tid>\d+)\: \*(?P<request_id>\d+) (?P<error_message>[^,]+), client\: (?P<ip>.+)')
      check2 = parse_regex!(check1.error_message, r'(?P<action>\w+)[^\"]+\"(?P<file_path>[^\"]+)\"[^\(]+\((?P<errno>\d+).+')
      .timestamp = check1.timestamp
      .level = check1.level
      .pid = check1.pid
      .tid = check1.tid
      .request_id = check1.request_id
      .ip = check1.ip
      .error_message = check1.error_message
      .action = check2.action
      .file_path = check2.file_path
      .errno = check2.errno
      
"""

parse_access_log = r"""
    type: remap
    inputs:
      - source_kafka
    drop_on_abort: true
    source: |
      .message = decode_charset!(.message, "utf-8")
      .log_type = "access_log"
      check1 = parse_regex!(.message, r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) - - \[(?P<timestamp>[0-9/\:\+\- ]+)\] \"(?P<method>\w+) (?P<url>[^ ]+) (?P<protocol>[\w/\.]+)\" (?P<status>\d+) (?P<bytes>\d+) \"(?P<user_agent>[^"]+)\" \"(?P<refer>[^"]+)\"')
      .ip = check1.ip
      .timestamp = check1.timestamp
      .method = check1.method
      .url = check1.url
      .protocol = check1.protocol
      .status = check1.status
      .bytes = check1.bytes
      .user_agent = check1.user_agent
      .refer = check1.refer
"""

parse_window_log = r"""
    type: remap
    inputs:
      - source_kafka
    drop_on_abort: true
    source: |
      .message = decode_charset!(.message, "utf-8")
      .log_type = "window_log"
      check1 = parse_xml!(.message)
              
      data_info = check1.Event.EventData.Data
      for_each(array!(data_info)) -> |_, item| {
        key = item."@Name"
        value = item.text
        . = set!(., [key], value)
      }
              
      system_info = check1.Event.System
      system_object = flatten!(system_info, "_")
      key_array = keys(system_object) 
      for_each(key_array) -> |_, key| {
        value = get!(system_object, [key])
        . = set!(., [key], value)
      }
      
      . = map_keys(.) -> |key| {
        key = replace(key, "@", "")
        key = snakecase(key)
      }
      del(.message)
      .time_created_system_time = parse_timestamp!(.time_created_system_time, "%+")
      .time_created_system_time = format_timestamp!(.time_created_system_time, "%Y-%m-%d %H:%M:%S")

"""

parse_cisco_log = r"""
    type: remap
    inputs:
      - source_kafka
    drop_on_abort: true
    source: |
      .message = decode_charset!(.message, "utf-8")
      .log_type = "cisco_log"
      check1 = parse_regex!(.message, r'%ASA-(?P<severity>\d+)-.+') 
      if (to_int!(check1.severity) == 7) {
        .severity = check1.severity
        check2 = parse_regex!(.message, r'%ASA-(?P<severity>\d+)-(?P<message_id>\d+): (?P<message_text>.+)')
        .message_text = check2.message_text
        .message_id = check2.message_id
      } else {
        .severity = check1.severity
        check2 = parse_regex!(.message, r'%ASA-(?P<severity>\d+)-(?P<message_id>\d+): (?P<message_text>.+)')
        .message_id = check2.message_id
        if (match(check2.message_text, r'Teardown .+')) {
          .event_type = "connection_teardown"
          check3 = parse_regex!(check2.message_text, r'Teardown (?P<protocol>\w+) connection (?P<conn_id>\d+) for (?P<src_zone>\w+):(?P<src_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<src_port>\d+) to (?P<dst_zone>\w+):(?P<dst_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<dst_port>\d+) duration (?P<duration>\d{1,2}(?:\:\d{1,2}){2}) bytes (?P<bytes>\d+)')
          .protocol = check3.protocol
          .conn_id = check3.conn_id
          .src_zone = check3.src_zone
          .src_ip = check3.src_ip
          .src_port = check3.src_port
          .dst_zone = check3.dst_zone
          .dst_ip = check3.dst_ip
          .dst_port = check3.dst_port
          .duration = check3.duration
          .bytes = check3.bytes
        } else if (match(check2.message_text, r'Deny .+')) {
          .event_type = "connection_denied"
          check3 = parse_regex!(check2.message_text, r'Deny (?P<protocol>\w+) src (?P<src_zone>\w+):(?P<src_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<src_port>\d+) dst (?P<dst_zone>\w+):(?P<dst_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<dst_port>\d+) by access-group "(?P<access_group>[^"]+)"')
          .protocol = check3.protocol
          .src_zone = check3.src_zone
          .src_ip = check3.src_ip
          .src_port = check3.src_port
          .dst_zone = check3.dst_zone
          .dst_ip = check3.dst_ip
          .dst_port = check3.dst_port
          .access_group = check3.access_group
        } else if (match(check2.message_text, r'Built dynamic .+')) {
          .event_type = "nat_translation"
          check3 = parse_regex!(check2.message_text, r'Built dynamic (?P<protocol>\w+) translation from (?P<src_zone>\w+):(?P<src_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<src_port>\d+) to (?P<dst_zone>\w+):(?P<dst_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<dst_port>\d+)')
          .protocol = check3.protocol
          .src_zone = check3.src_zone
          .src_ip = check3.src_ip
          .src_port = check3.src_port
          .dst_zone = check3.dst_zone
          .dst_ip = check3.dst_ip
          .dst_port = check3.dst_port
        } else if (match(check2.message_text, r'Built ICMP connection .+')) {
          .event_type = "icmp_connection"
          check3 = parse_regex!(check2.message_text, r'Built ICMP connection for faddr (?P<dst_ip>\d{1,3}(\.\d{1,3}){3})/0 gaddr (?P<nat_ip>\d{1,3}(\.\d{1,3}){3})/0 laddr (?P<src_ip>\d{1,3}(\.\d{1,3}){3})/0')
          .dst_ip = check3.dst_ip
          .nat_ip = check3.nat_ip
          .src_ip = check3.src_ip
        } else if (match(check2.message_text, r'Built \w+ \w+ connection .+')) {
          .event_type = "connection_build"
          check3 = parse_regex!(check2.message_text, r'Built (?P<direction>\w+) (?P<protocol>\w+) connection (?P<conn_id>\d+) for (?P<src_zone>\w+):(?P<src_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<src_port>\d+)(?: \((?P<nat_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<nat_port>\d+)\))? to (?P<dst_zone>\w+):(?P<dst_ip>\d{1,3}(?:\.\d{1,3}){3})/(?P<dst_port>\d+)')
          .protocol = check3.protocol
          .conn_id = check3.conn_id
          .src_zone = check3.src_zone
          .src_ip = check3.src_ip
          .src_port = check3.src_port
          .dst_zone = check3.dst_zone
          .dst_ip = check3.dst_ip
          .dst_port = check3.dst_port

          if (!is_null(check3.nat_ip)) {
            .nat_ip = check3.nat_ip
            .nat_port = check3.nat_port
          }
        }
        
      }
"""

split_parse_error_log = r"""
    type: exclusive_route
    inputs:
      - parse_json
    routes:
      - name: "sample"
        condition:
          type: vrl
          source: |
            important_levels = ["crit", "error", "alert"]
            check = true
            for_each(important_levels) -> |_, level| {
              if (.level == level) {
                check = false
              }
            }
            check
      - name: "dangerous"
        condition:
          type: vrl
          source: |
            true

      - name: "dedupe"
        condition:
          type: vrl
          source: |
            true
"""

split_parse_access_log = r"""
    type: exclusive_route
    inputs:
      - parse_json
    routes:
      - name: "sample"
        condition:
          type: "vrl"
          source: |
            statics = [ ".html", ".htm", ".css", ".js", ".mjs", ".jsx", ".tsx", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp", ".tiff", ".mp3", ".wav", ".ogg", ".mp4", ".webm", ".mov", ".avi", ".mkv", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json", ".xml", ".txt",]
            check_url = false
            for_each(statics) -> |_, static| {
              if (contains(string!(.url), static)) {
                check_url = true
              }
            }
            check_url
      - name: "dangerous"
        condition:
          type: "vrl"
          source: |
            methods = ["POST", "PUT", "DELETE"]
            check_method = false
            check_status = false
            
            for_each(methods) -> |_, refer| {
              if contains(string!(.method), refer) {
                check_method = true
              }
            }
            check_status = to_int!(.status) >= 400
            
            check_method || check_status 

      - name: "dedupe"
        condition:
          type: "vrl"
          source: |
            true
"""

split_parse_cisco_log = r"""
    type: exclusive_route
    inputs:
      - parse_json
    routes:
      - name: "sample"
        condition:
          type: vrl
          source: |
            to_int!(.severity) == 7
      - name: "dangerous"
        condition:
          type: vrl
          source: |
            string!(.event_type) == "connection_denied" || string!(.event_type) == "connection_teardown"
      - name: "dedupe"
        condition:
          type: vrl
          source: |
            true
"""

split_parse_window_log = r"""
    type: exclusive_route
    inputs:
      - parse_json
    routes:
      - name: "sample"
        condition:
          type: vrl
          source: |
            to_int!(.event_id) == 4634 # Logout

      - name: "dangerous"
        condition:
          type: vrl
          source: |
            to_int!(.event_id) == 4625 || to_int!(.event_id) == 4723
            # Failed login                 # Change password

      - name: "dedupe"
        condition:
          type: vrl
          source: |
            true
"""

sample_error_log = r"""
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""
"""

sample_access_log = r"""
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""
"""

sample_window_log = r"""
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""
"""

sample_cisco_log = r"""
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""
"""

dedupe_error_log = r"""
    type: dedupe
    inputs:
      - split_routes.dedupe
    cache:
      num_events: 1000
    fields:
      match:
        - timestamp
"""

dedupe_access_log = r"""
    type: dedupe
    inputs:
      - split_routes.dedupe
    cache:
      num_events: 5000
    fields:
      match:
        - method
        - status
        - url
        - ip
"""

dedupe_window_log = r"""
    type: dedupe
    inputs:
      - split_routes.dedupe
    cache:
      num_events: 1000
    fields:
      match:
        - ip_address
        - logon_type
        - workstation_name
        - target_user_name
"""

dedupe_cisco_log = r"""
    type: dedupe
    inputs:
      - split_routes.dedupe
    cache:
      num_events: 10000
    fields:
      match:
        - severity
        - event_type
        - src_ip
        - dst_ip
"""

sink_console = r"""
    type: console
    inputs:
      - sample_route
      - dedupe_route
      - split_routes.dangerous
    target: stdout
    encoding:
      codec: json
"""

sink_kafka = r"""
    type: kafka
    inputs:
      - sample_route
      - dedupe_route
      - split_routes.dangerous
    bootstrap_servers: broker1:29092
    topic: enrich_topic
    encoding:
      codec: json
    buffer:
      type: disk
      max_size: 268435490
      when_full: block
"""

enrich_threat = r"""
    type: remap
    inputs:
      - source_enrich_1
    drop_on_abort: true
    source: |
      threat = false
      for_each(keys(.)) -> |_, key| {
        if (contains(key, "ip")) {
          value = get!(., [key])
          if (is_ipv4(to_string!(value))) {
            # Check threat IP
            check, _ = get_enrichment_table_record("threat_ip_csv", {"ip":value})
            if (check != {}) {
              if (threat == false) {
                threat = true
              }
            }
          }
        }
      }
      .threat_ip = threat
      del(.message_key)
      del(.offset)
      del(.partition)
      del(.topic)
      del(.source_type)
      del(.headers)
"""

enrich_geo = r"""
    type: remap
    inputs:
      - source_enrich_1
    drop_on_abort: true
    source: |
      for_each(keys(.)) -> |_, key| {
        if (contains(key, "ip")) {
          value = get!(., [key])
          if (is_ipv4(to_string!(value))) {
            # Enrich Geo IP
            geo_enrich, _ = get_enrichment_table_record("geo_ip_db", {"ip": value})
            if (geo_enrich != {}) { 
              geo_name = "geo_" + key
              geo_field = {
                  "country": geo_enrich.country.names.en,
                  "latitude": geo_enrich.location.latitude,
                  "longitude": geo_enrich.location.longitude
              }
              . = set!(., [geo_name], geo_field)
            } 
      
          }
        }
      }
      del(.message_key)
      del(.offset)
      del(.partition)
      del(.topic)
      del(.source_type)
      del(.headers)
"""

enrich_all = r"""
    type: remap
    inputs:
      - source_enrich_1
    drop_on_abort: true
    source: |
      threat = false
      for_each(keys(.)) -> |_, key| {
        if (contains(key, "ip")) {
          value = get!(., [key])
          if (is_ipv4(to_string!(value))) {
      
            # Check threat IP
            check, _ = get_enrichment_table_record("threat_ip_csv", {"ip":value})
            if (check != {}) {
              if (threat == false) {
                threat = true
              }
            }
      
            # Enrich Geo IP
            geo_enrich, _ = get_enrichment_table_record("geo_ip_db", {"ip": value})
            if (geo_enrich != {}) { 
              geo_name = "geo_" + key
              geo_field = {
                  "country": geo_enrich.country.names.en,
                  "latitude": geo_enrich.location.latitude,
                  "longitude": geo_enrich.location.longitude
              }
              . = set!(., [geo_name], geo_field)
            } 
      
          }
        }
      }
      .threat_ip = threat
      del(.message_key)
      del(.offset)
      del(.partition)
      del(.topic)
      del(.source_type)
      del(.headers)
"""

enrich_null = r"""
    type: remap
    inputs:
      - source_enrich_1
    drop_on_abort: true
    source: |
      del(.message_key)
      del(.offset)
      del(.partition)
      del(.topic)
      del(.source_type)
      del(.headers)
"""

pre_transform_for_sink = r"""
  aws_s3_route:
    type: remap
    inputs:
      - del_sub_fields
    source: |
      true

  elasticsearch_route:
    type: remap
    inputs:
      - del_sub_fields
    source: |
      true
      
"""

aws_s3_error_log = r"""
    type: remap
    inputs:
      - aws_s3_route
    source: |
      .log_type == "error_log"
"""

aws_s3_access_log = r"""
    type: remap
    inputs:
      - aws_s3_route
    source: |
      .log_type == "access_log"
"""

aws_s3_window_log = r"""
    type: remap
    inputs:
      - aws_s3_route
    source: |
      .log_type == "window_log"
"""

aws_s3_cisco_log = r"""
    type: remap
    inputs:
      - aws_s3_route
    source: |
      .log_type == "cisco_log"
"""

elasticsearch_error_log = r"""
    type: remap
    inputs:
      - elasticsearch_route
    source: |
      del(.message)
      .log_type == "error_log"
"""

elasticsearch_access_log = r"""
    type: remap
    inputs:
      - elasticsearch_route
    source: |
      del(.message)
      .log_type == "access_log"
"""

elasticsearch_window_log = r"""
    type: remap
    inputs:
      - elasticsearch_route
    source: |
      del(.message)
      .log_type == "error_log"
"""

elasticsearch_cisco_log = r"""
    type: remap
    inputs:
      - elasticsearch_route
    source: |
      del(.message)
      .log_type == "cisco_log"
"""

sink_aws_s3 = r"""
    type: aws_s3
    inputs:
      - s3_route
    endpoint: http://minio:9000
    region: us-east-1
    bucket: log-bucket
    key_prefix: "year=%Y/month=%m/day=%d/{{ log_type }}/"
    force_path_style: true
    auth:
      access_key_id: minio
      secret_access_key: minio123
    buffer:
      type: disk
      max_size: 268435490
      when_full: block
    compression: gzip
    content_encoding: gzip
    filename_extension: gz
    content_type: application/json
    batch:
      max_events: 10
      max_timeout_secs: 10
    encoding:
      codec: json
"""

sink_elasticsearch = r"""
    type: elasticsearch
    inputs:
      - elasticsearch_route
    endpoint: http://elasticsearch:9200
    api_version: auto
    batch:
      max_events: 10
      timeout_secs: 10
    buffer:
      type: disk
      max_size: 268435488
      when_full: block
    mode: bulk
    bulk:
      action: index
      index: "{{ log_type }}"
      template_fallback_index: "default_log"
    distribution:
      retry_initial_backoff_secs: 1
      retry_max_duration_secs: 3600
"""

# Full config data
yaml_data = {
    'enrichment_table': enrichment_table,

    'source_error_log': source_error_log,
    'source_access_log': source_access_log,
    'source_window_log': source_window_log,
    'source_cisco_log': source_cisco_log,
    'source_enrich': source_enrich,

    'split_parse_error_log': split_parse_error_log,
    'split_parse_access_log': split_parse_access_log,
    'split_parse_window_log': split_parse_window_log,
    'split_parse_cisco_log': split_parse_cisco_log,

    'sample_error_log': sample_error_log,
    'sample_access_log': sample_access_log,
    'sample_window_log': sample_window_log,
    'sample_cisco_log': sample_cisco_log,

    'dedupe_error_log': dedupe_error_log,
    'dedupe_access_log': dedupe_access_log,
    'dedupe_window_log': dedupe_window_log,
    'dedupe_cisco_log': dedupe_cisco_log,

    'parse_error_log': parse_error_log,
    'parse_access_log': parse_access_log,
    'parse_window_log': parse_window_log,
    'parse_cisco_log': parse_cisco_log,

    'pre_transform_for_sink': pre_transform_for_sink,

    'sink_console': sink_console,
    'sink_kafka': sink_kafka,


    'enrich_geo': enrich_geo,
    'enrich_threat': enrich_threat,
    'enrich_all': enrich_all,
    'enrich_null': enrich_null,

    'aws_s3_error_log': aws_s3_error_log,
    'aws_s3_access_log': aws_s3_access_log,
    'aws_s3_window_log': aws_s3_window_log,
    'aws_s3_cisco_log': aws_s3_cisco_log,

    'elasticsearch_window_log': elasticsearch_window_log,
    'elasticsearch_cisco_log': elasticsearch_cisco_log,
    'elasticsearch_error_log': elasticsearch_error_log,
    'elasticsearch_access_log': elasticsearch_access_log,

    'sink_aws_s3': sink_aws_s3,
    'sink_elasticsearch': sink_elasticsearch,
}