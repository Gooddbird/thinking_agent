from mcp.server.fastmcp import FastMCP
import mcp.types as types

# Define available prompts
PROMPTS = {
    "read_file": types.Prompt(
        name="read_file",
        description="read a file from local or remote path",
        arguments=[
            types.PromptArgument(
                name="path",
                description="path of the file to read",
                required=True
            )
        ],
    )
}

app = FastMCP("file_system")


@app.tool(name="read_file", description="read a file from local or remote path")
async def read_file(path) -> str:
    print(path)
    return "src file name is" + path

if __name__ == "__main__":
    # 初始化并运行服务器
    app.run(transport='stdio')
