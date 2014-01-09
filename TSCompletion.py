import os
import re
import logging
import sublime, sublime_plugin

class TscompletionCommand(sublime_plugin.TextCommand):

    ## Constant plugin
    defaultFileEncoding = "utf-8"
    extInclude = ".ts" #TODO do a list
    extExclude = ".d.ts" #TODO do a list
    moduleRegex = ".*module\s.+{"
    classRegex = "\s*export class \w+"
    methodRegex = "\s*(public|private|static)\s+(static\s+)*\w+\s*\("

    ## Variable plugin
    projectPathList = []
    tsFileList = []
    tsProjectDictionary = {}
    tsClassList = []
    classChoice = []

    ## Method plugin
    def run(self, edit):
        # Reset
        self.projectPathList = []
        self.tsFileList = []
        self.tsProjectDictionary = {}
        self.tsClassList = []
        self.classChoice = []

        self.projectPathList = self.getCurrentProjectPath()
        self.tsFileList = self.getTsFileList(self.projectPathList)

        self.genProjectDictionary(self.tsFileList)
        sublime.active_window().show_quick_panel(self.tsClassList, self.onClassChoice)

    def getCurrentProjectPath(self):
        projectFolderList = sublime.active_window().project_data()["folders"]
        dirList = []

        for pathDic in projectFolderList:

            # Absolute path => ok
            if os.path.isdir(pathDic["path"]):
                dirList.append(pathDic["path"])

            # Relative path => not ok
            else:
                userPathList = sublime.packages_path().rsplit(os.sep)
                userPath = os.sep + os.sep.join((userPathList[1], userPathList[2], "Documents")) + os.sep
                if os.path.isdir(userPath + pathDic["path"]):
                    dirList.append(userPath + pathDic["path"])

        #logging.warning("Project Path: " + str(dirList))

        return dirList

    def getTsFileList(self, pathList):
        fileList = []
        for path in pathList:
            for root, dirs, files in os.walk(path):
                for name in files:
                    if name.endswith(self.extInclude) & (not name.endswith(self.extExclude)):
                        fileList.append(os.path.join(root, name))

        #logging.warning("File List: " + str(fileList))

        return fileList

    def genProjectDictionary(self, fileList):
        for file in fileList:
            tmpFile = open(file, 'r', -1, self.defaultFileEncoding)
            self.extractFromFile(tmpFile)
            tmpFile.close()

    def extractFromFile(self, file):
        # Module
        patternModule = re.compile(self.moduleRegex)
        patternModuleName = re.compile(r"\b(?!module|export|declare)\w+\b")
        moduleName = ""

        # Class
        patternClass = re.compile(self.classRegex)
        patternClassName = re.compile(r"\b(?!export|class|extends|implements)\w+\b")
        className = ""

        # Method
        patternMethod = re.compile(self.methodRegex)
        patternMethodName = re.compile(r"\w+\s\w+\(.*\)")
        methodName = ""

        for line in file.readlines():
            # Module
            if patternModule.match(line):
                # If a module are manually export into an other module and not simply module.submodule
                if "export" in line:
                    moduleName = moduleName + "." + ".".join(patternModuleName.findall(patternModule.findall(line)[0]))
                else:
                    moduleName = ".".join(patternModuleName.findall(patternModule.findall(line)[0]))

            # Class
            if patternClass.match(line):
                className = moduleName + "." + patternClassName.findall(line)[0]
                if not className in self.tsClassList:
                    self.tsClassList.append(className)
                if not className in self.tsProjectDictionary:
                    self.tsProjectDictionary[className] = []
                else:
                    break

            # Method
            if patternMethod.match(line):
                methodName = patternMethodName.findall(line)[0]
                if not methodName in self.tsProjectDictionary[className]:
                    self.tsProjectDictionary[className].append(methodName)

    def onClassChoice(self, value):
        #logging.warning(self.tsClassList[value])
        #logging.warning(self.tsProjectDictionary[self.tsClassList[value]])
        if value != -1:
            self.classChoice = self.tsClassList[value]
            #sublime.set_timeout(lambda: self.view.show_popup_menu(self.tsProjectDictionary[self.classChoice], self.onMethodChoice), 10)
            sublime.set_timeout(lambda: sublime.active_window().show_quick_panel(self.tsProjectDictionary[self.classChoice], self.onMethodChoice), 10)

    def onMethodChoice(self, value):
        if value != -1:
            methodString = self.tsProjectDictionary[self.classChoice][value]
            sublime.set_timeout(lambda: sublime.active_window().run_command("inserttscompletion", {"method": methodString}), 10)
        else:
            sublime.error_message("Sorry, no method in class " + self.classChoice + "\nIf you find a bug, leave issue on \nhttps://github.com/RonanDrouglazet/TSCompletion")

class InserttscompletionCommand(sublime_plugin.TextCommand):

    def run(self, edit, method):
        caretPos = self.view.sel()[0].begin()
        self.view.insert(edit, caretPos, method)
