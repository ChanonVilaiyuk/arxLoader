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
from arxLoader import ui3 as ui
reload(ui)

from arxLoader import mayaHook as hook
reload(hook)

from arxLoader import customWidget as cw
reload(cw)

from tools.utils import config, fileUtils
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
		self.itemColor = [0, 0, 0]
		self.textItemColor = [[200, 200, 200], [120, 120, 120], [100, 100, 100]]
		self.sceneInfo = None
		self.shotAssets = None
		self.viewMode = ['view1_icon.png', 'view2_icon.png', 'view3_icon.png', 'view4_icon.png']
		self.customWidgetMode = [0]
		self.sgAssetLists = []
		self.sgShotId = dict()

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
		self.ui.showSceneAsset_checkBox.stateChanged.connect(self.refreshUI)
		self.ui.main_listWidget.customContextMenuRequested.connect(self.showMenu)
		self.ui.thumbnail_checkBox.stateChanged.connect(self.refreshUI)
		self.ui.selectedReference_checkBox.stateChanged.connect(self.setReferenceButton)
		self.ui.viewMode_comboBox.currentIndexChanged.connect(self.refreshUI)
		self.ui.showMayaAsset_checkBox.stateChanged.connect(self.refreshUI)
		self.ui.uploadAsset_pushButton.clicked.connect(self.uploadShotgun)
		self.ui.asset_tabWidget.currentChanged.connect(self.listAllAsset)


	def initFunctions(self) : 
		# set the correct layout window
		self.loadData()
		self.setWindowMode()


	def test(self) : 
		print 'tab call'
		


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
			buttonText = 'Create All Reference'
			value3 = False


		if self.ui.manualBrowser_radioButton.isChecked() : 
			value = True
			# w = 850
			# h = 640
			# lPos = 620
			w = 550
			h = 640
			lPos = 320
			text = 'All Asset List'
			value2 = False
			mode = 'browser'
			buttonText = 'Create Reference'
			value3 = False
		
		# show / hide
		self.ui.add_pushButton.setVisible(value3)
		self.ui.remove_pushButton.setVisible(value3)
		self.ui.clear_pushButton.setVisible(value3)
		self.ui.search_frame.setVisible(value)
		self.ui.filter_frame.setVisible(value3)
		# self.ui.list_frame.setVisible(value3)
		self.ui.main_label.setText(text)
		self.ui.projectInfo_frame.setVisible(value2)
		self.ui.selectedReference_checkBox.setVisible(value2)
		self.ui.showSceneAsset_checkBox.setVisible(value)
		self.ui.type_comboBox.setVisible(value3)
		self.ui.type_checkBox.setVisible(value3)
		self.ui.uploadAsset_pushButton.setVisible(value3)
		self.ui.showMayaAsset_checkBox.setVisible(value2)
		self.ui.asset_tabWidget.setVisible(value)


		# resizing window
		# self.ui.frame.resize(w, h)
		# self.resize(w + 14, h + 14)
		# self.ui.logo_label.setGeometry(lPos, 10, 221, 61)
		self.setLogo()
		self.setViewComboBox()


		# button text
		self.ui.createReference_pushButton.setText(buttonText)

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
		self.ui.information_label.setText('Processing ...')
		self.ui.extra_label.setVisible(False)
		QtGui.QApplication.processEvents()
		self.setUI(mode)



	def setReferenceButton(self) : 

		if self.ui.selectedReference_checkBox.isChecked() : 
			self.ui.createReference_pushButton.setText('Create Selected Reference')

		else : 
			self.ui.createReference_pushButton.setText('Create All References')



	def setViewComboBox(self) : 
		self.ui.viewMode_comboBox.clear()
		self.ui.viewMode_comboBox.currentIndexChanged.disconnect(self.refreshUI)

		for i in range(len(self.viewMode)) : 
			iconPath = '%s/%s' % (self.iconPath, self.viewMode[i])
			self.ui.viewMode_comboBox.addItem('')
			icon = QtGui.QIcon()
			icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.ui.viewMode_comboBox.setItemIcon(i, icon)

		# default mode
		self.ui.viewMode_comboBox.setCurrentIndex(2)


		self.ui.viewMode_comboBox.currentIndexChanged.connect(self.refreshUI)



	# load data ==================================================================================================


	def loadData(self) : 
		# load scene name
		sceneName = hook.getSceneName()

		if sceneName : 
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

		if len(eles) >= 6 : 
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

		if sceneInfo : 
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
						self.sgShotId = {'code': shotCode, 'id': eachShot['id']}

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

				# check type > parent >

				# pxy file ======================================================
				aprvPxyFile = '%s/ttv_%s_%s_%s_rig_mr.%s' % (approvedPath, assetType, parent, variation, self.fileExt)
				masterPxyFile = '%s/ttv_%s_%s_%s_rig_mr.MASTER.%s' % (publishPath, assetType, parent, variation, self.fileExt)

				maxPublishPxyFile = self.findMaxVersion(publishPath, 'ttv_%s_%s_%s_rig_pxy' % (assetType, parent, variation), self.fileExt)

				if maxPublishPxyFile : 
					publishPxyFile = '%s/%s' % (publishPath, maxPublishPxyFile)

				# mr file ========================================================
				aprvFile = '%s/ttv_%s_%s_%s_rig_mr.%s' % (approvedPath, assetType, parent, variation, self.fileExt)
				masterFile = '%s/ttv_%s_%s_%s_rig_mr.MASTER.%s' % (publishPath, assetType, parent, variation, self.fileExt)
				masterFile2 = '%s/ttv_%s_%s_%s_rig_mr_MASTER.%s' % (publishPath, assetType, parent, variation, self.fileExt)

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

				elif os.path.exists(masterFile2) : 
					pullFile = masterFile2
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

			else : 
				self.ui.main_listWidget.clear()
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
		sgPullFiles = []
		addIcon = 0
		textColors = self.textItemColor
		message = str()
		sgAssets = []

		scenePathInfo = self.getSceneAssets()

		assetInfo = self.assetInfo


		if self.ui.thumbnail_checkBox.isChecked() : 
			addIcon = 1


		for each in assets : 
			
			if each['name'] in self.assetInfo.keys() : 
				pullFile = self.assetInfo[each['name']]['pullFile']
				aprvFile = self.assetInfo[each['name']]['aprvFile']
				masterFile = self.assetInfo[each['name']]['masterFile']
				publishPath = self.assetInfo[each['name']]['publishPath']
				aprvPxyFile = self.assetInfo[each['name']]['aprvPxyFile']
				masterPxyFile = self.assetInfo[each['name']]['masterPxyFile']
				fileType = self.assetInfo[each['name']]['fileType']
				# display = '%s - %s' % (self.assetInfo[each['name']]['code'], fileType)
				display = '%s' % (self.assetInfo[each['name']]['code'])
				thumbnailFile = self.assetInfo[each['name']]['thumbnailFile']
				
				color = [100, 0, 0]
				iconPath = self.noPreviewIcon
				sgAssets.append(display)
				sgPullFiles.append(pullFile)
				fileCheckList = [pullFile, aprvFile, masterFile, publishPath, aprvPxyFile, masterPxyFile]

				numberDisplay = 'In scene x 0'
				number = 0

				for checkFile in fileCheckList : 
					if checkFile in scenePathInfo.keys() : 
						number = scenePathInfo[checkFile]['number']


					
				if number : 
					numberDisplay = 'In scene x %s' % number

				textColors[2] = [200, 100, 100]

				if number > 0 : 
					textColors[2] = [100, 200, 0]

				if number == 0 : 
					textColors[2] = [200, 200, 0]

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

				self.addListWidgetItem(display, fileType, numberDisplay, iconPath, color, textColors, addIcon, size = 90)

				if not self.assetInfo[each['name']] in self.sgAssetLists : 
					self.sgAssetLists.append(self.assetInfo[each['name']])

			i+=1

		# list not in shotgun ==============================================================================================

		self.ui.uploadAsset_pushButton.setVisible(False)

		if self.ui.showMayaAsset_checkBox.isChecked() : 
			
			assetCount = 0

			for each in sorted(assetInfo.keys()) : 
				display = each
				fileType = assetInfo[each]['fileType']
				pullFile = assetInfo[each]['pullFile']
				aprvFile = assetInfo[each]['aprvFile']
				masterFile = assetInfo[each]['masterFile']
				publishPath = assetInfo[each]['publishPath']
				aprvPxyFile = assetInfo[each]['aprvPxyFile']
				masterPxyFile = assetInfo[each]['masterPxyFile']

				fileCheckList = [pullFile, aprvFile, masterFile, publishPath, aprvPxyFile, masterPxyFile]



				thumbnailFile = assetInfo[each]['thumbnailFile']
				iconPath = self.noPreviewIcon
				numberDisplay = 'In scene x 0'
				number = 0
				assetNo = 100

				# if maya asset not already in the list
				if not display in sgAssets : 

					for checkFile in fileCheckList : 

						if checkFile in scenePathInfo.keys() : 
							number = scenePathInfo[checkFile]['number']


					if number : 
						numberDisplay = 'In scene x %s' % number

						if os.path.exists(thumbnailFile) : 
							iconPath = thumbnailFile


						if fileType == 'approved' : 
							color = [200, 100, 0]
							aprvCount+=1

						if fileType == 'master' : 
							color = [200, 100, 0]
							masterCount+=1

						if fileType == 'publish' : 
							color = [200, 100, 0]
							publishCount+=1

						if fileType == 'No File' : 
							color = [100, 0, 0]
							missingCount+=1
						

						textColors[2] = [200, 100, 100]

						if number > 0 : 
							textColors[2] = [100, 200, 0]

						if number == 0 : 
							textColors[2] = [200, 200, 0]

						self.addListWidgetItem(display, fileType, numberDisplay, iconPath, color, textColors, addIcon, 90)
						assetCount+=1

						if not assetInfo[each] in self.sgAssetLists : 
							self.sgAssetLists.append(assetInfo[each])

				if assetCount > 0 : 
					message = '%s assets Not in shotgun' % assetCount
					self.ui.uploadAsset_pushButton.setVisible(True)

				if assetCount == 0 : 
					message = 'All assets in shotgun'


		if not assets : 
			# self.ui.information_label.setText('No Shotgun data')
			self.ui.extra_label.setVisible(True)
			self.ui.extra_label.setText('No Shotgun data')
			self.ui.extra_label.setStyleSheet('background-color: rgb(200, 40, 0)')

		else : 
			self.ui.extra_label.setText('')

		info.append('	%s 	approved asset' % aprvCount)
		info.append('	%s 	master asset' % masterCount)
		info.append('	%s 	publish asset' % publishCount)
		info.append('	-----------------------------------')
		info.append('	%s/%s available (%s Missing)' % ((aprvCount + masterCount + publishCount), i, missingCount))
		info.append('')
		info.append(message)
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

		filterInfo = dict()

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

			if not assetType in filterInfo.keys() : 
				filterInfo[assetType] = []

			filterInfo[assetType].append(parent)

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
		currentTab = self.ui.asset_tabWidget.currentIndex()
		currentTabName = str(self.ui.asset_tabWidget.tabText(currentTab))


		# get in scene reference
		scenePathInfo = self.getSceneAssets()
		print 'in scene %s' % scenePathInfo

		self.ui.main_listWidget.clear()
		color = [100, 0, 0]
		assetCount = 0
		aprvCount = 0
		masterCount = 0
		publishCount = 0
		missingCount = 0
		addIcon = 0

		textColors = self.textItemColor


		if self.ui.thumbnail_checkBox.isChecked() : 
			addIcon = 1

		for each in sorted(assetInfo.keys()) : 
			fileType = assetInfo[each]['fileType']
			pullFile = assetInfo[each]['pullFile']
			aprvFile = assetInfo[each]['aprvFile']
			masterFile = assetInfo[each]['masterFile']
			publishPath = assetInfo[each]['publishPath']
			aprvPxyFile = assetInfo[each]['aprvPxyFile']
			masterPxyFile = assetInfo[each]['masterPxyFile']
			assetType = assetInfo[each]['assetType']
			parent = assetInfo[each]['parent']
			variation = assetInfo[each]['variation']
			thumbnailFile = assetInfo[each]['thumbnailFile']
			fileCheckList = [pullFile, aprvFile, masterFile, publishPath, aprvPxyFile, masterPxyFile]
			iconPath = self.noPreviewIcon
			numberDisplay = 'In scene x 0'
			number = 0
			assetNo = 100



			for checkFile in fileCheckList : 
				if checkFile in scenePathInfo.keys() : 
					number = scenePathInfo[checkFile]['number']

			if number : 
				numberDisplay = 'In scene x %s' % number

			if os.path.exists(thumbnailFile) : 
				iconPath = thumbnailFile

			if not self.ui.type_checkBox.isChecked() : 
				assetTypeKw = assetType

			if not self.ui.parent_checkBox.isChecked() : 
				parentKw = parent

			if not self.ui.variation_checkBox.isChecked() : 
				variationKw = variation

			if self.ui.showSceneAsset_checkBox.isChecked() : 
				assetNo = number

			if currentTabName == 'all' : 
				assetTypeKw = assetType

			else : 
				assetTypeKw = currentTabName


			if kw in each : 			
				if assetTypeKw == assetType :  
					if parentKw == parent : 
						if variationKw == variation : 
							if assetNo > 0 : 
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
								

								textColors[2] = [200, 100, 100]

								if number > 0 : 
									textColors[2] = [100, 200, 0]

								if number == 0 : 
									textColors[2] = [200, 200, 0]

								self.addListWidgetItem(each, fileType, numberDisplay, iconPath, color, textColors, addIcon, 90)
								assetCount+=1

		self.ui.extra_label.setText('')

		info.append('	%s	assets' % assetCount)
		info.append('	---------------------------------')
		info.append('	%s 	approved asset' % aprvCount)
		info.append('	%s	master asset' % masterCount)
		info.append('	%s	publish asset' % publishCount)
		info.append('	%s	missing asset' % missingCount)
		display = ('\n\r').join(info)

		self.ui.information_label.setText(display)


	def showMenu(self,pos):
		menu1, state = self.getMenu1()
		if self.ui.main_listWidget.currentItem() : 
			menu=QtGui.QMenu(self)
			menu.addAction(menu1)
			menu.setEnabled(state)
			
			menu.popup(self.ui.main_listWidget.mapToGlobal(pos))
			result = menu.exec_(self.ui.main_listWidget.mapToGlobal(pos))

			if result : 
				self.menuCommand(result.text(), 'main_listWidget')

	# open in explorer command
	def getMenu1(self) : 
		text = self.getSelectedWidgetItem(1)
		item = text[-1]
		menu = None

		heroFile = self.assetInfo[item]['pullFile']

		if heroFile : 
			path = heroFile.replace('/', '\\')

		else : 
			path = self.assetInfo[item]['publishPath'].replace('/', '\\')
			
		if os.path.exists(path) : 
			menu = 'Open in Explorer'
			status = True

		else : 
			menu = 'Path not exists'
			status = False

		return menu, status


	def menuCommand(self, command, listWidget) : 
		# cmd = 'self.ui.%s.currentItem().text()' % listWidget
		# item = str(eval(cmd))

		item = self.getSelectedWidgetItem(1)[0]

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

		# check allow multiple asset
		multipleAsset = True

		# get what exists in the scene
		scenePathInfo = self.getSceneAssets()

		# check create all or selected
		selOnly = self.ui.selectedReference_checkBox.isChecked()

		# read from shotgun

		if self.ui.shotgun_radioButton.isChecked() : 

			if selOnly : 
				readAssetList = self.getSelectedWidgetItem(1)

			else : 
				readAssetList = self.getAllListWidgetItem()

		if self.ui.manualBrowser_radioButton.isChecked() : 
			readAssetList = self.getSelectedWidgetItem(1)

		if readAssetList : 

			for each in readAssetList : 
				assetName = self.assetInfo[each]['code']
				namespace = assetName
				path = self.assetInfo[each]['pullFile']

				if path : 
					if not path in scenePathInfo.keys() : 
						result = hook.createReference(namespace, path)

					else : 
						# asking if want to create another reference
						title = 'Confirm create multiple reference'
						description = '%s already exists in the scene, do you still want to create reference?' % assetName
						result = self.messageBox(title, description)

						if result == QtGui.QMessageBox.Ok : 
							result = hook.createReference(namespace, path)

				else : 
					if selOnly : 
						title = 'Asset not exists'
						dialog = '%s has no approved, MASTER or published file' % assetName
						self.completeDialog(title, dialog)


		self.refreshUI()

		# read from list
		# if self.ui.manualBrowser_radioButton.isChecked() : 
		# 	readAssetList = self.getSelectedWidgetItem(1)

		

	'''
	this function get all reference in the scene and return path and number of references
	'''

	def getSceneAssets(self) : 
		allRefs = hook.getAllReferencePath()
		paths = []
		sceneAssetPathInfo = dict()

		for each in allRefs : 
			namespace = hook.getNamespace(each)
			path = each.split('{')[0]
			number = 1
			display = str()
			fileType = str()

			# get display by extracting file name
			try : 
				display = ('_').join(os.path.basename(path).split('_')[2:4])
			except : 
				pass

			if not path in paths : 
				paths.append(path)

			else : 
				number = sceneAssetPathInfo[path]['number'] + 1


			# get file type
			# approved ==================================
			if '/approved/' in path : 
				fileType = 'approved'

			if '/publish/' in path : 
				# master ==============================
				if 'MASTER.ma' in path : 
					fileType = 'master'

				# publish ==============================
				else : 
					fileType = 'publish'

			# get thumbnail


			sceneAssetPathInfo[path] = {'namespace': namespace, 'number': number, 'display': display, 'fileType': fileType}

		return sceneAssetPathInfo



	''' upload asset not in the list to shotgun '''

	def uploadShotgun(self) : 

		assets = []
		shotID = self.sgShotId['id']

		for each in self.sgAssetLists : 
			assets.append({'type': 'Asset', 'id': each['id']})

		result = self.messageBox('Confirm', 'Update assets list to Shotgun?')

		if result : 
			self.ui.information_label.setText('Updating shotgun ...')
			QtGui.QApplication.processEvents()

			data = {'assets': assets}
			result2 = sgUtils.sg.update('Shot', shotID, data)

			if result2 : 
				self.loadData()
				self.refreshUI()
				self.completeDialog('Complete', 'Update assets list to shotgun complete')


	# utils =================================================================

	def getSelectedWidgetItem(self, lineText) : 
		mode = self.ui.viewMode_comboBox.currentIndex()
		allItems = []

		if mode in self.customWidgetMode : 
			items = self.ui.main_listWidget.selectedItems()

			for item in items : 
				customWidget = self.ui.main_listWidget.itemWidget(item)

				if lineText == 1 : 
					text = customWidget.text1()

				if lineText == 2 : 
					text = customWidget.text2()

				if lineText == 3 : 
					text = customWidget.text3()
				
				allItems.append(text)

		else : 
			items = self.ui.main_listWidget.selectedItems()

			for item in items : 
				if lineText == 1 : 
					text = str(item.text()).split('\n\r')[0]

					allItems.append(text)

		return allItems


	def getAllListWidgetItem(self) : 
		mode = self.ui.viewMode_comboBox.currentIndex()
		count = self.ui.main_listWidget.count()
		items = []

		for i in range(count) : 
			item = self.ui.main_listWidget.item(i)

			if mode in self.customWidgetMode : 
				customWidget = self.ui.main_listWidget.itemWidget(item)
				text1 = customWidget.text1()

			else : 
				text1 = str(self.ui.main_listWidget.item(i).text()).split('\n\r')[0]

			items.append(text1)


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


	def addListWidgetItem(self, text1, text2, text3, iconPath, color, textColors, addIcon = 1, size = 90) : 

		mode = self.ui.viewMode_comboBox.currentIndex()

		# list mode details
		if mode == 0 : 		
			self.ui.main_listWidget.setFlow(QtGui.QListView.TopToBottom)
			self.ui.main_listWidget.setViewMode(QtGui.QListView.ListMode)
			self.ui.main_listWidget.setGridSize(QtCore.QSize(66, 66))
			self.ui.main_listWidget.setProperty("isWrapping", False)
			self.addListWidgetItemListMode(text1, text2, text3, iconPath, color, textColors, addIcon, size)


		# list mode small details
		if mode == 1 : 
			self.ui.main_listWidget.setFlow(QtGui.QListView.TopToBottom)
			self.ui.main_listWidget.setViewMode(QtGui.QListView.ListMode)
			self.ui.main_listWidget.setGridSize(QtCore.QSize(240, 32))
			self.ui.main_listWidget.setProperty("isWrapping", True)
			self.addListWidgetItemSmallListMode(text1, text3, iconPath, color, textColors, addIcon, 40)


		# icon mode 
		if mode == 2 : 
			self.ui.main_listWidget.setFlow(QtGui.QListView.LeftToRight)
			self.ui.main_listWidget.setViewMode(QtGui.QListView.IconMode)
			self.ui.main_listWidget.setProperty("isWrapping", True)
			self.ui.main_listWidget.setGridSize(QtCore.QSize(120, 120))
			self.addListWidgetItemIconMode(text1, text3, iconPath, color, textColors, addIcon, size)


		# text only mode
		if mode == 3 : 
			self.ui.main_listWidget.setFlow(QtGui.QListView.TopToBottom)
			self.ui.main_listWidget.setViewMode(QtGui.QListView.ListMode)
			self.ui.main_listWidget.setProperty("isWrapping", True)
			self.ui.main_listWidget.setGridSize(QtCore.QSize(240, 14))
			self.addListWidgetItemTextOnly(text1, color)
		
		# QtGui.QApplication.processEvents()


	def addListWidgetItemListMode(self, text1, text2, text3, iconPath, color, textColors, addIcon = 1, size = 90) : 

		myCustomWidget = cw.customQWidgetItem()
		myCustomWidget.setText1(text1)
		myCustomWidget.setText2(text2)
		myCustomWidget.setText3(text3)
		# myCustomWidget.setText4(text4)

		myCustomWidget.setTextColor1(textColors[0])
		myCustomWidget.setTextColor2(textColors[1])
		myCustomWidget.setTextColor3(textColors[2])

		if addIcon : 
			myCustomWidget.setIcon(iconPath, size)

		item = QtGui.QListWidgetItem(self.ui.main_listWidget)

		item.setSizeHint(myCustomWidget.sizeHint())
		self.ui.main_listWidget.addItem(item)
		self.ui.main_listWidget.setItemWidget(item, myCustomWidget)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))



	def addListWidgetItemIconMode(self, text1, text2, iconPath, color, textColors, addIcon = 1, size = 90) : 
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)

		font = QtGui.QFont()
		font.setPointSize(9)
		font.setBold(False)
		self.ui.main_listWidget.setFont(font)

		text = '%s\n\r%s' % (text1, text2)

		item = QtGui.QListWidgetItem(self.ui.main_listWidget)
		item.setIcon(icon)
		item.setText(text)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
		self.ui.main_listWidget.setIconSize(QtCore.QSize(size, size))



	def addListWidgetItemSmallListMode(self, text1, text2, iconPath, color, textColors, addIcon = 1, size = 90) : 

		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)

		font = QtGui.QFont()
		font.setPointSize(9)
		font.setBold(False)
		self.ui.main_listWidget.setFont(font)

		text = '%s\n\r%s' % (text1, text2)

		item = QtGui.QListWidgetItem(self.ui.main_listWidget)
		item.setIcon(icon)
		item.setText(text)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
		self.ui.main_listWidget.setIconSize(QtCore.QSize(size, size))
		


	def addListWidgetItemTextOnly(self, text1, color) : 

		font = QtGui.QFont()
		font.setPointSize(9)
		font.setWeight(75)
		font.setBold(False)
		self.ui.main_listWidget.setFont(font)
		
		item = QtGui.QListWidgetItem(self.ui.main_listWidget)

		item.setText(text1)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))


	def messageBox(self, title, description) : 
		result = QtGui.QMessageBox.question(self,title,description ,QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

		return result


	def completeDialog(self, title, dialog) : 
		QtGui.QMessageBox.information(self, title, dialog, QtGui.QMessageBox.Ok)

		





