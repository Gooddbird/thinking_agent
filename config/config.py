import json

def read_mcp_server_config():
    with open("E:\\ai_workspace\\thinking_agent\\config\\mcp_server_config.json") as json_file:
        return json.load(json_file)


g_mcp_server_config = read_mcp_server_config()
