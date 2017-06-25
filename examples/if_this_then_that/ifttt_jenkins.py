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

'''"If This Then That" Jenkins example

This example demonstrates how "If This Then That" (http://ifttt.com) can be used
make Cozmo respond when a Jenkins build job is completed. Instructions below
will lead you through setting up an applet on the IFTTT website. When the applet
trigger is called (which sends a web request received by the web server started
in this example), Cozmo will annouce the the Build status, play an animation and
light up the cubes.

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

    2) Set up your applet on the "If This Then That" website.
        a) Sign up and sign into https://ifttt.com
        b) Create an applet: https://ifttt.com/create
        c) Set up your trigger.
            1. Click "this".
            2. Select "Maker Webhooks" as your service.
            3. Under "Choose a Trigger", select “Receive a Web request".
            4. In "Recive a Web Request", enter "JenkinsBuild" as "Event Name"
            5. Click "Create Trigger" button
        d) Set up your action.
            1. Click “that".
            2. Select “Maker Webhooks" to set it as your action channel. Connect to the Maker channel if prompted.
            3. Click “Make a web request" and fill out the fields as follows. Remember your publicly
                accessible URL from above (e.g., http://55e57164.ngrok.io) and use it in the URL field,
                followed by "/iftttJenkins" as shown below:

                 URL: http://55e57164.ngrok.io/iftttJenkins
                 Method: POST
                 Content Type: application/json
                 Body: {"project" : "{{Value1}}", "build" : "{{Value2}}", "status": "{{Value3}}"}

            5. Click “Create Action" then “Finish".

    3) Test your applet.
        a) Run this script at the command line: ./ifttt_jenkins.py
        b) On ifttt.com, on your applet page, click “Check now”. See that IFTTT confirms that the applet
            was checked.
    4) Setup Jenkins Job - requires IFTTT Build Notification Plugin
        a) In your Jenkins job "Post-build Action" section add a new "IFTTT Build Notifier" 
                action with following values:

            Event Name: JenkinsBuild
            Key: <Your Make Webhooks Key>

            Note: You can get your unique Maker Webhooks Key from https://ifttt.com/services/maker_webhooks/settings

    5) Run your Jenkins job to test the setup.
        In response to the ifttt web request, Cozmo should roll off the charger, raise and lower
        his lift, announce the status, and then animate and light-up the cubes.
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
from cozmo.objects import LightCube1Id, LightCube2Id, LightCube3Id

app = web.Application()


async def serve_jenkins(request):
    '''Define an HTTP POST handler for receiving requests from If This Then That.

    You may modify this method to change how Cozmo reacts to the Jenkins build
    notification
    '''

    json_object = await request.json()

    # Extract the name of the project and build status.
    project_name = json_object["project"]
    status = json_object["status"]

    robot = request.app['robot']
    async def read_name():
        try:
            async with robot.perform_off_charger():
                '''If necessary, Move Cozmo's Head and Lift to make it easy to see Cozmo's face.'''
                await robot.get_in_position()

                # First, have Cozmo play an animation
                await robot.play_anim_trigger(cozmo.anim.Triggers.ReactToPokeStartled).wait_for_completed()

                # Next, have Cozmo speak the name of the project and the build status.
                if status == "SUCCESS":
                    await robot.say_text("Build for " + project_name + " is successful").wait_for_completed()
                elif status == "FAILURE":
                    await robot.say_text("Build for " + project_name + " is failed").wait_for_completed()
                else:
                    await robot.say_text("Build for " + project_name + " is completed" +  status).wait_for_completed()

                # Last, have Cozmo animate & Cubes flash light based on build status
                await rock_n_roll(robot, status)

        except cozmo.RobotBusy:
            cozmo.logger.warning("Robot was busy so didn't receive status for: "+ project_name)

    # Perform Cozmo's task in the background so the HTTP server responds immediately.
    asyncio.ensure_future(read_name())

    return web.Response(text="OK")

async def rock_n_roll(robot, status):
    cube1 = robot.world.get_light_cube(LightCube1Id)  # looks like a paperclip
    cube2 = robot.world.get_light_cube(LightCube2Id)  # looks like a lamp / heart
    cube3 = robot.world.get_light_cube(LightCube3Id)  # looks like the letters 'ab' over 'T'

    if status == "SUCCESS":
        light_color = cozmo.lights.green_light
        await robot.play_anim_trigger(cozmo.anim.Triggers.PeekABooGetOutHappy).wait_for_completed()
    elif status == "FAILURE":
        light_color = cozmo.lights.red_light
        await robot.play_anim_trigger(cozmo.anim.Triggers.FrustratedByFailure).wait_for_completed()
    else:
        light_color = cozmo.lights.blue_light

    if cube1 is not None:
        cube1.set_lights(light_color)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube1Id cube - check the battery.")

    if cube2 is not None:
        cube2.set_lights(light_color)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube2Id cube - check the battery.")

    if cube3 is not None:
        cube3.set_lights(light_color)
    else:
        cozmo.logger.warning("Cozmo is not connected to a LightCube3Id cube - check the battery.")

    await asyncio.sleep(10)
    cube1.set_lights_off()
    cube2.set_lights_off()
    cube3.set_lights_off()

# Attach the function as an HTTP handler.
app.router.add_post('/iftttJenkins', serve_jenkins)

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
