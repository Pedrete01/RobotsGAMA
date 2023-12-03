import asyncio
from asyncio import Future
from typing import Dict
import math
import json

from gama_client.base_client import GamaBaseClient
from gama_client.command_types import CommandTypes
from gama_client.message_types import MessageTypes

experiment_future: Future
play_future: Future
pause_future: Future
expression_future: Future
step_future: Future
stop_future: Future

velocity = 0.05

async def message_handler(message: Dict):
    print("received", message)
    if "command" in message:
        if message["command"]["type"] == CommandTypes.Load.value:
            experiment_future.set_result(message)
        elif message["command"]["type"] == CommandTypes.Play.value:
            play_future.set_result(message)
        elif message["command"]["type"] == CommandTypes.Pause.value:
            pause_future.set_result(message)
        elif message["command"]["type"] == CommandTypes.Expression.value:
            expression_future.set_result(message)
        elif message["command"]["type"] == CommandTypes.Step.value:
            step_future.set_result(message)
        elif message["command"]["type"] == CommandTypes.Stop.value:
            stop_future.set_result(message)

async def new_angle(pos, posN, ang):
    vr = [] 
    pos = pos.replace("{", "[").replace("}", "]")
    pos = json.loads(pos)

    posN = posN.replace("{", "[").replace("}", "]")
    posN = json.loads(posN)

    ang = ang.replace("{", "[").replace("}", "]")
    ang = json.loads(ang)

    for i in range(len(pos)):
        if(math.sqrt((posN[i][0] - pos[i][0])**2 + (posN[i][1] - pos[i][1])**2) < 2):
            vr.append(ang[i] + 45)
        else:
            vr.append(ang[i])

    return vr

async def new_velocity(ang):

    vt = [] 

    for i in ang:
        vt.append(velocity)

    return vt

async def main():

    global experiment_future
    global play_future
    global pause_future
    global expression_future
    global step_future
    global stop_future

    # Experiment and Gama-server constants
    MY_SERVER_URL = "localhost"
    MY_SERVER_PORT = 6868
    GAML_FILE_PATH_ON_SERVER = r"C:\Users\pedre\Gama_Workspace\Control\models\Robots.gaml"
    EXPERIMENT_NAME = "robots_move"
    MY_EXP_INIT_PARAMETERS = [{"type": "int", "name": "nRobots", "value": 100}]

    client = GamaBaseClient(MY_SERVER_URL, MY_SERVER_PORT, message_handler)

    print("connecting to Gama server")
    await client.connect()

    print("initialize a gaml model")
    experiment_future = asyncio.get_running_loop().create_future()
    await client.load(GAML_FILE_PATH_ON_SERVER, EXPERIMENT_NAME, True, True, True, MY_EXP_INIT_PARAMETERS)
    gama_response = await experiment_future

    try:
        experiment_id = gama_response["content"]
    except Exception as e:
        print("error while initializing", gama_response, e)
        return

    print("initialization successful, running the model")
    play_future = asyncio.get_running_loop().create_future()
    await client.play(experiment_id)
    gama_response = await play_future
    if gama_response["type"] != MessageTypes.CommandExecutedSuccessfully.value:
        print("error while trying to run the experiment", gama_response)
        return

    print("model running, waiting a bit")
    await asyncio.sleep(2)

    print("pausing the model")
    pause_future = asyncio.get_running_loop().create_future()
    await client.pause(experiment_id)
    gama_response = await pause_future
    if gama_response["type"] != MessageTypes.CommandExecutedSuccessfully.value:
        print("Unable to pause the experiment", gama_response)
        return

    while True:

        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"cycle")
        gama_response = await expression_future
        print("asking simulation the value of: cycle=", gama_response["content"])

        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"nRobots")
        gama_response = await expression_future
        print("asking simulation the value of: nRobots=",  gama_response["content"])

        print("asking simulation the value of: Position Robots")
        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"get_agents_pos()")
        gama_response = await expression_future
        positions = gama_response["content"]

        print("asking simulation the value of: Vecinos Robots")
        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"get_agents_neigh()")
        gama_response = await expression_future
        vecinos = gama_response["content"]

        print("asking simulation the value of: Angulos Robots")
        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"get_agents_angulo()")
        gama_response = await expression_future
        angulos = gama_response["content"]

        vr = await new_angle(positions, vecinos, angulos)
        vt = await new_velocity(angulos)

        print("asking simulation to setting: Velocity Robots")
        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, fr"set_agents_vel(matrix({vt}),matrix({vr}))")
        gama_response = await expression_future

        print("asking gama to run 1 more steps of the experiment")
        step_future = asyncio.get_running_loop().create_future()
        await client.step(experiment_id, 1, True)
        gama_response = await step_future
        if gama_response["type"] != MessageTypes.CommandExecutedSuccessfully.value:
            print("Unable to execute 1 new steps in the experiment", gama_response)
            return

        expression_future = asyncio.get_running_loop().create_future()
        await client.expression(experiment_id, r"cycle")
        gama_response = await expression_future
        print("asking simulation the value of: cycle=", gama_response["content"])

    print("killing the simulation")
    stop_future = asyncio.get_running_loop().create_future()
    await client.stop(experiment_id)
    gama_response = await stop_future
    if gama_response["type"] != MessageTypes.CommandExecutedSuccessfully.value:
        print("Unable to stop the experiment", gama_response)
        return


if __name__ == "__main__":
    asyncio.run(main())