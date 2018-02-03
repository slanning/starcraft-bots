#include <iostream>
#include <sstream>

#include "bot.h"
#include "util.h"   // dump_unit, dump_game_info, ...

using namespace sc2;

Bot::Bot() {
}

// void Bot::OnGameFullStart() {
// }

void Bot::OnGameStart() {
	const GameInfo& game_info = Observation()->GetGameInfo();

	std::string botname = "Beleaguered";
	std::stringstream greeting;
	greeting << "glhf from " << botname
		<< " (Player " << Observation()->GetPlayerID() << ", "
		<< race_to_str( game_info.player_info[Observation()->GetPlayerID() - 1].race_requested ) << ")";
	Actions()->SendChat(greeting.str(), sc2::ChatChannel::All);

	dump_game_info(game_info);
}

void Bot::OnGameEnd() {
    std::cout << "gg" << std::endl;
	// can ->SendChat be done here?

	dump_player_results(Observation());
}

void Bot::OnStep() {
	uint32_t i = Observation()->GetGameLoop();
	//std::cout << "game loop: " << i << std::endl;

	TryBuildSupplyDepot();
	TryBuildBarracks();
	/*
	if (i % 200 == 0) {
		for (const auto& u : Observation()->GetUnits()) {
			dump_unit(u);
		}
	}
	*/
	/*
	if (i % 100 == 0) {
		dump_resource_info(Observation());
	}
	*/

	// dump_scores(Observation()->GetScore());
}

void Bot::OnUnitDestroyed(const Unit* unit) {
	std::cout << "Unit destroyed: " << sc2::UnitTypeToName(unit->unit_type) << " with tag " << unit->tag << std::endl;
}

void Bot::OnUnitCreated(const Unit* unit) {
	std::cout << "Unit created: " << sc2::UnitTypeToName(unit->unit_type) << " with tag " << unit->tag << std::endl;
}

void Bot::OnUnitIdle(const Unit* unit) {
	switch (unit->unit_type.ToType()) {
	case UNIT_TYPEID::TERRAN_COMMANDCENTER: {
		Actions()->UnitCommand(unit, ABILITY_ID::TRAIN_SCV);
		break;
	}
	case UNIT_TYPEID::TERRAN_SCV: {
		const Unit* mineral_target = FindNearestMineralPatch(unit->pos);
		if (!mineral_target) {
			break;
		}
		Actions()->UnitCommand(unit, ABILITY_ID::SMART, mineral_target);
		break;
	}
	case UNIT_TYPEID::TERRAN_BARRACKS: {
		Actions()->UnitCommand(unit, ABILITY_ID::TRAIN_MARINE);
		break;
	}
	case UNIT_TYPEID::TERRAN_MARINE: {
		const GameInfo& game_info = Observation()->GetGameInfo();
		Actions()->UnitCommand(unit, ABILITY_ID::ATTACK_ATTACK, game_info.enemy_start_locations.front());
		break;
	}
	default: {
		break;
	}
	}
}

void Bot::OnUpgradeCompleted(UpgradeID upgrade_id) {
	std::cout << "Upgrade completed: " << sc2::UpgradeIDToName(upgrade_id) << std::endl;
}

void Bot::OnBuildingConstructionComplete(const Unit* unit) {
	std::cout << "Building construction completed: " << sc2::UnitTypeToName(unit->unit_type) << std::endl;
}

void Bot::OnNydusDetected() {
	std::cout << "Nydus detected" << std::endl;  // where?
}

void Bot::OnNuclearLaunchDetected() {
	std::cout << "Nuclear launch detected" << std::endl;  // where?
}

void Bot::OnUnitEnterVision(const Unit* unit) {
	std::cout << "Unit entered vision: " << sc2::UnitTypeToName(unit->unit_type) << std::endl;
}

void Bot::OnError(const std::vector<ClientError>& client_errors, const std::vector<std::string>& protocol_errors) {
	for (auto client_error : client_errors) {
		std::string errstr;
		switch (client_error) {
		case ClientError::ErrorSC2: {
			errstr = "ErrorSC2: some SC2 error (?)";
			break;
		}
		case ClientError::InvalidAbilityRemap: {
			errstr = "InvalidAbilityRemap: An ability was improperly mapped to an ability id that doesn't exist";
			break;
		}
		case ClientError::InvalidResponse: {
			errstr = "InvalidResponse: The response does not contain a field that was expected";
			break;
		}
		case ClientError::NoAbilitiesForTag: {
			errstr = "NoAbilitiesForTag: The unit does not have any abilities";
			break;
		}
		case ClientError::ResponseNotConsumed: {
			errstr = "ResponseNotConsumed: A request was made without consuming the response from the previous request, that puts this library in an illegal state";
			break;
		}
		case ClientError::ResponseMismatch: {
			errstr = "ResponseMismatch: The response received from SC2 does not match the request";
			break;
		}
		case ClientError::ConnectionClosed: {
			errstr = "ConnectionClosed: The websocket connection has prematurely closed, this could mean starcraft crashed or a websocket timeout has occurred";
			break;
		}
		case ClientError::SC2UnknownStatus: {
			errstr = "SC2UnknownStatus: some SC2 error";
			break;
		}
		case ClientError::SC2AppFailure: {
			errstr = "SC2AppFailure: SC2 has either crashed or been forcibly terminated by this library because it was not responding to requests";
			break;
		}
		case ClientError::SC2ProtocolError: {
			errstr = "SC2ProtocolError: The response from SC2 contains errors, most likely meaning the API was not used in a correct way";
			break;
		}
		case ClientError::SC2ProtocolTimeout: {
			errstr = "SC2ProtocolTimeout: A request was made and a response was not received in the amount of time given by the timeout";
			break;
		}
		case ClientError::WrongGameVersion: {
			errstr = "WrongGameVersion: A replay was attempted to be loaded in the wrong game version";
			break;
		}
		default: {
			errstr = "default: unknown error";
			break;
		}
		}

		std::cerr << "client error: " << errstr << std::endl;
	}

	for (auto protocol_error : protocol_errors) {
		std::cerr << "protocol error: " << protocol_error << std::endl;
	}
}

size_t Bot::CountUnitType(UNIT_TYPEID unit_type) {
	return Observation()->GetUnits(Unit::Alliance::Self, IsUnit(unit_type)).size();
}

bool Bot::TryBuildStructure(ABILITY_ID ability_type_for_structure, UNIT_TYPEID unit_type) {
	const ObservationInterface* observation = Observation();

	// If a unit already is building a supply structure of this type, do nothing.
	// Also get an scv to build the structure.
	const Unit* unit_to_build = nullptr;
	Units units = observation->GetUnits(Unit::Alliance::Self);
	for (const auto& unit : units) {
		for (const auto& order : unit->orders) {
			if (order.ability_id == ability_type_for_structure) {
				return false;
			}
		}

		if (unit->unit_type == unit_type) {
			unit_to_build = unit;
		}
	}

	float rx = GetRandomScalar();
	float ry = GetRandomScalar();

	Actions()->UnitCommand(unit_to_build,
		ability_type_for_structure,
		Point2D(unit_to_build->pos.x + rx * 15.0f, unit_to_build->pos.y + ry * 15.0f));

	return true;
}

bool Bot::TryBuildSupplyDepot() {
	const ObservationInterface* observation = Observation();

	// If we are not supply capped, don't build a supply depot.
	if (observation->GetFoodUsed() <= observation->GetFoodCap() - 2)
		return false;

	// Try and build a depot. Find a random SCV and give it the order.
	return TryBuildStructure(ABILITY_ID::BUILD_SUPPLYDEPOT);
}

const Unit* Bot::FindNearestMineralPatch(const Point2D& start) {
	Units units = Observation()->GetUnits(Unit::Alliance::Neutral);
	float distance = std::numeric_limits<float>::max();
	const Unit* target = nullptr;
	for (const auto& u : units) {
		if (u->unit_type == UNIT_TYPEID::NEUTRAL_MINERALFIELD) {
			float d = DistanceSquared2D(u->pos, start);
			if (d < distance) {
				distance = d;
				target = u;
			}
		}
	}
	return target;
}

bool Bot::TryBuildBarracks() {
	const ObservationInterface* observation = Observation();

	if (CountUnitType(UNIT_TYPEID::TERRAN_SUPPLYDEPOT) < 1) {
		return false;
	}

	if (CountUnitType(UNIT_TYPEID::TERRAN_BARRACKS) > 0) {
		return false;
	}

	return TryBuildStructure(ABILITY_ID::BUILD_BARRACKS);
}
