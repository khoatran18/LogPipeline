import data_yaml
from ruamel.yaml import YAML
import os

yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True


data = {'action': 'start', 'type': 'enrich', 'id': 1, 'vector_name': 'enrich_vector_1',
        'timestamp': '2025-06-09T05:15:09.138Z', 'client': 'frontend-ui', 'status': 'pending',
        'data': {'source_topics': ['cisco_log_topic'], 'sink_topic': 'cisco_log_topic'}
}

def create_enrich_yaml(data):
    transform_str = data_yaml.enrich_transform_data

    sources = data_yaml.enrich_source_kafka_data.copy()
    transforms = yaml.load(transform_str)['transforms']
    sinks = data_yaml.enrich_sink_kafka_data.copy()
    enrichment_tables = data_yaml.enrich_table_data['enrichment_tables'].copy()

    sources['source_kafka']['topics'] = data['data']['source_topics']
    sources['source_kafka']['group_id'] = sources['source_kafka']['topics'][0]
    sinks['kafka_output']['topic'] = data['data']['sink_topic']
    sinks['console_output'] = data_yaml.enrich_sink_console_data['console_output'].copy()

    full_config = {
        'enrichment_tables': enrichment_tables,
        'sources': sources,
        'transforms': transforms,
        'sinks': sinks,
    }
    # with open(f"{data['vector_name']}.yaml", 'w', encoding="utf-8") as f:
    #     yaml.dump(full_config, f)

    return full_config



def create_sink_yaml(data):
    transform_str = data_yaml.sink_transform_data

    sources = data_yaml.sink_source_kafka_data.copy()
    transforms = yaml.load(transform_str)['transforms']

    sources['source_kafka']['topics'] = data['data']['source_topics']
    sources['source_kafka']['group_id'] = sources['source_kafka']['topics'][0]

    sinks = {}

    sinks['console_output'] = data_yaml.sink_sink_console_data['console_output'].copy()
    for sink in ['elasticsearch', 'clickhouse', 'aws_s3']:
        if sink in data['data']:
            if (sink == 'elasticsearch'):
                sinks['elasticsearch_output'] = data_yaml.sink_sink_elasticsearch_data['elasticsearch_output'].copy()
                sinks['elasticsearch_output']['bulk']['index'] = data['data'][sink]['index']
            elif (sink == 'clickhouse'):
                sinks['clickhouse_output'] = data_yaml.sink_sink_clickhouse_data['clickhouse_output'].copy()
                sinks['clickhouse_output']['table'] = data['data'][sink]['table']
            else:
                sinks['s3_output'] = data_yaml.sink_sink_aws_s3_data['s3_output'].copy()
                sinks['s3_output']['bucket'] = data['data'][sink]['bucket']
                sinks['s3_output']['key_prefix'] = data['data'][sink]['key_prefix']

    full_config = {
        'sources': sources,
        'transforms': transforms,
        'sinks': sinks
    }
    # with open(f"{data['vector_name']}.yaml", 'w', encoding="utf-8") as f:
    #     yaml.dump(full_config, f)

    return full_config


def create_parse_yaml(data):
    if (data['data']['source_vector'] == 'error_log'):
        transform_str = data_yaml.parse_transform_error_data
    elif (data['data']['source_vector'] == 'access_log'):
        transform_str = data_yaml.parse_transform_access_data
    elif (data['data']['source_vector'] == 'cisco_log'):
        transform_str = data_yaml.parse_transform_cisco_data
    else:
        transform_str = data_yaml.parse_transform_window_data

    sources = data_yaml.parse_source_kafka_data.copy()
    transforms = yaml.load(transform_str)['transforms']
    sinks = data_yaml.parse_sink_kafka_data.copy()
    sinks['console_output'] = data_yaml.parse_sink_console_data['console_output'].copy()

    sources['source_kafka']['topics'] = data['data']['source_topics']
    sources['source_kafka']['group_id'] = sources['source_kafka']['topics'][0]
    sinks['kafka_output']['topic'] = data['data']['sink_topic']

    full_config = {
        'sources': sources,
        'transforms': transforms,
        'sinks': sinks,
    }

    # with open(f"{data['vector_name']}.yaml", 'w', encoding="utf-8") as f:
    #     yaml.dump(full_config, f)

    return full_config

def create_yaml_config(data):
    config = {}
    type = data['type']
    if (type == 'parse'):
        config = create_parse_yaml(data)
    elif (type == 'enrich'):
        config = create_enrich_yaml(data)
    else:
        config = create_sink_yaml(data)

    return config

def main_create_yaml_file(data, folder_path):
    config = create_yaml_config(data)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(os.path.join(folder_path, f"{data['vector_name']}.yml"), 'w') as f:
        yaml.dump(config, f)