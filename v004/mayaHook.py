import maya.cmds as mc
import maya.mel as mm

import sys, os

from tools.utils import config
reload(config)

def getSceneName() : 
	currentScene = mc.file(q = True, sn = True)
	
	return currentScene


def createReference(namespace, path) : 
	result = mc.file(path, r = True, type = 'mayaAscii', namespace = namespace, ignoreVersion = True, options = 'v=0')

	return result


def getAllReferencePath() : 
	return mc.file(q = True, r = True)


def getNamespace(path) : 
	return mc.file(path, q = True, namespace = True)