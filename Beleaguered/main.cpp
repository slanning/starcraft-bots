#include "sc2api/sc2_api.h"
#include "sc2lib/sc2_lib.h"
#include "sc2utils/sc2_manage_process.h"
#include "sc2utils/sc2_arg_parser.h"
#include "rapidjson/document.h"
#include "JSONTools.h"
#include "Util.h"

#include <iostream>
#include <string>
#include <random>
#include <cmath>
#include <algorithm>

//#include "CCBot.h"
#include "bot.h"

sc2::PlayerSetup CreateBot(Agent *bot) {
	// return( sc2::CreateParticipant(sc2::Race::Zerg, bot) );
	return(sc2::CreateParticipant(sc2::Race::Terran, bot));
}

#ifndef LADDEREXE
bool useDebug = true;
bool useAutoObserver = false;
#else
bool useDebug = false;
bool useAutoObserver = true;
#endif

#ifndef LADDEREXE

int main(int argc, char* argv[]) {
	sc2::Coordinator coordinator;

	int stepSize = 1;
		// Add the custom bot, it will control the players.
		//CCBot bot;
		Bot bot;
		
		if (!coordinator.LoadSettings(argc, argv)) {
			std::cout << "Couldn't load settings" << std::endl;
			return 1;
		}

		// WARNING: Bot logic has not been thorougly tested on step sizes > 1
		//          Setting this = N means the bot's onFrame gets called once every N frames
		//          The bot may crash or do unexpected things if its logic is not called every frame
		coordinator.SetStepSize(stepSize);
		coordinator.SetRealtime(false);
		coordinator.SetMultithreaded(true);
		coordinator.SetParticipants({
			CreateBot(&bot),
			//CreateParticipant(sc2::Race::Terran, &bot),
			//sc2::PlayerSetup(sc2::PlayerType::Observer,Util::GetRaceFromString(enemyRaceString)),
			CreateComputer(sc2::Race::Protoss, sc2::Difficulty::CheatInsane),
		});
		// Start the game.
		coordinator.LaunchStarcraft();

		// this value is VERY SENSITIVE and depends on having the map file in a particular place,
		// otherwise when it launches it will just hang with a black screen....
		// coordinator.StartGame(sc2::kMapBelShirVestigeLE);
		if (coordinator.StartGame("InterloperLE.SC2Map")) {
			std::cout << "Started" << std::endl;
		}
		else {
			std::cerr << "Couldn't start game" << std::endl;
			return(1);
		}

		// Step forward the game simulation.
		while (coordinator.Update()) {
		}
		//if (bot.Control()->SaveReplay("C:/Users/D/Documents/StarCraft II/Accounts/115842237/2-S2-1-1338490/Replays/Multiplayer/asdf.Sc2Replay")) {
		//	std::cout << "REPLAY SUCESS" << "replay/asdf.Sc2Replay" << std::endl;
		//}
		//else {
		//	std::cout << "REPLAY FAIL" << "replay/asdf.Sc2Replay" << std::endl;
		//}
		//coordinator.LeaveGame();
		//Sleep(1000);

    return 0;
}

#else

#include "LadderInterface.h"

int main(int argc, char* argv[]) {
	Bot bot;
	RunBot(argc, argv, CreateBot(&bot), sc2::Race::Protoss);
	return 0;
}

#endif
