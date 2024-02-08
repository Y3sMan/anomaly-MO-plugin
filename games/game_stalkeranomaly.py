# -*- encoding: utf-8 -*-

from pathlib import Path
from typing import List
from enum import IntEnum
import shutil

try:
    from PyQt6.QtCore import QDir, QFileInfo, Qt
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
except:
    from PyQt5.QtCore import Qt, QDir, QFileInfo
    from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

import mobase

from ..basic_features.basic_save_game_info import (
    BasicGameSaveGame,
    BasicGameSaveGameInfo,
)
from ..basic_game import BasicGame

from .stalkeranomaly import XRSave


## debug ##
_mo_dir = 'G:/GOG Galaxy/Games/GAMMA/'
_game_dir = 'G:\GOG Galaxy\Games\Anomoly - GAMMA/'
def print_to_file(msg: str):
    import datetime
    with open('G:/GOG Galaxy/Games/GAMMA/logs/mo_yesman_anomaly.log', "a") as fout:
        fout.write("\n")
        fout.write(f'[{datetime.datetime.now()}]: {msg}')


def move_file(source, target):
    # mobase.IFileTree.move( f'{_game_dir}/appdata_mo')
    # game_tree = mobase.IFileTree()
    # print_to_file(mobase.IFileTree.find(f'{_game_dir}/appdata'), type=mobase.FileTreeEntry.FileTypes.DIRECTORY)
    if not target.parent.exists():
        target.parent.mkdir(parents=True)
    shutil.move(str(source.resolve()), str(target.resolve()))

def copy_file(source, target):
    # mobase.IFileTree.move( f'{_game_dir}/appdata_mo')
    # game_tree = mobase.IFileTree()
    # print_to_file(mobase.IFileTree.find(f'{_game_dir}/appdata'), type=mobase.FileTreeEntry.FileTypes.DIRECTORY)
    if not target.parent.exists():
        target.parent.mkdir(parents=True)
    shutil.copyfile(str(source.resolve()), str(target.resolve()))

class StalkerAnomalyModDataChecker(mobase.ModDataChecker):
    _valid_folders: List[str] = [
        "appdata",
        "bin",
        "db",
        "gamedata",
    ]

    def hasValidFolders(self, tree: mobase.IFileTree) -> bool:
        for e in tree:
            if e.isDir():
                if e.name().lower() in self._valid_folders:
                    return True

        return False

    def findLostData(self, tree: mobase.IFileTree) -> List[mobase.FileTreeEntry]:
        lost_db: List[mobase.FileTreeEntry] = []

        for e in tree:
            if e.isFile():
                if e.suffix().lower().startswith("db"):
                    lost_db.append(e)

        return lost_db

    def dataLooksValid(
        self, tree: mobase.IFileTree
    ) -> mobase.ModDataChecker.CheckReturn:
        if self.hasValidFolders(tree):
            return mobase.ModDataChecker.VALID

        if self.findLostData(tree):
            return mobase.ModDataChecker.FIXABLE

        return mobase.ModDataChecker.INVALID

    def fix(self, tree: mobase.IFileTree) -> mobase.IFileTree:
        lost_db = self.findLostData(tree)
        if lost_db:
            rfolder = tree.addDirectory("db").addDirectory("mods")
            for r in lost_db:
                rfolder.insert(r, mobase.IFileTree.REPLACE)

        return tree


class Content(IntEnum):
    INTERFACE = 0
    TEXTURE = 1
    MESH = 2
    SCRIPT = 3
    SOUND = 4
    MCM = 5
    CONFIG = 6


class StalkerAnomalyModDataContent(mobase.ModDataContent):
    content: List[int] = []

    def getAllContents(self) -> List[mobase.ModDataContent.Content]:
        return [
            mobase.ModDataContent.Content(
                Content.INTERFACE, "Interface", ":/MO/gui/content/interface"
            ),
            mobase.ModDataContent.Content(
                Content.TEXTURE, "Textures", ":/MO/gui/content/texture"
            ),
            mobase.ModDataContent.Content(
                Content.MESH, "Meshes", ":/MO/gui/content/mesh"
            ),
            mobase.ModDataContent.Content(
                Content.SCRIPT, "Scripts", ":/MO/gui/content/script"
            ),
            mobase.ModDataContent.Content(
                Content.SOUND, "Sounds", ":/MO/gui/content/sound"
            ),
            mobase.ModDataContent.Content(Content.MCM, "MCM", ":/MO/gui/content/menu"),
            mobase.ModDataContent.Content(
                Content.CONFIG, "Configs", ":/MO/gui/content/inifile"
            ),
        ]

    def walkContent(
        self, path: str, entry: mobase.FileTreeEntry
    ) -> mobase.IFileTree.WalkReturn:
        name = entry.name().lower()
        if entry.isFile():
            ext = entry.suffix().lower()
            if ext in ["dds", "thm"]:
                self.content.append(Content.TEXTURE)
                if path.startswith("gamedata/textures/ui"):
                    self.content.append(Content.INTERFACE)
            elif ext in ["omf", "ogf"]:
                self.content.append(Content.MESH)
            elif ext in ["script"]:
                self.content.append(Content.SCRIPT)
                if "_mcm" in name:
                    self.content.append(Content.MCM)
            elif ext in ["ogg"]:
                self.content.append(Content.SOUND)
            elif ext in ["ltx", "xml"]:
                self.content.append(Content.CONFIG)
                if path.startswith("gamedata/configs/ui"):
                    self.content.append(Content.INTERFACE)

        return mobase.IFileTree.WalkReturn.CONTINUE

    def getContentsFor(self, tree: mobase.IFileTree) -> List[int]:
        self.content = []
        tree.walk(self.walkContent, "/")
        return self.content


class StalkerAnomalySaveGame(BasicGameSaveGame):
    _filepath: Path

    xr_save: XRSave

    def __init__(self, filepath: Path):
        super().__init__(filepath)
        self._filepath = filepath
        self.xr_save = XRSave(self._filepath)

    def getName(self) -> str:
        xr_save = self.xr_save
        player = xr_save.player
        if player:
            name = player.character_name_str
            time = xr_save.time_fmt
            return f"{name}, {xr_save.save_fmt} [{time}]"
        return ""

    def allFiles(self) -> List[str]:
        filepath = str(self._filepath)
        paths = [filepath]
        scoc = filepath.replace(".scop", ".scoc")
        if Path(scoc).exists():
            paths.append(scoc)
        dds = filepath.replace(".scop", ".dds")
        if Path(dds).exists():
            paths.append(dds)
        return paths


class StalkerAnomalySaveGameInfoWidget(mobase.ISaveGameInfoWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        layout = QVBoxLayout()
        self._labelSave = self.newLabel(layout)
        self._labelName = self.newLabel(layout)
        self._labelFaction = self.newLabel(layout)
        self._labelHealth = self.newLabel(layout)
        self._labelMoney = self.newLabel(layout)
        self._labelRank = self.newLabel(layout)
        self._labelRep = self.newLabel(layout)
        self.setLayout(layout)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.setWindowFlags(Qt.ToolTip | Qt.BypassGraphicsProxyWidget)  # type: ignore

    def newLabel(self, layout: QVBoxLayout) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignLeft)
        palette = label.palette()
        palette.setColor(label.foregroundRole(), Qt.white)
        label.setPalette(palette)
        layout.addWidget(label)
        layout.addStretch()
        return label

    def setSave(self, save: mobase.ISaveGame):
        self.resize(240, 32)
        if not isinstance(save, StalkerAnomalySaveGame):
            return
        xr_save = save.xr_save
        player = xr_save.player
        if player:
            self._labelSave.setText(f"Save: {xr_save.save_fmt}")
            self._labelName.setText(f"Name: {player.character_name_str}")
            self._labelFaction.setText(f"Faction: {xr_save.getFaction()}")
            self._labelHealth.setText(f"Health: {player.health:.2f}%")
            self._labelMoney.setText(f"Money: {player.money} RU")
            self._labelRank.setText(f"Rank: {xr_save.getRank()} ({player.rank})")
            self._labelRep.setText(
                f"Reputation: {xr_save.getReputation()} ({player.reputation})"
            )


class StalkerAnomalySaveGameInfo(BasicGameSaveGameInfo):
    def getSaveGameWidget(self, parent=None):
        return StalkerAnomalySaveGameInfoWidget(parent)



class StalkerAnomalyLocalSavegames(mobase.LocalSavegames):
    def __init__(self, myGameSaveDir):
        super().__init__()
        print_to_file('Running StalkerAnomalyLocalSavegames init')
        self._savesDir = myGameSaveDir.absolutePath()
        # self._savesDir = str( Path( self._savesDir ).parent.absolute() )
        print_to_file(f'{self._savesDir = }')
        # reset appdata folder
        # if  Path(self._savesDir).parent.joinpath("mo__appdata").exists():
        #     print_to_file('it exists')
        #     move_file(Path(f'{self._savesDir}/mo__appdata'), Path(f'{_game_dir}/appdata'))

    def mappings(self, profile_save_dir):
        print_to_file('Running StalkerAnomalyLocalSavegames mappings')
        root_game = Path(self._savesDir).parent

        # root_game = Path(self._savesDir)
        # print_to_file(f'{root_game = }')
        appdata = root_game.joinpath('appdata')
        mo_appdata = root_game.joinpath('mo__appdata')
        # print_to_file(f'{appdata = }')
        # print_to_file(f'{mo_appdata = }')
        if appdata.exists():
        #     # move_file(appdata, mo_appdata)
            appdata.rename(mo_appdata)
            # create empty appdata
            appdata.mkdir()

        

        # print_to_file(f'{self._savesDir = }')
        src = profile_save_dir.absolutePath()  + '/appdata'
        # dest = str( root_game.absolute() )
        dest = self._savesDir

        print_to_file(f'{src = } ')
        print_to_file(f'{dest = }')

        return [
            mobase.Mapping(
                source=src,
                destination=dest,
                is_directory=True,
                create_target=True,
            )
        ]

    def prepareProfile(self, profile):
        return profile.localSavesEnabled()


class StalkerAnomalyGame(BasicGame, mobase.IPluginFileMapper):
    Name = "STALKER Anomaly"
    Author = "Qudix"
    Version = "0.5.0"
    Description = "Adds support for STALKER Anomaly"

    GameName = "STALKER Anomaly"
    GameShortName = "stalkeranomaly"
    GameNexusName = "stalkeranomaly"
    GameNexusId = 3743
    GameBinary = "AnomalyLauncher.exe"
    GameDataPath = ""
    GameDocumentsDirectory = "%GAME_PATH%/appdata"

    GameSaveExtension = "scop"
    GameSavesDirectory = "%GAME_PATH%/appdata"

    def __init__(self):
        BasicGame.__init__(self)
        mobase.IPluginFileMapper.__init__(self)

    def init(self, organizer: mobase.IOrganizer):
        BasicGame.init(self, organizer)
        self._featureMap[mobase.ModDataChecker] = StalkerAnomalyModDataChecker()
        self._featureMap[mobase.ModDataContent] = StalkerAnomalyModDataContent()
        # self._featureMap[mobase.SaveGameInfo] = StalkerAnomalySaveGameInfo()
        self._featureMap[mobase.LocalSavegames] = StalkerAnomalyLocalSavegames(
            self.savesDirectory()
        )
        # organizer.onAboutToRun(lambda _str: self.aboutToRun(_str))
        # organizer.onFinishedRun(lambda test, test2: print_to_file('onfinishedrun2'))
        print_to_file(f'{self._organizer.appVersion().displayString() = }')
        self._register_event_handler()
        return True

    def initializeProfile(self, directory: QDir, settings: mobase.ProfileSetting):
        print_to_file('initializeProfile')
        print_to_file(f'{self.savesDirectory().absolutePath() = }')
        self._featureMap[mobase.LocalSavegames] = StalkerAnomalyLocalSavegames(
            self.savesDirectory()
        )

        # print_to_file(f'{self.UiInitialized = }')
        super().initializeProfile(directory, settings)
        # if self.UiInitialized:
        #     print_to_file(f'{ self._organizer.profile().localSavesEnabled() =}')
            # print_to_file(f'{self._featureMap[mobase.LocalSavegames].prepareProfile()}')


    def aboutToRun(self, _str: str) -> bool:
        gamedir = self.gameDirectory()
        if gamedir.exists():
            # For mappings
            gamedir.mkdir("appdata")
            # The game will crash if this file exists in the
            # virtual tree rather than the game dir
            dbg_path = Path(self._gamePath, "gamedata/configs/cache_dbg.ltx")
            if not dbg_path.exists():
                dbg_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dbg_path, "w", encoding="utf-8") as file:  # noqa
                    pass
        return True

    def executables(self) -> List[mobase.ExecutableInfo]:
        info = [
            ["Anomaly Launcher", "AnomalyLauncher.exe"],
            ["Anomaly (DX11-AVX)", "bin/AnomalyDX11AVX.exe"],
            ["Anomaly (DX11)", "bin/AnomalyDX11.exe"],
            ["Anomaly (DX10-AVX)", "bin/AnomalyDX10AVX.exe"],
            ["Anomaly (DX10)", "bin/AnomalyDX10.exe"],
            ["Anomaly (DX9-AVX)", "bin/AnomalyDX9AVX.exe"],
            ["Anomaly (DX9)", "bin/AnomalyDX9.exe"],
            ["Anomaly (DX8-AVX)", "bin/AnomalyDX8AVX.exe"],
            ["Anomaly (DX8)", "bin/AnomalyDX8.exe"],
        ]
        gamedir = self.gameDirectory()
        return [
            mobase.ExecutableInfo(inf[0], QFileInfo(gamedir, inf[1])) for inf in info
        ]

    def listSaves(self, folder: QDir) -> List[mobase.ISaveGame]:
        save_games = super().listSaves(folder)
        path = Path(folder.absolutePath() + '/savedgames') 
        # print_to_file(path)
        ext = self._mappings.savegameExtension.get()
        save_games.extend(StalkerAnomalySaveGame(f) for f in path.glob(f"*.{ext}"))
        return save_games

    def mappings(self) -> List[mobase.Mapping]:
        appdata = self.gameDirectory().filePath("appdata")
        m = mobase.Mapping()
        m.createTarget = True
        m.isDirectory = True
        m.source = appdata
        m.destination = appdata
        return [m]


    def _register_event_handler(self):
        self._organizer.onUserInterfaceInitialized(lambda win: self._organizer_onUiInitalized_event_handler())
        self._organizer.onAboutToRun(self._game_aboutToRun_event_handler)
        self._organizer.onFinishedRun(self._game_finished_event_handler)
        self._organizer.onProfileCreated(self._organizer_onProfileCreated_event_handler)
        self._organizer.onProfileChanged(self._organizer_onProfileChanged_event_handler)

        if self._organizer.appVersion().displayString()[0:3].find('2.5') > 0:
            print_to_file('version 2.5')
            immediate_if_possible:bool = True 
            self._organizer.onNextRefresh(self._organizer_onNextRefresh_event_handler, immediate_if_possible)
        else:
            print_to_file('not version 2.5')

    # version 2.5 or greater
    def _organizer_onNextRefresh_event_handler(self) -> bool:
        print_to_file('_organizer_onNextRefresh_event_handler')

        root_game = Path(self.GameSavesDirectory).parent
        print_to_file(f'{root_game = }')
        appdata = root_game.joinpath('appdata')
        mo_appdata = root_game.joinpath('mo__appdata')
        if not appdata.exists() and mo_appdata.exists():
            mo_appdata.rename(appdata)
            # self._organizer_onNextRefresh_event_handler(_organizer_onNextRefresh_event_handler)

    def _organizer_onUiInitalized_event_handler(self) -> bool:
        print_to_file("UI Loaded")
        print_to_file(f'{self._organizer.profileName()}')
        self.UiInitialized = True
        # print_to_file(f'{self.UiInitialized = }')
        # pass
        # print_to_file(f'{ self._organizer.profile().localSavesEnabled() =}')

    def _organizer_onProfileCreated_event_handler(self, profile) -> bool:
        print_to_file('profile created')

    def _organizer_onProfileChanged_event_handler(self, oldProfile, newProfile ):
        print_to_file('onprofilechanged')
        # old_profile = profiles[0]
        # new_profile = profiles[1]
        profile_dir = Path( newProfile.absolutePath() )
        profile_appdata = profile_dir.joinpath('saves/appdata')

        root_game = Path( self.gameDirectory().absolutePath() )
        print_to_file(f'initializeProfile: {root_game = }')
        game_appdata = root_game.joinpath('appdata')
        mo_appdata = root_game.joinpath('mo__appdata')

        if newProfile.localSavesEnabled():
            if not profile_appdata.exists():
                print_to_file(f'Profile: {newProfile.name()} does not have saves/appdata')
                profile_appdata.mkdir()
                profile_appdata.joinpath('logs').mkdir()
                profile_appdata.joinpath('savedgames').mkdir()
                profile_appdata.joinpath('shaders_cache').mkdir()
                profile_appdata.joinpath('screenshots').mkdir()
                # if Default profile exists
                default_pro = profile_dir.parent.joinpath('Default')
                print_to_file(default_pro)
                # refresh the vfs right now
                # immediate_if_possible : bool = True

                # self._organizer.onNextRefresh(self._organizer_onNextRefresh_event_handler, immediate_if_possible)
                # if default_pro.exists():
                #     # copy_file(default_pro.joinpath('saves/appdata'), profile_dir.joinpath('saves'))
                #     for path in default_pro.joinpath('saves/appdata').glob('*'):
                #         print_to_file(str(path.absolute()))
                    # mobase.IFileTree.copy(default_pro.joinpath('saves/appdata'), profile_appdata)
                    # shutil.copy2(default_pro, profile_dir.joinpath('testytest'))

        if mo_appdata.exists():
            if game_appdata.exists():
                # try:
                game_appdata.rmdir()
                # except():
            mo_appdata.rename(game_appdata)

                        
                
        # print_to_file(old_profile)
        # self.UiInitialized = True
        return True

    def _game_aboutToRun_event_handler(self, _str: str) -> bool:
        print_to_file('_game_aboutToRun_event_handler')
        gamedir = self.gameDirectory()
        if gamedir.exists():
            print_to_file('game exists')
            # For mappings
            # gamedir.mkdir("appdata")
            # The game will crash if this file exists in the
            # virtual tree rather than the game dir

            dbg_path = Path(self._gamePath, "gamedata/configs/cache_dbg.ltx")
            if not dbg_path.exists():
                dbg_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dbg_path, "w", encoding="utf-8"):
                    pass
        return True


    def _game_finished_event_handler(self, app_path: str, exit_code: int) -> None:
        print_to_file('app_path')
        print_to_file('_game_finished_event_handler')
        root_game = Path( self.gameDirectory().absolutePath() )
        appdata = root_game.joinpath('appdata')
        mo_appdata = root_game.joinpath('mo__appdata')
        print_to_file(f'{appdata = }')
        print_to_file(f'{mo_appdata = }')
        if mo_appdata.exists():
            if appdata.exists() and len(list( appdata.glob('*'))) == 0:
                appdata.rmdir()
            # move_file(mo_appdata, root_game)
            mo_appdata.rename(appdata)