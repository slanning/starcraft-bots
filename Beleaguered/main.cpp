#include <iostream>

#include "sc2api/sc2_api.h"

#include "bot.h"

sc2::PlayerSetup CreateBot(Agent *bot) {
//	return( sc2::CreateParticipant(sc2::Race::Zerg, bot) );
	return( sc2::CreateParticipant(sc2::Race::Terran, bot) );
}

// code for local testing
#ifndef LADDEREXE

int main(int argc, char* argv[]) {
    sc2::Coordinator coordinator;
    coordinator.LoadSettings(argc, argv);

	std::cout << "main" << std::endl;

    Bot bot;
    coordinator.SetParticipants({
        //CreateBot(&bot),
		sc2::CreateParticipant(sc2::Race::Terran, &bot),
        CreateComputer(Race::Zerg, sc2::Easy),
    });

	std::cout << "botted" << std::endl;

    coordinator.LaunchStarcraft();

	std::cout << "launched" << std::endl;

	// this value is VERY SENSITIVE and depends on having the map file in a particular place,
	// otherwise when it launches it will just hang with a black screen....
//    coordinator.StartGame(sc2::kMapBelShirVestigeLE);
	coordinator.StartGame("InterloperLE.SC2Map");

	std::cout << "started" << std::endl;

    while (coordinator.Update()) {
    }

    return 0;
}


/////////////////////////////////////////////////////////////

// code for LadderManager
#else

#include <iostream>

#include "sc2lib/sc2_lib.h"
#include "sc2utils/sc2_arg_parser.h"

struct ConnectionOptions
{
	int32_t GamePort;
	int32_t StartPort;
	std::string ServerAddress;
};

void ParseArguments(int argc, char *argv[], ConnectionOptions &connect_options)
{
	sc2::ArgParser arg_parser(argv[0]);
	arg_parser.AddOptions({
		{ "-g", "--GamePort", "Port of client to connect to", false },
		{ "-o", "--StartPort", "Starting server port", false },
		{ "-l", "--LadderServer", "Ladder server address", false },
		});
	arg_parser.Parse(argc, argv);
	std::string GamePortStr;
	if (arg_parser.Get("GamePort", GamePortStr)) {
		connect_options.GamePort = atoi(GamePortStr.c_str());
	}
	std::string StartPortStr;
	if (arg_parser.Get("StartPort", StartPortStr)) {
		connect_options.StartPort = atoi(StartPortStr.c_str());
	}
	arg_parser.Get("LadderServer", connect_options.ServerAddress);
}

//*************************************************************************************************
int main(int argc, char* argv[]) {
	ConnectionOptions Options;
	ParseArguments(argc, argv, Options);

	sc2::Coordinator coordinator;
	if (!coordinator.LoadSettings(argc, argv)) {
		return 1;
	}

	// Add the custom bot, it will control the players.
	Bot bot;
	coordinator.SetParticipants({
		CreateBot(&bot),
	});

	// Start the game.

	// Step forward the game simulation.
	std::cout << "Connecting to port " << Options.GamePort << std::endl;
	coordinator.Connect(Options.GamePort);
	coordinator.SetupPorts(2, Options.StartPort, false);
	// Step forward the game simulation.
	coordinator.JoinGame();
	coordinator.SetTimeoutMS(10000);
	std::cout << " Successfully joined game" << std::endl;
	while (coordinator.Update()) {
	}

	return 0;
}

#endif
