# ------------------------------------------------------------------------------
#   BSD 2-Clause License
#   
#   Copyright (c) 2019, Thomas Larsson
#   All rights reserved.
#   
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#   
#   1. Redistributions of source code must retain the above copyright notice, this
#      list of conditions and the following disclaimer.
#   
#   2. Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#   
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#   FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------

import bpy
from bpy.props import EnumProperty, StringProperty

from . import utils
from .utils import *

#
#   Global variables
#

_actions = []

#
#   Select or delete action
#   Delete button really deletes action. Handle with care.
#
#   listAllActions(context):
#   findActionNumber(name):
#   class MCP_OT_UpdateActionList(BvhOperator):
#

def listAllActions(context):
    global _actions

    scn = context.scene
    try:
        doFilter = scn.McpFilterActions
        filter = context.object.name
        if len(filter) > 4:
            filter = filter[0:4]
            flen = 4
        else:
            flen = len(filter)
    except:
        doFilter = False

    _actions = []
    for act in bpy.data.actions:
        name = act.name
        if (not doFilter) or (name[0:flen] == filter):
            _actions.append((name, name, name))
    bpy.types.Scene.McpActions = EnumProperty(
        items = _actions,
        name = "Actions")
    print("Actions declared")
    return _actions


def findActionNumber(name):
    global _actions
    for n,enum in enumerate(_actions):
        (name1, name2, name3) = enum
        if name == name1:
            return n
    raise MocapError("Unrecognized action %s" % name)


class MCP_OT_UpdateActionList(BvhOperator):
    bl_idname = "mcp.update_action_list"
    bl_label = "Update Action List"
    bl_description = "Update the action list"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object

    def run(self, context):
        listAllActions(context)

#
#   deleteAction(context):
#   class MCP_OT_Delete(BvhOperator):
#

def deleteActions(context):
    global _actions
    listAllActions(context)
    scn = context.scene
    try:
        act = bpy.data.actions[scn.McpActions]
    except KeyError:
        act = None
    if not act:
        raise MocapError("Did not find action %s" % scn.McpActions)
    print('Delete action', act)
    act.use_fake_user = False
    if act.users == 0:
        print("Deleting", act)
        n = findActionNumber(act.name)
        _actions.pop(n)
        bpy.data.actions.remove(act)
        print('Action', act, 'deleted')
        listAllActions(context)
        #del act
    else:
        raise MocapError("Cannot delete. Action %s has %d users." % (act.name, act.users))


class MCP_OT_Delete(BvhOperator):
    bl_idname = "mcp.delete"
    bl_label = "Delete Action"
    bl_description = "Delete the action selected in the action list"
    bl_options = {'UNDO'}

    def run(self, context):
        deleteActions(context)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=200, height=20)

    def draw(self, context):
        self.layout.label(text="Really delete action?")

#
#   deleteHash():
#   class MCP_OT_DeleteHash(BvhOperator):
#

def deleteAction(act):
    act.use_fake_user = False
    if act.users == 0:
        bpy.data.actions.remove(act)
    else:
        print("%s has %d users" % (act, act.users))


def deleteHash():
    for act in bpy.data.actions:
        if act.name[0] == '#':
            deleteAction(act)
    return


class MCP_OT_DeleteHash(BvhOperator):
    bl_idname = "mcp.delete_hash"
    bl_label = "Delete Temporary Actions"
    bl_description = (
        "Delete all actions whose name start with '#'. " +
        "Such actions are created temporarily by MakeWalk. " +
        "They should be deleted automatically but may be left over."
    )
    bl_options = {'UNDO'}

    def run(self, context):
        deleteHash()

#
#   setCurrentAction(context, prop):
#   class MCP_OT_SetCurrentAction(BvhOperator):
#

def setCurrentAction(context, prop):
    listAllActions(context)
    name = getattr(context.scene, prop)
    act = getActionFromName(name)
    context.object.animation_data.action = act
    print("Action set to %s" % act)
    return


def getActionFromName(name):
    if name in bpy.data.actions.keys():
        return bpy.data.actions[name]
    else:
        raise MocapError("Did not find action %s" % name)


def getObjectAction(ob):
    if ob and ob.animation_data:
        return ob.animation_data.action
    else:
        print("%s has no action" % ob)
        return None


class MCP_OT_SetCurrentAction(BvhOperator):
    bl_idname = "mcp.set_current_action"
    bl_label = "Set Current Action"
    bl_description = "Set the action selected in the action list as the current action"
    bl_options = {'UNDO'}

    prop : StringProperty()

    def run(self, context):
        setCurrentAction(context, self.prop)

#----------------------------------------------------------
#   Initialize
#----------------------------------------------------------

classes = [
    MCP_OT_UpdateActionList,
    MCP_OT_Delete,
    MCP_OT_DeleteHash,
    MCP_OT_SetCurrentAction,
]

def initialize():
    for cls in classes:
        bpy.utils.register_class(cls)


def uninitialize():
    for cls in classes:
        bpy.utils.unregister_class(cls)
