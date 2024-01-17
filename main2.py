from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel
import uuid
import os, time
import helper
from LLM_Geo_kernel import Solution
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


@app.post("/generate_session")
async def generate_session(task: Task):
    session_id = str(uuid.uuid4())
    print(task)

    ## initialize the solution
    save_dir = os.path.join(os.getcwd(), 'solutions', session_id)
    os.makedirs(save_dir, exist_ok=True)

    # create graph
    model=r"gpt-4"
    solution = Solution(
                        task=task.task,
                        task_name=task.task_name,
                        save_dir=save_dir,
                        data_locations=task.data_locations,
                        model=model,
                        )
    session_state[session_id] = solution

    return {"session_id": session_id}


def SSEmodifier(contenYieldFunction):
    for content in contenYieldFunction():
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
    if session_id in session_state:
        solution: Solution = session_state[session_id]

        try: 
            return StreamingResponse(SSEmodifier(solution.yield_LLM_response_for_graph), media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" %e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_graph_html")
async def get_graph_html(session_id: str):    
    if session_id in session_state:        
        solution: Solution = session_state[session_id]

        if solution.solution_graph:
            try: 
                nt = helper.show_graph(solution.solution_graph)
                graph_html_path = os.path.join(solution.save_dir, 'solution_graph.html')
                nt.show(name=graph_html_path)
                return FileResponse(graph_html_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal error: %s" %e)
        
        else:
            raise HTTPException(status_code=404, detail="Please generate the solution graph first")

    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/{session_id}/get_operation_code")
async def get_operations_code(session_id: str):    
    if session_id in session_state:
        solution: Solution = session_state[session_id] 

        try:                      
            return StreamingResponse(SSEmodifier(solution.yield_LLM_responses_for_operations), media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" %e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/{session_id}/get_assembly_code")
async def get_assembly_code(session_id: str):
    if session_id in session_state:
        solution: Solution = session_state[session_id]

        try:
            return StreamingResponse(SSEmodifier(solution.yield_LLM_assembly_response), media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" %e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/{session_id}/execute_complete_code")
async def execute_complete_code(session_id: str):
    if session_id in session_state:
        solution: Solution = session_state[session_id]

        all_operation_code_str = '\n'.join([operation['operation_code'] for operation in solution.operations])
        all_code = all_operation_code_str + '\n' + solution.code_for_assembly
        try:
            solution.execute_complete_program(code=all_code, try_cnt=10)
            return os.listdir(solution.save_dir)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" %e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/{session_id}/return_file")
async def return_file(session_id: str, file_name: str):
    if session_id in session_state:
        file_path = os.path.join(os.getcwd(), 'solutions', session_id, file_name)
        try:
            return FileResponse(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal error: %s" %e)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)