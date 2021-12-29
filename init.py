"""
Author: Efthymis B.
Last Modified: 03/11/2021

Python 2.7 only
Katana Catalog Script, tested on 4.0v5 (Windows)
To be placed in a Katana startup script, e.g. ~/.katana/init.py
"""

def onTabCreated(objectHash, tab):
    """
    Callback that is called when a tab has been added to a window in Katana's
    UI.

    @type objectHash: C{object} or C{None}
    @type tab: C{UI4.Tabs.BaseTab.BaseTab}
    @param objectHash: An arbitrary object that was passed as an argument to
        the C{Callbacks.ExecuteCallbacksForType()} function, or C{None} if no
        argument was passed.
    @param tab: The tab that was added.
    """
    from functools import partial
    import NodegraphAPI
    import AssetAPI
    import os
    import UI4.App.Tabs

    if UI4.App.Tabs.GetTabTypeName(tab) != 'Catalog':
        return

    catalogTab = tab
    catalogWidget = catalogTab.getCatalogWidget()
    suffix = "Master"

    def get_items(selection):
        if selection == catalogWidget.LIST_ALL:
            selectedItems = catalogWidget.getItems(selection)
            return selectedItems if selectedItems else UI4.Widgets.MessageBox.Information('Information', 'Catalog is empty.')
        elif selection == catalogWidget.LIST_SELECTED:
            selectedItems = catalogWidget.getItems(selection)
            return selectedItems if selectedItems else UI4.Widgets.MessageBox.Information('Information', 'No selection.')
        elif selection == catalogWidget.LIST_LOCKED:
            selectedItems = catalogWidget.getItems(selection)
            return selectedItems if selectedItems else UI4.Widgets.MessageBox.Information('Information', 'No Locked images.')

    def on_mergedExport_triggered(selection):
        selectedItems = get_items(selection)
        if selectedItems:
            filePath = UI4.Util.AssetId.BrowseForAsset('', 'Export Catalog', True, args)
            filePath = os.path.splitext(filePath)[0]
            if not os.access(os.path.dirname(filePath), os.W_OK):
                UI4.Widgets.MessageBox.Information('Information', 'Export location {} does not have write permissions.'.format(os.path.dirname(filePath)))
            frameNumber = 1
            fileNameList = []
            itemIndex = []
            for catalogItem in selectedItems:
                if catalogItem.getIndex() in itemIndex:
                    continue
                else:
                    itemIndex.append(catalogItem.getIndex())
                    AOVlist = []
                    layerViews = catalogItem.getLayerViews()
                    for layerView in layerViews:
                        if deleteIndividualAOVs.isChecked():
                            name = filePath + '_{}.{}.exr'.format(layerView[0], str(frameNumber).zfill(4))
                        else:
                            # If 'Delete Individual AOVs' is not Checked, create a folder per AOV
                            name = os.path.join(filePath + '_{}'.format(str(layerView[0])), os.path.basename(filePath) +
                                                '_{}.{}.exr'.format(layerView[0], str(frameNumber).zfill(4)))
                            if not os.path.exists(os.path.dirname(name)):
                                os.mkdir(os.path.dirname(name))
                        buf = catalogItem.getBuffer(layerView)
                        fileNameList.append(name)
                        AOVlist.append([name, layerView[0]])
                        buf.writeToDisk(name, imageOptions, 1, 0, False)

                    exrCombine = os.sys.exec_prefix + '\\ExrCombine.exe '
                    for imageFIle, AOV in AOVlist:
                        # For each AOV append the respective file path and AOV name
                        exrCombine += imageFIle + ' ' + AOV + ' '

                    exrCombine += filePath + '_{}.{}.exr'.format(suffix, str(frameNumber).zfill(4))
                    frameNumber += 1
                    os.system(exrCombine)
                    # If 'Delete Individual AOVs' is Checked, delete the original files
                    if deleteIndividualAOVs.isChecked():
                        for item in AOVlist:
                            os.remove(item[0])

    def on_primaryExport_triggered(selection):
        selectedItems = get_items(selection)
        if selectedItems:
            filePath = UI4.Util.AssetId.BrowseForAsset('', 'Export Catalog', True, args)
            filePath = os.path.splitext(filePath)[0]
            if not os.access(os.path.dirname(filePath), os.W_OK):
                UI4.Widgets.MessageBox.Information('Information', 'Export location {} does not have write permissions.'.format(os.path.dirname(filePath)))
            frameNumber = 1
            itemIndex = []
            for catalogItem in selectedItems:
                if catalogItem.getIndex() in itemIndex:
                    continue
                else:
                    layerview = catalogItem.getPrimaryLayerView()
                    buf = catalogItem.getBuffer(layerview)
                    name = filePath + ('.{}.exr').format(str(frameNumber).zfill(4))
                    frameNumber += 1

                    # EXR metadata start (can add anything here)
                    exrMetadata = []
                    if catalogItem.getNodeName():
                        exrMetadata.append(('katana:node', str(catalogItem.getNodeName())))
                    if catalogItem.getFrameRange():
                        exrMetadata.append(('katana:framerange', str(catalogItem.getFrameRange())))
                    sourceFile = NodegraphAPI.GetSourceFile()
                    if sourceFile:
                        exrMetadata.append(('katana:file', str(sourceFile)))
                    exrMetadata.append(('katana:layer', layerview[0]))
                    exrMetadata.append(('katana:view', layerview[1]))
                    # EXR metadata end

                    imageOptions['exrMetadata'] = exrMetadata
                    imageOptions['comments'] = catalogItem.getUserComment()
                    buf.writeToDisk(name, imageOptions, 1, 0, False)

    args = {'dirsOnly': False, 'acceptDir': True, 'sequenceListing': True, 'context': AssetAPI.kAssetContextCatalog}
    imageOptions = dict([('exrCompression', 'Wavelet'), ('exrBitDepth', '16')])

    menuBar = catalogTab.getMenuBar()
    fileAction = menuBar.actions()[0]
    fileMenu = fileAction.menu()

    fileMenu.addSeparator().setText('Special Export')

    # Merged AOVs menu
    mergedSubmenu = fileMenu.addMenu('Merged AOVs')
    deleteIndividualAOVs = mergedSubmenu.addAction('Delete individual AOVs')
    mergedSubmenuSeparator = mergedSubmenu.addSeparator()
    mergedSubmenuSeparator.setObjectName('mergedSubmenuSeparator')
    deleteIndividualAOVs.setObjectName('deleteIndividualAOVs')
    deleteIndividualAOVs.setCheckable(True)
    deleteIndividualAOVs.setChecked(True)
    allMergedAOVs = mergedSubmenu.addAction('All Images')
    allMergedAOVs.setObjectName('allMergedAOVs')
    lockedMergedAOVs = mergedSubmenu.addAction('Locked Images')
    lockedMergedAOVs.setObjectName('lockedMergedAOVs')
    selectedMergedAOVs = mergedSubmenu.addAction('Selected Images')
    selectedMergedAOVs.setObjectName('selectedMergedAOVs')

    # Primary only menu
    mergedSubmenu = fileMenu.addMenu('Primary Only')
    allPrimary = mergedSubmenu.addAction('All Images')
    allPrimary.setObjectName('allPrimary')
    lockedPrimary = mergedSubmenu.addAction('Locked Images')
    lockedPrimary.setObjectName('lockedPrimary')
    selectedPrimary = mergedSubmenu.addAction('Selected Images')
    selectedPrimary.setObjectName('selectedPrimary')

    # Connect Merged functions
    allMergedAOVs.triggered.connect(partial(on_mergedExport_triggered, catalogWidget.LIST_ALL))
    lockedMergedAOVs.triggered.connect(partial(on_mergedExport_triggered, catalogWidget.LIST_LOCKED))
    selectedMergedAOVs.triggered.connect(partial(on_mergedExport_triggered, catalogWidget.LIST_SELECTED))

    # Connect Primary functions
    allPrimary.triggered.connect(partial(on_primaryExport_triggered, catalogWidget.LIST_ALL))
    lockedPrimary.triggered.connect(partial(on_primaryExport_triggered, catalogWidget.LIST_LOCKED))
    selectedPrimary.triggered.connect(partial(on_primaryExport_triggered, catalogWidget.LIST_SELECTED))

if hasattr(Callbacks.Type, 'onTabCreated'):
   Callbacks.addCallback(Callbacks.Type.onTabCreated, onTabCreated)