import os
import requests
import networkx as nx
import pandas as pd
import geopandas as gpd
from pyvis.network import Network
import openai
import LLM_Geo_Constants as constants
import helper
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import base64
import json
from pydantic import BaseModel
from LLM_Geo_kernel import Solution
from IPython.display import display, HTML, Code
from IPython.display import clear_output
from fastapi.middleware.cors import CORSMiddleware
import logging
isReview = True
app = FastAPI()

# 将配置挂在到app上
app.add_middleware(
    CORSMiddleware,
    # 这里配置允许跨域访问的前端地址
    allow_origins=["*"],
    # 跨域请求是否支持 cookie， 如果这里配置true，则allow_origins不能配置*
    allow_credentials=True,
    # 支持跨域的请求类型，可以单独配置get、post等，也可以直接使用通配符*表示支持所有
    allow_methods=["*"],
    allow_headers=["*"],
)
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
fh = logging.FileHandler(filename='./log/server.log')
formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s"
)

ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch) #将日志输出至屏幕
logger.addHandler(fh) #将日志输出至文件


logger = logging.getLogger(__name__)

class Item(BaseModel):
    task_name: str
    task: str
    data_locations: list = []

@app.post("/stream_suite")
async def stream_suite(request_data: Item):
    def stream_content():
        task_name = request_data.task_name
        task = request_data.task
        data_locations = request_data.data_locations

        save_dir = os.path.join(os.getcwd(), task_name)
        os.makedirs(save_dir, exist_ok=True)

        # create graph
        model = r"gpt-4"
        solution = Solution(
            task=task,
            task_name=task_name,
            save_dir=save_dir,
            data_locations=data_locations,
            model=model,
        )
        response_for_graph = solution.get_LLM_response_for_graph()
        solution.graph_response = response_for_graph
        solution.save_solution()

        # Stream text content
        text_content = solution.code_for_graph
        logger.info("第一次返回：" + text_content)
        yield "event: message\ndata: " + json.dumps({"type": "text", "data": text_content}) + "\n\n"

        # Show the graph
        G = nx.read_graphml(solution.graph_file)
        nt = helper.show_graph(G)
        html_name = os.path.join(os.getcwd(), solution.task_name + '.html')

        nt.show(name=html_name)
        with open(html_name, "r") as f:
            html_content = f.read()
        os.remove(html_name)
        # Stream HTML content
        logger.info("第2次返回：" + html_content)
        yield "event: message\ndata: " + json.dumps({"type": "html", "data": html_content}) + "\n\n"

        operations = solution.get_LLM_responses_for_operations(review=isReview)
        solution.save_solution()

        all_operation_code_str = '\n'.join([operation['operation_code'] for operation in operations])

        assembly_LLM_response = solution.get_LLM_assembly_response(review=isReview)
        solution.assembly_LLM_response = assembly_LLM_response
        solution.save_solution()

        # Stream code content
        code_content = all_operation_code_str + '\n' + solution.code_for_assembly
        logger.info("第3次返回：" + code_content)
        yield "event: message\ndata: " + json.dumps({"type": "code", "data": code_content}) + "\n\n"
        # Stream image content
        with open("result.png", "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
            logger.info("第4次返回：")
            yield "event: message\ndata: " + json.dumps({"type": "image", "data": "data:image/png;base64," + encoded_image}) + "\n\n"
    return StreamingResponse(stream_content(), media_type="text/event-stream")



@app.post('/llmgeo')
async def handler(request_data: Item):
    task_name = request_data.task_name
    task = request_data.task
    data_locations = request_data.data_locations

    save_dir = os.path.join(os.getcwd(), task_name)
    os.makedirs(save_dir, exist_ok=True)

    # create graph
    model = r"gpt-3.5-turbo"
    solution = Solution(
        task=task,
        task_name=task_name,
        save_dir=save_dir,
        data_locations=data_locations,
        model=model,
    )
    response_for_graph = solution.get_LLM_response_for_graph()
    solution.graph_response = response_for_graph
    solution.save_solution()

    # clear_output(wait=True)
    # display(Code(solution.code_for_graph, language='python'))
    #
    # exec(solution.code_for_graph)
    # solution_graph = solution.load_graph_file()

    # Show the graph
    G = nx.read_graphml(solution.graph_file)
    nt = helper.show_graph(G)
    html_name = os.path.join(os.getcwd(), solution.task_name + '.html')

    nt.show(name=html_name)
    with open(html_name, "r") as f:
        d = f.read()
    os.remove(html_name)
    return d

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)