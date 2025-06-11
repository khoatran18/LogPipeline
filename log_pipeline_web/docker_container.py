import subprocess
import os

def run_container(data, folder_path):
    parse_name = f"parse_vector_{data['fullPipelineConfig']['id']}"
    enrich_name = f"enrich_sink_vector_{data['fullPipelineConfig']['id']}"
    container_names = [parse_name, enrich_name]
    subprocess.run(["docker", "network", "create", "log-pipeline-net"])

    for container_name in container_names:
        config_path = os.path.abspath(f"{folder_path}/{container_name}.yml")
        cmd = []
        if (data['action'] == 'start'):
            subprocess.run(["docker", "rm", "-f", container_name])
            if ('enrich' in container_name):
                data_path_1 = os.path.abspath(f"data/enrich/GeoLite2-City.mmdb")
                data_path_2 = os.path.abspath(f"data/enrich/threat_ip.csv")
                cmd = ["docker", "run", "-d",
                    "--name", container_name,
                    "--hostname", container_name,
                    "--restart", "unless-stopped",
                    "--network", "log-pipeline-net",
                    "-v", f"{config_path}:/etc/vector/vector.yaml:ro",
                    "-v", f"{data_path_1}:/data/GeoLite2-City.mmdb",
                    "-v", f"{data_path_2}:/data/threat_ip.csv",
                    "-p", f"{8686 + 1 + 2*int(data['pipelineId'])}:8686",
                    "timberio/vector:0.46.1-debian"
                ]
            else:
                cmd = ["docker", "run", "-d",
                   "--name", container_name,
                   "--hostname", container_name,
                   "--restart", "unless-stopped",
                   "--network", "log-pipeline-net",
                   "-v", f"{config_path}:/etc/vector/vector.yaml:ro",
                   "-p", f"{8686 + 2*int(data['pipelineId'])}:8686",
                   "timberio/vector:0.46.1-debian"
                   ]
        elif (data['action'] == 'stop'):
            cmd = ["docker", "stop", container_name]
            cmd = ["docker", "rm", "-f", container_name]
        elif (data['action'] == 'restart'):
            cmd = ["docker", "restart", container_name]
        elif (data['action'] == 'delete'):
            cmd = ["docker", "rm", "-f", container_name]

        subprocess.run(cmd)