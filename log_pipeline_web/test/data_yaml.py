parse_source_kafka_data = {'source_kafka': {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'error_log',
                     'topics': ['error_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True},
                     'decoding': {'codec': 'bytes'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}}

enrich_source_kafka_data = {'source_kafka': {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'error_log',
                     'topics': ['error_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True},
                     'decoding': {'codec': 'json'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}}

sink_source_kafka_data = {'source_kafka': {'type': 'kafka', 'bootstrap_servers': 'broker1:29092', 'group_id': 'error_log',
                     'topics': ['error_log'], 'auto_offset_reset': 'earliest', 'acknowledgements': {'enabled': True},
                     'decoding': {'codec': 'json'}, 'drain_timeout_ms': 2500, 'fetch_wait_max_ms': 100}}
############################################################################################################
parse_sink_kafka_data = {'kafka_output': {'type': 'kafka', 'inputs': ['sample_route', 'dedupe_route', 'split_routes.dangerous'],
                              'bootstrap_servers': 'broker1:29092', 'topic': 'parse_split_log', 'encoding': {'codec': 'json'},
                              'buffer': {'type': 'disk', 'max_size': 268435490, 'when_full': 'block'}, 'acknowledgements': {'enabled': True}
}}

parse_sink_console_data = {'console_output': {'type': 'console', 'inputs': ['sample_route', 'dedupe_route', 'split_routes.dangerous'],
                                'target': 'stdout', 'encoding': {'codec': 'json'}}
}

enrich_sink_console_data = {'console_output': {'type': 'console', 'inputs': ['enrich_geo_ip_threat'],
                            'target': 'stdout', 'encoding': {'codec': 'json'}}
}

enrich_sink_kafka_data = {'kafka_output': {'type': 'kafka', 'inputs': ['enrich_geo_ip_threat'],
                          'bootstrap_servers': 'broker1:29092', 'topic': 'enrich_log', 'encoding': {'codec': 'json'},
                          'buffer': {'type': 'disk', 'max_size': 268435490, 'when_full': 'block'}, 'acknowledgements': {'enabled': True}
}}


################################################################################################################
parse_transform_cisco_data = r"""
transforms:
  parse_json:
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

  split_routes:
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

  sample_route:
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""

  dedupe_route:
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

parse_transform_error_data = r"""
transforms:
  parse_json:
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
      
      # "send() \"/opt/app/storage/logs/laravel.log\" aborted (32: Broken pipe)"

  split_routes:
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


  sample_route:
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""

  dedupe_route:
    type: dedupe
    inputs:
      - split_routes.dedupe
    cache:
      num_events: 1000
    fields:
      match:
        - timestamp
"""

parse_transform_access_data = r"""
transforms:
  parse_json:
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

  split_routes:
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

  sample_route:
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""

  dedupe_route:
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

parse_transform_window_data = r"""
transforms:
  parse_json:
    type: remap
    inputs:
      - source_kafka
    drop_on_abort: true
    source: |
      .message = decode_charset!(.message, "utf-8")
      .log_type = "window_log"
      check1 = parse_xml!(.message)
      del(.message)
              
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

  split_routes:
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


  sample_route:
    type: sample
    inputs:
      - split_routes.sample
    ratio: 0.2
    sample_rate_key: ""

  dedupe_route:
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

enrich_transform_data = r"""
transforms:
  enrich_geo_ip_threat:
    type: remap
    inputs:
      - source_kafka
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


sink_transform_data = r"""
transforms:
  del_sub_fields:
    type: remap
    inputs:
      - source_kafka
    source: |
      del(.message_key)
      del(.offset)
      del(.partition)
      del(.topic)
      del(.source_type)
      del(.headers)

  s3_route:
    type: remap
    inputs:
      - del_sub_fields
    source: |
      true
      

  clickhouse_route:
    type: remap
    inputs:
      - del_sub_fields
    source: |
      . = flatten!(., "_")
      .timestamp = parse_timestamp!(.timestamp, "%+")
      .timestamp = format_timestamp!(.timestamp, "%Y-%m-%d %H:%M:%S")

  elasticsearch_route:
    type: remap
    inputs:
      - del_sub_fields
    source: |
      true
"""

######################################################################################################################
sink_sink_aws_s3_data = {'s3_output': {'type': 'aws_s3', 'inputs': ['s3_route'], 'endpoint': 'http://minio:9000',
                     'region': 'us-east-1', 'bucket': 'log-bucket', 'key_prefix': 'year=%Y/month=%m/day=%d/{{ log_type }}/',
                     'force_path_style': True, 'auth': {'access_key_id': 'minio', 'secret_access_key': 'minio123'},
                     'buffer': {'type': 'disk', 'max_size': 268435490, 'when_full': 'block'}, 'compression': 'gzip',
                     'content_encoding': 'gzip', 'filename_extension': 'gz', 'content_type': 'application/json',
                     'batch': {'max_events': 10, 'max_timeout_secs': 10}, 'encoding': {'codec': 'json'}}}

sink_sink_elasticsearch_data = {'elasticsearch_output': {'type': 'elasticsearch', 'inputs': ['elasticsearch_route'],
                                'endpoint': 'http://elasticsearch:9200', 'api_version': 'auto',
                                'batch': {'max_events': 10, 'timeout_secs': 10},
                                'buffer': {'type': 'disk', 'max_size': 268435488, 'when_full': 'block'},
                                'mode': 'bulk', 'bulk': {'action': 'index', 'index': '{{ log_type }}',
                                                         'template_fallback_index': 'default_log'},
                                'distribution': {'retry_initial_backoff_secs': 1, 'retry_max_duration_secs': 3600}}}

sink_sink_clickhouse_data = {'clickhouse_output': {'type': 'clickhouse', 'inputs': ['clickhouse_route'], 'endpoint': 'http://clickhouse:8123',
                             'table': '{{ log_type }}', 'format': 'json_each_row', 'skip_unknown_fields': True,
                             'acknowledgements': {'enabled': True},
                             'auth': {'strategy': 'basic', 'user': 'default', 'password': ''},
                             'batch': {'max_events': 1, 'timeout_secs': 1},
                             'buffer': {'type': 'disk', 'max_size': 268435490, 'when_full': 'block'},
                             'healthcheck': {'enabled': True}, 'database': 'log_database'}}

sink_sink_console_data = {'console_output': {'type': 'console', 'inputs': ['clickhouse_route'], 'target': 'stdout',
                                             'encoding': {'codec': 'json'}}}

enrich_table_data = {'enrichment_tables': {'geo_ip_db': {'type': 'mmdb', 'path': '/data/GeoLite2-City.mmdb', 'locale': 'en'},
                                           'threat_ip_csv': {'type': 'file', 'file':
                                               {'encoding': {'include_headers': True, 'type': 'csv'},
                                                'path': '/data/threat_ip.csv'}}}}

