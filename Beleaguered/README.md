This is code for the Starcraft 2 bot "Beleaguered".
It is based on the tutorial at
https://github.com/Blizzard/s2client-api/blob/master/docs/tutorial3.md
except made into a separate Solution and with code to allow it to run
in a LadderManager tournament, as at https://sc2ai.net/FAQ.php ,
which runs on https://github.com/Cryptyc/Sc2LadderServer .
It uses the LADDEREXE trick from https://github.com/Archiatrus/5minBot/blob/master/src/main.cpp
to use code for local testing (Debug) or for the LadderManager (Release).
The code for the LadderManager part comes from CryptBot,
https://github.com/Cryptyc/CryptBot/blob/master/CryptbotMain.cpp .
I also split the Bot class out into bot.h and bot.cpp
instead of inlining it like the tutorial does.


I tried to keep notes of what was needed to set things up
on Windows with Visual Studio.
I assumed s2client-api is already built
two folders above the Beleaguered folder.
If you open Beleaguered.sln and right-click the Project (not the Solution)
in the menu, select Properties, I think this is what changed from the defaults:

-=-=-=-=-=-

Select the Debug configuration, x64 platform

```
Configuration Properties
> C/C++ > General > Additional Include Directories:
..\..\s2client-api\contrib\protobuf\src;..\..\s2client-api\include;..\..\s2client-api\contrib\civetweb\include;..\..\s2client-api\contrib\SDL-mirror\include;..\..\s2client-api\build\generated;%(AdditionalIncludeDirectories)

> Linker > General > Additional Library Directories:
..\..\s2client-api\project\lib;%(AdditionalLibraryDirectories)

> Linker > Input > Additional Dependencies (note: most end with "d" for Debug): sc2apid.lib;sc2libd.lib;sc2utilsd.lib;sc2protocold.lib;libprotobufd.lib;civetweb.lib;%(AdditionalDependencies)
```
	
Select the Release configuration, x64 platform

```
Configuration Properties
> C/C++ > General > Additional Include Directories (same as Debug):
..\..\s2client-api\contrib\protobuf\src;..\..\s2client-api\include;..\..\s2client-api\contrib\civetweb\include;..\..\s2client-api\contrib\SDL-mirror\include;..\..\s2client-api\build\generated;%(AdditionalIncludeDirectories)

> C/C++ > Preprocessor > Preprocessor Definitions:
LADDEREXE;%(PreprocessorDefinitions)
  
> Linker > General > Additional Library Directories:
..\..\s2client-api\project\lib;%(AdditionalLibraryDirectories)

> Linker > Input > Additional Dependencies:
sc2api.lib;sc2lib.lib;sc2utils.lib;sc2protocol.lib;libprotobuf.lib;civetweb.lib;%(AdditionalDependencies)
```

-=-=-=-=-=-

Works for me, at least, though I haven't submitted anything to the LadderManager tournament yet.
Once you select "Debug x64" configuration and "Build > Build Solution",
you should be able to run starcraft-bots\Beleaguered\x64\Debug\Beleaguered.exe
(You shouldn't need to start Starcraft first or even the Battlenet client.)
If you get a blank screen, likely you don't have the map,
which is "InterloperLE.SC2Map". That should be in your Maps folder,
by default C:\Program Files (x86)\StarCraft II\Maps\
You can get that by playing a custom game on that map against the AI for example.
Or of course you could change the map to one you have.

(I still get some warnings from protobuf, so I probably still have something wrong there.)
