#!/usr/bin/env python3

# Copyright (c) 2016 Anki, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the file LICENSE.txt or at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Program modified by Unmesh Gundecha, http://unmesh.me

'''

Please place Cozmo on the charger for this example. When necessary, he will be
rolled off and back on.

Follow these steps to set up and run the example:
    1) Provide a a static ip, URL or similar that can be reached from the If This
        Then That server. One easy way to do this is with ngrok, which sets up
        a secure tunnel to localhost running on your machine.

        To set up ngrok:
        a) Follow instructions here to download and install:
            https://ngrok.com/download
        b) Run this command to create a secure public URL for port 8080:
            ./ngrok http 8080
        c) Note the HTTP forwarding address shown in the terminal (e.g., http://55e57164.ngrok.io).
            You will use this address in your applet, below.

        WARNING: Using ngrok exposes your local web server to the internet. See the ngrok
        documentation for more information: https://ngrok.com/docs
'''

import asyncio
import re
import sys


try:
    from aiohttp import web
except ImportError:
    sys.exit("Cannot import from aiohttp. Do `pip3 install --user aiohttp` to install")

import cozmo

from common import IFTTTRobot
from cozmo.util import degrees, distance_mm, speed_mmps

app = web.Application()


async def move_forward(request):
    robot = request.app['robot']
    
    async def forward():
        try:
            async with robot.perform_off_charger():
                '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face.'''

                # First, have Cozmo play an animation
                await robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeStartled).wait_for_completed()
                await robot.drive_straight(distance_mm(150), speed_mmps(50)).wait_for_completed()

        except cozmo.RobotBusy:
            cozmo.logger.warning("Robot was busy so didn't move")

    # Perform Cozmo's task in the background so the HTTP server responds immediately.
    asyncio.ensure_future(forward())
    return web.Response(text="OK")

async def move_backward(request):
    robot = request.app['robot']
    
    async def backward():
        try:
            async with robot.perform_off_charger():
                '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face.'''

                # First, have Cozmo play an animation
                await robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeStartled).wait_for_completed()
                await robot.drive_straight(distance_mm(-150), speed_mmps(50)).wait_for_completed()

        except cozmo.RobotBusy:
            cozmo.logger.warning("Robot was busy so didn't move")

    # Perform Cozmo's task in the background so the HTTP server responds immediately.
    asyncio.ensure_future(backward())
    return web.Response(text="OK")

async def raise_hand(request):
    robot = request.app['robot']
    
    async def raise_lift():
        try:
            async with robot.perform_off_charger():
                '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face.'''

                # First, have Cozmo play an animation
                await robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeStartled).wait_for_completed()
                await robot.set_lift_height(1.0,10.0,0.0,False,0).wait_for_completed()

        except cozmo.RobotBusy:
            cozmo.logger.warning("Robot was busy so didn't move")

    # Perform Cozmo's task in the background so the HTTP server responds immediately.
    asyncio.ensure_future(raise_lift())
    return web.Response(text="OK")

async def drop_hand(request):
    robot = request.app['robot']
    
    async def drop_lift():
        try:
            async with robot.perform_off_charger():
                '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face.'''

                # First, have Cozmo play an animation
                await robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeStartled).wait_for_completed()
                await robot.set_lift_height(0.0,10.0,0.0,False,0).wait_for_completed()
                await robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSneeze).wait_for_completed()

        except cozmo.RobotBusy:
            cozmo.logger.warning("Robot was busy so didn't move")

    # Perform Cozmo's task in the background so the HTTP server responds immediately.
    asyncio.ensure_future(drop_lift())
    return web.Response(text="OK")

# Attach the function as an HTTP handler.
app.router.add_post('/moveForward', move_forward)
app.router.add_post('/moveBackward', move_backward)
app.router.add_post('/raiseHand', raise_hand)
app.router.add_post('/dropHand', drop_hand)

if __name__ == '__main__':
    cozmo.setup_basic_logging()
    cozmo.robot.Robot.drive_off_charger_on_connect = False

    # Use our custom robot class with extra helper methods
    cozmo.conn.CozmoConnection.robot_factory = IFTTTRobot

    try:
        app_loop = asyncio.get_event_loop()
        sdk_conn = cozmo.connect_on_loop(app_loop)

        # Wait for the robot to become available and add it to the app object.
        app['robot'] = app_loop.run_until_complete(sdk_conn.wait_for_robot())
    except cozmo.ConnectionError as e:
        sys.exit("A connection error occurred: %s" % e)

    web.run_app(app)
