#Import python modules
import sys, os, re, shutil, urllib, subprocess, time

# from PyQt4 import QtCore
# from PyQt4 import QtGui
# import sip
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *

#Import GUI
from PySide import QtCore
from PySide import QtGui

from shiboken import wrapInstance


# import ui
from arxLoader import ui as ui
reload(ui)

from arxLoader import mayaHook as hook
reload(hook)

from utils import config, fileUtils
reload(config)
reload(fileUtils)

from sgUtils import sgUtils
reload(sgUtils)

moduleDir = sys.modules[__name__].__file__


# If inside Maya open Maya GUI
def getMayaWindow():
	ptr = mui.MQtUtil.mainWindow()
	return wrapInstance(long(ptr), QtGui.QWidget)
	# return sip.wrapinstance(long(ptr), QObject)

import maya.OpenMayaUI as mui
getMayaWindow()


class MyForm(QtGui.QMainWindow):

	def __init__(self, parent=None):
		self.count = 0
		#Setup Window
		super(MyForm, self).__init__(parent)
		# QtGui.QWidget.__init__(self, parent)
		self.ui = ui.Ui_loaderWindow()
		self.ui.setupUi(self)


		# custom variable
		self.configPath = '%s/config.txt' % os.path.split(moduleDir)[0]
		self.configData = config.readSetting(self.configPath)
		self.moduleDir = moduleDir
		self.iconPath = '%s/%s' % (os.path.split(self.moduleDir)[0], 'icons')
		self.root = eval(self.configData['root'])['windowRoot']
		self.rootProject = '%s/%s' % (self.root, self.configData['rootProject'])
		self.assetRoot = '%s/%s' % (self.root, self.configData['assetRoot'])
		self.fileExt = eval(self.configData['ext'])['maya']
		self.noPreviewIcon = '%s/%s' % (self.iconPath, 'noPreview.png')
		self.thumbnail = self.configData['thumbnail']

		# init connections
		self.initConnections()

		# init functions
		self.initFunctions()



	def initConnections(self) : 
		self.ui.shotgun_radioButton.toggled.connect(self.setWindowMode)
		self.ui.createReference_pushButton.clicked.connect(self.doCreateReference)
		self.ui.search_lineEdit.textChanged.connect(self.listAllAsset)
		self.ui.type_checkBox.stateChanged.connect(self.setFilterSignal1)
		self.ui.parent_checkBox.stateChanged.connect(self.setFilterSignal2)
		self.ui.variation_checkBox.stateChanged.connect(self.setFilterSignal3)
		self.ui.main_listWidget.customContextMenuRequested.connect(self.showMenu)
		self.ui.thumbnail_checkBox.stateChanged.connect(self.refreshUI)


	def initFunctions(self) : 
		# set the correct layout window
		self.loadData()
		self.setWindowMode()
		


	# window area =========================================================================

	def setWindowMode(self) : 
		# check what mode is checked 
		if self.ui.shotgun_radioButton.isChecked() : 
			value = False
			w = 550
			h = 640
			lPos = 320
			text = 'Shotgun Asset List'
			value2 = True
			mode = 'shotgun'


		if self.ui.manualBrowser_radioButton.isChecked() : 
			value = True
			w = 850
			h = 640
			lPos = 620
			text = 'All Asset List'
			value2 = False
			mode = 'browser'
		
		# show / hide
		self.ui.add_pushButton.setVisible(value)
		self.ui.remove_pushButton.setVisible(value)
		self.ui.clear_pushButton.setVisible(value)
		self.ui.search_frame.setVisible(value)
		self.ui.filter_frame.setVisible(value)
		self.ui.list_frame.setVisible(value)
		self.ui.main_label.setText(text)
		self.ui.projectInfo_frame.setVisible(value2)

		# resizing window
		self.ui.frame.resize(w, h)
		self.resize(w + 14, h + 14)
		self.ui.logo_label.setGeometry(lPos, 10, 221, 61)
		self.setLogo()

		# set all UI
		self.ui.information_label.setText('Processing ...')
		QtGui.QApplication.processEvents()
		self.setUI(mode)


	def setLogo(self) : 
		# set company logo
		logo = self.configData['logo']
		iconPath = '%s/%s' % (self.iconPath, logo)
		self.ui.logo_label.setPixmap(QtGui.QPixmap(iconPath).scaled(200, 40, QtCore.Qt.KeepAspectRatio))



	def refreshUI(self) : 
		# check what mode is checked 
		if self.ui.shotgun_radioButton.isChecked() : 
			mode = 'shotgun'


		if self.ui.manualBrowser_radioButton.isChecked() : 
			mode = 'browser'

		# set all UI
		self.setUI(mode)


	# load data ==================================================================================================


	def loadData(self) : 
		# load scene name
		sceneName = hook.getSceneName()
		self.sceneInfo = self.getSceneInfo(sceneName)

		# load shotgun shot
		self.shotAssets = self.loadShotgunAsset()

		# load all shotgun asset
		self.allSgAssets = self.loadAllShotgunAsset()

		# asset info
		if self.allSgAssets : 
			self.assetInfo = self.getAssetInfo(self.allSgAssets)



	def getSceneInfo(self, sceneName) : 
		# layout ex.
		# U:/projects/ttv/episodes/e100/work/sq010/layout/maya/ttv_e100_010_layout.v002.ma
		eles = sceneName.replace('%s/' % self.rootProject, '').split('/')
		episode = eles[0]
		level = eles[1]
		sequence = eles[2]
		fileName = eles[-1]
		shot = ''
		project = 'ttv_%s' % episode

		if 'layout' in eles : 
			step = eles[3]

		if 'anim' in eles : 
			shot = eles[3]
			step = eles[4]


		info = {'project': project, 'episode': episode, 'step': step, 'sequence': sequence, 'shot': shot}

		return info


	def loadShotgunAsset(self) : 
		sceneName = hook.getSceneName()
		sceneInfo = self.getSceneInfo(sceneName)
		step = sceneInfo['step']
		projName = sceneInfo['project']
		episode = sceneInfo['episode']
		sequenceName = sceneInfo['sequence']
		shotName = sceneInfo['shot']

		if step == 'layout' : 
			shotCode = '%s_%s_layout' % (episode, sequenceName.replace('sq', ''))

		if step == 'anim' : 
			shotCode = '%s_%s_%s' % (episode, sequenceName.replace('sq', ''), shotName.replace('sh', ''))

		shots = sgUtils.sgGetShot(projName, sequenceName)

		if shots : 
			for eachShot in shots : 
				if shotCode == eachShot['code'] : 
					assets = eachShot['assets']

					return assets


	def loadAllShotgunAsset(self) : 
		# using asset from this project
		# sceneName = hook.getSceneName()
		# sceneInfo = self.getSceneInfo(sceneName)
		# projName = sceneInfo['project']

		# using ttv_assets as a master asset project
		projName = self.configData['assetProject']

		assets = sgUtils.sgGetAllAssets(projName, fields=['code', 'id', 'sg_origin_id', 'sg_asset_type', 'sg_parent', 'sg_folder', 'sg_status_list', 'image'])

		return assets



	def downloadThumbnail(self) : 
		if self.thumbnail == 'auto' : 
			print 'Checking Thumbnail ...'
			countImage = 0
			
			for each in self.assetInfo : 
				image = self.assetInfo[each]['image']
				thumbnailFile = self.assetInfo[each]['thumbnailFile']
				thumbnailPath = os.path.dirname(thumbnailFile)
				code = self.assetInfo[each]['code']

				if image : 
					if not os.path.exists(thumbnailFile) : 
						if not os.path.exists(thumbnailPath) : 
							os.makedirs(thumbnailPath)

						print 'Downloading %s ...' % code
						self.ui.information_label.setText('Downloading %s...' % code)
						QtGui.QApplication.processEvents()

						urllib.urlretrieve(image, thumbnailFile)


			print 'Done'





	def getAssetInfo(self, sgAssets) : 
		assetInfo = dict()

		for each in sgAssets : 
			id = each['id']
			originID = each['sg_origin_id']
			code = each['code']
			assetType = each['sg_asset_type']
			parent = each['sg_parent']
			variation = each['sg_folder']
			pullFile = None
			publishFile = str()
			publishPxyFile = str()
			fileType = 'No File'
			image = each['image']

			if assetType and parent and variation : 
				approvedPath = os.path.join(self.assetRoot, 'approved', assetType, parent, variation, 'rig', 'maya').replace('\\', '/')
				publishPath = os.path.join(self.assetRoot, 'publish', assetType, parent, variation, 'rig', 'maya').replace('\\', '/')
				thumbnailPath = os.path.join(self.assetRoot, 'publish', assetType, parent, variation, '_shotgun').replace('\\', '/')
				thumbnailFile = '%s/%s' % (thumbnailPath, '%s.jpg' % code)

				# pxy file ======================================================
				aprvPxyFile = '%s/ttv_%s_%s_%s_rig_mr.%s' % (approvedPath, assetType, parent, variation, self.fileExt)
				masterPxyFile = '%s/ttv_%s_%s_%s_rig_mr.MASTER.%s' % (publishPath, assetType, parent, variation, self.fileExt)

				maxPublishPxyFile = self.findMaxVersion(publishPath, 'ttv_%s_%s_%s_rig_pxy' % (assetType, parent, variation), self.fileExt)

				if maxPublishPxyFile : 
					publishPxyFile = '%s/%s' % (publishPath, maxPublishPxyFile)

				# mr file ========================================================
				aprvFile = '%s/ttv_%s_%s_%s_rig_mr.%s' % (approvedPath, assetType, parent, variation, self.fileExt)
				masterFile = '%s/ttv_%s_%s_%s_rig_mr.MASTER.%s' % (publishPath, assetType, parent, variation, self.fileExt)

				maxPublishFile = self.findMaxVersion(publishPath, 'ttv_%s_%s_%s_rig_mr' % (assetType, parent, variation), self.fileExt)

				if maxPublishFile : 
					publishFile = '%s/%s' % (publishPath, maxPublishFile)

				# ================================================================

				# check apprv -> master -> publishVersion 
				if os.path.exists(aprvPxyFile) : 
					pullFile = aprvPxyFile
					fileType = 'approved'

				elif os.path.exists(masterPxyFile) : 
					pullFile = masterPxyFile
					fileType = 'master'

				elif os.path.exists(publishPxyFile) : 
					pullFile = publishPxyFile
					fileType = 'publish'

				elif os.path.exists(aprvFile) : 
					pullFile = aprvFile
					fileType = 'approved'

				elif os.path.exists(masterFile) : 
					pullFile = masterFile
					fileType = 'master'

				elif os.path.exists(publishFile) : 
					pullFile = publishFile
					fileType = 'publish'

				else : 
					print '%s has no assosiated file' % code

			else : 
				print 'Missing field %s %s %s' % (assetType, parent, variation)


			assetInfo[code] = {'id': id, 'code': code, 'assetType': assetType, 'parent': parent, 'variation': variation, 'pullFile': pullFile, 'fileType': fileType, 'aprvFile': aprvFile, 'masterFile': masterFile, 'publishPath': publishPath, 'aprvPxyFile': aprvPxyFile, 'masterPxyFile': masterPxyFile, 'thumbnailFile': thumbnailFile, 'image': image}

		return assetInfo


			# U:\projects\ttv\assets\approved\charmain\angela\base\rig\maya\ttv_charmain_angela_base_rig_mr.v004.ma
			# "U:\projects\ttv\assets\publish\charmain\angela\base\rig\maya\ttv_charmain_angela_base_rig_mr.MASTER.ma"


	# set UI =======================================================================================================


	def setUI(self, mode) : 

		if mode == 'shotgun' : 

			if self.sceneInfo : 
				self.setSceneInfo(self.sceneInfo)

			if self.shotAssets : 
				self.downloadThumbnail()
				self.listShotAsset(self.shotAssets)

		if mode == 'browser' : 

			if self.assetInfo : 
				self.downloadThumbnail()
				self.setFilter()				
				self.listAllAsset()



	def setSceneInfo(self, sceneInfo) : 
		# set UI shot Info
		self.ui.step_label.setText(sceneInfo['step'])
		self.ui.episode_label.setText(sceneInfo['episode'])
		self.ui.sequence_label.setText(sceneInfo['sequence'])
		self.ui.shot_label.setText(sceneInfo['shot'])


	def listShotAsset(self, assets) : 

		self.ui.main_listWidget.clear()
		aprvCount = 0
		masterCount = 0
		publishCount = 0
		missingCount = 0
		i = 0
		info = []
		addIcon = 0

		if self.ui.thumbnail_checkBox.isChecked() : 
			addIcon = 1


		for each in assets : 
			
			if each['name'] in self.assetInfo.keys() : 
				pullFile = self.assetInfo[each['name']]['pullFile']
				fileType = self.assetInfo[each['name']]['fileType']
				# display = '%s - %s' % (self.assetInfo[each['name']]['code'], fileType)
				display = '%s' % (self.assetInfo[each['name']]['code'])
				color = [100, 0, 0]
				thumbnailFile = self.assetInfo[each['name']]['thumbnailFile']
				iconPath = self.noPreviewIcon

				if os.path.exists(thumbnailFile) : 
					iconPath = thumbnailFile

				if fileType == 'approved' : 
					color = [0, 0, 0]
					aprvCount+=1

				if fileType == 'master' : 
					color = [0, 0, 0]
					masterCount+=1

				if fileType == 'publish' : 
					color = [0, 0, 0]
					publishCount+=1

				if fileType == 'No File' : 
					print each['name']
					print 'Approved file missing %s' % self.assetInfo[each['name']]['aprvFile']
					print 'Master file missing %s' % self.assetInfo[each['name']]['masterFile']
					print '------------------------' 
					missingCount+=1

				self.addListWidgetItem('main_listWidget', display, iconPath, color, addIcon, size = 90)

			i+=1


		info.append('	%s 	approved asset' % aprvCount)
		info.append('	%s 	master asset' % masterCount)
		info.append('	%s 	publish asset' % publishCount)
		info.append('	-----------------------------------')
		info.append('	%s/%s available (%s Missing)' % ((aprvCount + masterCount + publishCount), i, missingCount))
		info.append('')
		displayInfo = ('\n\r').join(info)

		print '%s asset missing' % missingCount

		self.ui.information_label.setText(displayInfo)



	def setFilterSignal1(self) : 

		if self.ui.type_checkBox.isChecked() : 
			self.ui.type_comboBox.currentIndexChanged.connect(self.listAllAsset)

		else : 
			self.ui.type_comboBox.currentIndexChanged.disconnect(self.listAllAsset)

		self.refreshUI()

	def setFilterSignal2(self) : 

		if self.ui.parent_checkBox.isChecked() : 
			self.ui.parent_comboBox.currentIndexChanged.connect(self.listAllAsset)

		else : 
			self.ui.parent_comboBox.currentIndexChanged.disconnect(self.listAllAsset)

		self.refreshUI()


	def setFilterSignal3(self) : 

		if self.ui.variation_checkBox.isChecked() : 
			self.ui.variation_comboBox.currentIndexChanged.connect(self.listAllAsset)

		else : 
			self.ui.variation_comboBox.currentIndexChanged.disconnect(self.listAllAsset)

		self.refreshUI()


	def setFilter(self) : 

		assetTypes = []
		parents = []
		variations = []

		for each in self.assetInfo : 
			assetType = self.assetInfo[each]['assetType']
			parent = self.assetInfo[each]['parent']
			variation = self.assetInfo[each]['variation']

			if not assetType in assetTypes : 
				assetTypes.append(assetType)

			if not parent in parents : 
				parents.append(parent)

			if not variation in variations : 
				variations.append(variation)

		self.ui.type_comboBox.clear()

		for each in assetTypes : 
			self.ui.type_comboBox.addItem(each)

		self.ui.parent_comboBox.clear()

		for each in parents : 
			self.ui.parent_comboBox.addItem(each)

		self.ui.variation_comboBox.clear()

		for each in variations : 
			self.ui.variation_comboBox.addItem(each)



	def listAllAsset(self) : 
		assetInfo = self.assetInfo
		info = []
		self.ui.information_label.setText('Working ...')

		# keyword in search field
		kw = str(self.ui.search_lineEdit.text())
		assetTypeKw = str(self.ui.type_comboBox.currentText())
		parentKw = str(self.ui.parent_comboBox.currentText())
		variationKw = str(self.ui.variation_comboBox.currentText())

		self.ui.main_listWidget.clear()
		color = [100, 0, 0]
		assetCount = 0
		aprvCount = 0
		masterCount = 0
		publishCount = 0
		missingCount = 0
		addIcon = 0

		if self.ui.thumbnail_checkBox.isChecked() : 
			addIcon = 1

		for each in sorted(assetInfo.keys()) : 
			fileType = assetInfo[each]['fileType']
			assetType = assetInfo[each]['assetType']
			parent = assetInfo[each]['parent']
			variation = assetInfo[each]['variation']
			thumbnailFile = assetInfo[each]['thumbnailFile']
			iconPath = self.noPreviewIcon

			if os.path.exists(thumbnailFile) : 
				iconPath = thumbnailFile

			if not self.ui.type_checkBox.isChecked() : 
				assetTypeKw = assetType

			if not self.ui.parent_checkBox.isChecked() : 
				parentKw = parent

			if not self.ui.variation_checkBox.isChecked() : 
				variationKw = variation

			if kw in each : 			
				if assetTypeKw == assetType :  
					if parentKw == parent : 
						if variationKw == variation : 
							if fileType == 'approved' : 
								color = [0, 0, 0]
								aprvCount+=1

							if fileType == 'master' : 
								color = [0, 0, 0]
								masterCount+=1

							if fileType == 'publish' : 
								color = [0, 0, 0]
								publishCount+=1

							if fileType == 'No File' : 
								color = [100, 0, 0]
								missingCount+=1

							self.addListWidgetItem('main_listWidget', each, iconPath, color, addIcon, 90)
							assetCount+=1

		info.append('	%s	assets' % assetCount)
		info.append('	---------------------------------')
		info.append('	%s 	approved asset' % aprvCount)
		info.append('	%s	master asset' % masterCount)
		info.append('	%s	publish asset' % publishCount)
		info.append('	%s	missing asset' % missingCount)
		display = ('\n\r').join(info)

		self.ui.information_label.setText(display)


	def showMenu(self,pos):
		if self.ui.main_listWidget.currentItem() : 
			menu=QtGui.QMenu(self)
			menu.addAction('Show in Explorer')
			
			menu.popup(self.ui.main_listWidget.mapToGlobal(pos))
			result = menu.exec_(self.ui.main_listWidget.mapToGlobal(pos))

			if result : 
				self.menuCommand(result.text(), 'main_listWidget')



	def menuCommand(self, command, listWidget) : 
		cmd = 'self.ui.%s.currentItem().text()' % listWidget
		item = str(eval(cmd))

		if ' - ' in item : 
			item = item.split(' - ')[0]

		heroFile = self.assetInfo[item]['pullFile']

		if heroFile : 
			path = heroFile.replace('/', '\\')

		else : 
			path = self.assetInfo[item]['publishPath'].replace('/', '\\')
			print path

		subprocess.Popen(r'explorer /select,"%s"' % path)
			


	# signal call button command
	def doCreateReference(self) : 
		readAssetList = self.getAllListWidgetItem('main_listWidget')

		# for each in readAssetList : 





	# utils =================================================================

	def getAllListWidgetItem(self, widget) : 
		count = eval('self.ui.%s.count()' % widget)
		items = []

		for i in range(count) : 
			item = eval('self.ui.%s.item(i).text()' % widget)

			items.append(item)


		return items


	def findMaxVersion(self, path, fileName, ext) : 
		files = fileUtils.listFile(path, ext)

		max = 0
		targetFile = str()

		for each in files : 
			if fileName in each : 
				version = each.split('.')[-2].replace('v', '')
				if version.isdigit() : 
					num = int(version)
					if num > max : 
						max = num
						targetFile = each
					
		return targetFile


	def addListWidgetItem(self, listWidget, text, iconPath, color, addIcon = 1, size = 90) : 
 		
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
		cmd = 'QtGui.QListWidgetItem(self.ui.%s)' % listWidget
		item = eval(cmd)

		if addIcon : 
			item.setIcon(icon)
			cmd2 = 'self.ui.%s.setIconSize(QtCore.QSize(%s, %s))' % (listWidget, size, size)
			eval(cmd2)

		item.setText(text)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
		
		# QtGui.QApplication.processEvents()