import yaml_data
from ruamel.yaml import YAML
import os

yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True

data = {
  "action": "start",
  "pipelineId": 1,
  "fullPipelineConfig": {
    "id": 1,
    "inputs": [
      {
        "id": "input-1",
        "log_type": "cisco_log",
        "enrich_geoip": True,
        "enrich_threatip": True,
        "sinks": [
          {
            "id": "sink-1",
            "type": "elasticsearch",
            "config": {
              "endpoint": "http://elasticsearch:9200",
              "index": "cisco_log"
            }
          },
          {
            "id": "sink-2",
            "type": "aws_s3",
            "config": {
              "endpoint": "http://minio:9000",
              "bucket": "log-bucket",
              "key_prefix": "year=%Y/month=%m/day=%d/cisco_log",
              "auth": {
                "access_key_id": "minio",
                "secret_access_key": "minio123"
              },
              "region": "us-east-1"
            }
          }
        ]
      },
      {
        "id": "input-2",
        "log_type": "cisco_log",
        "enrich_geoip": False,
        "enrich_threatip": True,
        "sinks": [
          {
            "id": "sink-3",
            "type": "aws_s3",
            "config": {
              "endpoint": "http://minio:9000",
              "bucket": "log-bucket",
              "key_prefix": "year=%Y/month=%m/day=%d/cisco_log",
              "auth": {
                "access_key_id": "minio",
                "secret_access_key": "minio123"
              },
              "region": "us-east-1"
            }
          }
        ]
      }
    ],
    "isRunning": True
  }
}

def create_pre_config(data):
  fullPipelineConfig = data['fullPipelineConfig']['inputs']

  mainIds = [f"{config['log_type']}_{config['id']}" for config in fullPipelineConfig]
  sourceIds = [f"source_{config['log_type']}_{config['id']}" for config in fullPipelineConfig]
  transformParseIds = [f"parse_{config['log_type']}_{config['id']}" for config in fullPipelineConfig]
  transformSplitIds = [f"split_{config['log_type']}_{config['id']}" for config in fullPipelineConfig]
  transformEnrichIds = [f"enrich_{config['log_type']}_{config['id']}" for config in fullPipelineConfig]

  transformSinkId = 'transform_sink'
  # type = route
  transformSinkName = ['aws_s3', 'elasticsearch']

  transformPreSinkIds = []
  sinkIds = []

  for input_config in fullPipelineConfig:  # Lặp qua từng cấu hình input
    log_type = input_config['log_type']
    sinks = input_config['sinks']
    for sink_item in sinks:  # Lặp qua từng sink trong danh sách sinks
      sink_type = sink_item['type']
      transformPreSinkIds.append(f"transform_{log_type}_{sink_type}")
      sinkIds.append(f"sink_{log_type}_{sink_type}")

  fullConfig = {
    'fullPipelineConfig': fullPipelineConfig,
    'sourceIds': sourceIds,
    'mainIds': mainIds,
    'transformParseIds': transformParseIds,
    'transformSplitIds': transformSplitIds,
    'transformEnrichIds': transformEnrichIds,
    'transformSinkId': transformSinkId,
    'transformSinkName': transformSinkName,
    'transformPreSinkIds': transformPreSinkIds,
    'sinkIds': sinkIds,
  }

  return fullConfig

def get_log_type(name):
  if 'error_log' in name:
    return 'error_log'
  elif 'window_log' in name:
    return 'window_log'
  elif 'cisco_log' in name:
    return 'cisco_log'
  else:
    return 'access_log'

def get_sink_type(name):
  if 'elasticsearch' in name:
    return 'elasticsearch'
  else:
    return 'aws_s3'


def create_parse_source_yaml(data):
  config = create_pre_config(data)
  source_yaml = {}
  sourceIds = config['sourceIds']
  for sourceId in sourceIds:
    log_type = get_log_type(sourceId)
    source_yaml[sourceId] = yaml_data.yaml_data[f"source_{log_type}"]
  return source_yaml

def create_parse_transform_yaml(data):
  config = create_pre_config(data)
  inputsForSink = []
  parseYaml = {}
  sourceIds = config['sourceIds']
  transformParseIds = config['transformParseIds']
  transformSplitIds = config['transformSplitIds']

  for index, transformParseId in enumerate(transformParseIds):
    log_type = get_log_type(transformParseId)

    # For parse
    parse_str = yaml_data.yaml_data[f"parse_{log_type}"]
    parse = yaml.load(parse_str)
    parse['inputs'] = [sourceIds[index]]
    parseYaml[transformParseId] = parse

    # For split
    split_str = yaml_data.yaml_data[f"split_parse_{log_type}"]
    split = yaml.load(split_str)
    split['inputs'] = [transformParseId]
    parseYaml[transformSplitIds[index]] = split
    inputsForSink.append(f"{transformSplitIds[index]}.dangerous")

    # For post split
    sample_str = yaml_data.yaml_data[f"sample_{log_type}"]
    dedupe_str = yaml_data.yaml_data[f"dedupe_{log_type}"]
    sample = yaml.load(sample_str)
    dedupe = yaml.load(dedupe_str)
    sample['inputs'] = [f"{transformSplitIds[index]}.sample"]
    dedupe['inputs'] = [f"{transformSplitIds[index]}.dedupe"]
    parseYaml[f"sample_{transformSplitIds[index]}"] = sample
    parseYaml[f"dedupe_{transformSplitIds[index]}"] = dedupe
    inputsForSink.append(f"sample_{transformSplitIds[index]}")
    inputsForSink.append(f"dedupe_{transformSplitIds[index]}")

  return (parseYaml, inputsForSink)

def create_parse_sink_yaml(data):
  config = create_pre_config(data)
  pipelineId = data['fullPipelineConfig']['id']
  sinkYaml = {}
  (parseYaml, inputsForSink) = create_parse_transform_yaml(data)
  sink_console_str = yaml_data.yaml_data[f"sink_console"]
  sink_console = yaml.load(sink_console_str)
  sink_kafka_str = yaml_data.yaml_data[f"sink_kafka"]
  sink_kafka = yaml.load(sink_kafka_str)
  sink_console['inputs'] = [input for input in inputsForSink]
  sink_kafka['inputs'] = [input for input in inputsForSink]
  sink_kafka['topic'] = f"enrich_{pipelineId}"
  sinkYaml[f"console_{pipelineId}"] = sink_console
  sinkYaml[f"kafka_{pipelineId}"] = sink_kafka

  return sinkYaml

def create_parse_yaml(data):
  config = create_pre_config(data)
  source = create_parse_source_yaml(data)
  (transform, _) = create_parse_transform_yaml(data)
  sink = create_parse_sink_yaml(data)
  fullConfig = {
    'sources': source,
    'transforms': transform,
    'sinks': sink,
  }
  return fullConfig



#
# config = create_pre_config(data)
# print(create_parse_yaml(data))

def create_enrich_source_yaml(data):
  # config = create_pre_config(data)
  pipelineId = data['fullPipelineConfig']['id']
  source_id = f"source_enrich_{pipelineId}"
  sourceYaml = {}
  topic = f"enrich_{pipelineId}"
  sourceYaml[source_id] = yaml_data.yaml_data[f"source_enrich"]
  sourceYaml[source_id]['group_id'] = topic
  sourceYaml[source_id]['topics'] = [topic]

  return sourceYaml

def create_enrich_transform_yaml(data):
  transformYaml = {}
  config = create_pre_config(data)
  mainIds = config['mainIds']
  fullPipelineConfig = config['fullPipelineConfig']

  inputsPre = []
  for index, mainId in enumerate(mainIds):
    # For enrich
    id = f"enrich_{mainId}"
    inputsPre.append(id)
    enrich = None
    if fullPipelineConfig[index]['enrich_geoip'] == True and fullPipelineConfig[index]['enrich_threatip'] == True:
      enrich_str = yaml_data.yaml_data[f"enrich_all"]
      enrich = yaml.load(enrich_str)
    elif fullPipelineConfig[index]['enrich_geoip'] == True and fullPipelineConfig[index]['enrich_threatip'] == False:
      enrich_str = yaml_data.yaml_data[f"enrich_geo"]
      enrich = yaml.load(enrich_str)
    elif fullPipelineConfig[index]['enrich_geoip'] == False and fullPipelineConfig[index]['enrich_threatip'] == True:
      enrich_str = yaml_data.yaml_data[f"enrich_threat"]
      enrich = yaml.load(enrich_str)
    else:
      enrich_str = yaml_data.yaml_data["enrich_null"]
      enrich = yaml.load(enrich_str)
    transformYaml[id] = enrich

  # For Pre Transform For Sink
  preTransformForSink_str = yaml_data.yaml_data[f"pre_transform_for_sink"]
  preTransformForSink = yaml.load(preTransformForSink_str)
  transformYaml['aws_s3_route'] = preTransformForSink['aws_s3_route']
  transformYaml['elasticsearch_route'] = preTransformForSink['elasticsearch_route']
  transformYaml['aws_s3_route']['inputs'] = [input for input in inputsPre]
  transformYaml['elasticsearch_route']['inputs'] = [input for input in inputsPre]

  for index, _ in enumerate(fullPipelineConfig):
    pipeLineConfig = fullPipelineConfig[index]
    sinks = pipeLineConfig['sinks']
    for sink in sinks:
      id = f"{sink['type']}_{pipeLineConfig['log_type']}_{pipeLineConfig['id']}"
      pre_str = yaml_data.yaml_data[f"{sink['type']}_{pipeLineConfig['log_type']}"]
      pre = yaml.load(pre_str)
      transformYaml[id] = pre

  return transformYaml

def create_enrich_sink_yaml(data):
  sinkYaml = {}
  config = create_pre_config(data)
  fullPipelineConfig = config['fullPipelineConfig']

  for index, _ in enumerate(fullPipelineConfig):
    pipeLineConfig = fullPipelineConfig[index]
    sinks = pipeLineConfig['sinks']
    for sink in sinks:
      sinkConfig = sink['config']
      sink_type = sink['type']
      log_type = pipeLineConfig['log_type']
      inputId = f"{sink_type}_{log_type}_{pipeLineConfig['id']}"
      id = f"sink_{sink_type}_{log_type}_{pipeLineConfig['id']}"
      sink_str = yaml_data.yaml_data[f"sink_{sink_type}"]
      sink_v = yaml.load(sink_str)
      sink_v['inputs'] = [inputId]
      if (sink_type == 'aws_s3'):
        sink_v['endpoint'] = sinkConfig['endpoint']
        sink_v['bucket'] = sinkConfig['bucket']
        sink_v['key_prefix'] = sinkConfig['key_prefix']
        sink_v['auth']['access_key_id'] = sinkConfig['auth']['access_key_id']
        sink_v['auth']['secret_access_key'] = sinkConfig['auth']['secret_access_key']
        sink_v['region'] = sinkConfig['region']
      else:
        sink_v['endpoint'] = sinkConfig['endpoint']
        sink_v['bulk']['index'] = sinkConfig['index']
      sinkYaml[id] = sink_v

  return sinkYaml

def create_enrich_yaml(data):
  source = create_enrich_source_yaml(data)
  transform = create_enrich_transform_yaml(data)
  sink = create_enrich_sink_yaml(data)
  fullConfig = {
    'enrichment_tables': yaml_data.yaml_data['enrichment_table']['enrichment_tables'],
    'sources': source,
    'transforms': transform,
    'sinks': sink,
  }
  return fullConfig

def main_create_yaml_file(data, folder_path):
  config_parse = create_parse_yaml(data)
  config_enrich = create_enrich_yaml(data)
  parse_name = f"parse_vector_{data['fullPipelineConfig']['id']}"
  enrich_name = f"enrich_sink_vector_{data['fullPipelineConfig']['id']}"
  if not os.path.exists(folder_path):
    print(f"Creating folder: {folder_path}")
    os.makedirs(folder_path)
  with open(os.path.join(folder_path, f"{parse_name}.yml"), 'w') as f:
    print("Open successfully")
    yaml.dump(config_parse, f)
  with open(os.path.join(folder_path, f"{enrich_name}.yml"), 'w') as f:
    print("Open successfully")
    yaml.dump(config_enrich, f)

#




