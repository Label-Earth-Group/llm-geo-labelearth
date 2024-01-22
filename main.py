from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel
import uuid
import os, time
import helper
from LLM_Geo_kernel import Solution
import pickle
import networkx as nx

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# This dictionary will store the state. In production, consider a more robust solution like Redis
session_state = {}


class Task(BaseModel):
    task_name: str
    task: str = None
    data_locations: list[str]


def retrieve_solution(session_id) -> Solution or None:
    if session_id in session_state:
        solution = session_state[session_id]
        return solution
    if session_id in os.listdir(os.path.join(os.getcwd(), 'solutions')):
        try:
            with open(os.path.join(os.getcwd(), 'solutions', session_id, 'solution.pkl'), 'rb') as file:
                solution = pickle.load(file)
                return solution
        except Exception as e:
            return None
    return None


@app.post("/generate_session")
async def generate_session(task: Task):
    session_id = str(uuid.uuid4())
    print(task)

    # initialize the solution
    save_dir = os.path.join(os.getcwd(), 'solutions', session_id)
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, 'output'), exist_ok=True)  # make the output dir

    # create graph
    model = r"gpt-4"
    solution = Solution(
        task=task.task,
        task_name=task.task_name,
        save_dir=save_dir,
        data_locations=task.data_locations,
        model=model,
    )
    session_state[session_id] = solution

    return {"session_id": session_id}


def SSEmodifier(contenYieldIterator):
    for content in contenYieldIterator:
        try:
            # Split the content by newlines and reformat
            lines = content.split('\n')
            formatted_content = '\n'.join(f"data: {line}" for line in lines)
            yield f"{formatted_content}\n\n"
        except Exception as e:
            print("Connection to client lost, stopping stream")
            break
    yield "event: contentclose\ndata: end\n\n"  # to gracefully stop the stream


@app.get("/{session_id}/get_graph_code")
async def get_graph_code(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:
        try:
            return StreamingResponse(SSEmodifier(solution.yield_LLM_response_for_graph()),
                                     media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" % e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_graph_html")
async def get_graph_html(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:

        if solution.solution_graph:
            try:
                nt = helper.show_graph(solution.solution_graph)
                graph_html_path = os.path.join(solution.save_dir, 'solution_graph.html')
                nt.save_graph(name=graph_html_path)
                return FileResponse(graph_html_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal error: %s" % e)

        else:
            raise HTTPException(status_code=404, detail="Please generate the solution graph first")

    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_operation_code")
async def get_operations_code(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:

        if solution.solution_graph:
            try:
                return StreamingResponse(SSEmodifier(solution.yield_LLM_responses_for_operations()),
                                         media_type="text/event-stream")
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal error: %s" % e)
        else:
            raise HTTPException(status_code=404, detail="Please generate the solution graph first")

    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_assembly_code")
async def get_assembly_code(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:

        if solution.operations:
            try:
                return StreamingResponse(SSEmodifier(solution.yield_LLM_assembly_response()),
                                         media_type="text/event-stream")
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal error: %s" % e)
        else:
            raise HTTPException(status_code=404, detail="Please generate the code for each operation first")

    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/execute_complete_code")
async def execute_complete_code(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:

        if solution.code_for_assembly:
            try:
                return StreamingResponse(SSEmodifier(solution.yield_execute_complete_program(try_cnt=10)),
                                         media_type="text/event-stream")
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal error: %s" % e)
        else:
            raise HTTPException(status_code=404, detail="Please generate the assembly code first")

    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/list_output_files")
async def list_output_files(session_id: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:
        try:
            output_dir = os.path.join(solution.save_dir, 'output')
            return os.listdir(output_dir)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" % e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_file/{file_name}")
async def get_file(session_id: str, file_name: str):
    solution: Solution = retrieve_solution(session_id)
    if solution:
        try:
            file_path = os.path.join(solution.save_dir, 'output', file_name)
            return FileResponse(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" % e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
