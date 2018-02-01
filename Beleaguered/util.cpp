#include <iostream>

#include "util.h"

// maybe should pass Unit* for these
const char* display_type_to_str(Unit::DisplayType t) {
	switch (t) {
	case Unit::DisplayType::Visible:   return "Visible";
	case Unit::DisplayType::Snapshot:  return "Snapshot";
	case Unit::DisplayType::Hidden:    return "Hidden";
	}
	return "UNKNOWN";
}

const char* alliance_to_str(Unit::Alliance a) {
	switch (a) {
	case Unit::Alliance::Self:     return "Self";
	case Unit::Alliance::Ally:     return "Ally";
	case Unit::Alliance::Neutral:  return "Neutral";
	case Unit::Alliance::Enemy:    return "Enemy";
	}
	return "UNKNOWN";
}

const char* cloak_state_to_str(Unit::CloakState c) {
	switch (c) {
	case Unit::CloakState::Cloaked:          return "Cloaked";
	case Unit::CloakState::CloakedDetected:  return "CloakedDetected";
	case Unit::CloakState::NotCloaked:       return "NotCloaked";
	case Unit::CloakState::Unknown:          return "Unknown";
	}
	return "UNKNOWN";
}

void dump_unit(const Unit *u) {
	std::cout
		<< "unit tag: " << u->tag << std::endl
		<< "\tdisplay_type: " << display_type_to_str(u->display_type) << " (" << u->display_type << ")" << std::endl
		<< "\talliance: " << alliance_to_str(u->alliance) << " (" << u->alliance << ")" << std::endl
		<< "\tunit_type: " << UnitTypeToName(u->unit_type) << " (" << u->unit_type << ")" << std::endl
		<< "\towner: player " << u->owner << std::endl // player 16 is "neutral"
		<< "\tpos x: " << u->pos.x << " y: " << u->pos.y << " z: " << u->pos.z << std::endl
		<< "\tfacing: " << u->facing << " radians" << std::endl
		<< "\tradius: " << u->radius << std::endl
		<< "\tbuild_progress: " << u->build_progress << std::endl
		<< "\tcloak: " << cloak_state_to_str(u->cloak) << " (" << u->cloak << ")" << std::endl
		<< "\tdetect_range: " << u->detect_range << std::endl
		<< "\tradar_range: " << u->radar_range << std::endl
		<< "\tis_selected: " << u->is_selected << std::endl
		<< "\tis_on_screen: " << u->is_on_screen << std::endl
		<< "\tis_blip: " << u->is_blip << std::endl
		;

	if (u->display_type != Unit::DisplayType::Snapshot) {
		std::cout
			<< "\thealth: " << u->health << std::endl
			<< "\thealth_max: " << u->health_max << std::endl
			<< "\tshield: " << u->shield_max << std::endl
			<< "\tshield_max: " << u->shield_max << std::endl
			<< "\tenergy: " << u->energy << std::endl
			<< "\tenergy_max: " << u->energy_max << std::endl
			<< "\tmineral_contents: " << u->mineral_contents << std::endl
			<< "\tvespene_contents: " << u->vespene_contents << std::endl
			<< "\tis_flying: " << u->is_flying << std::endl
			<< "\tis_burrowed: " << u->is_burrowed << std::endl
			<< "\tweapon_cooldown: " << u->weapon_cooldown << std::endl
			;
	}

	// docs are a bit confusing here:
	// "Not populated for enemies/snapshots" vs "Only valid for this player's units"
	if (u->alliance == Unit::Alliance::Self) {
		std::cout << "\torders: " << std::endl;
		for (auto o : u->orders) {
			Point2D pos = o.target_pos;
			std::cout
				<< "\t\tability_id: " << AbilityTypeToName(o.ability_id) << " (" << o.ability_id << ")" << std::endl
				<< "\t\ttarget_unit_tag: " << o.target_unit_tag << std::endl
				// I'm not sure if pos can be NULL...
				<< "\t\ttarget_pos: " << "(" << (&pos && pos.x) << "," + (&pos && pos.y) << ")" << std::endl
				<< "\t\tprogress: " << o.progress << std::endl
				;
		}

		std::cout << "\tadd_on_tag: " << u->add_on_tag << std::endl;   // what if it's not an add-on?
		std::cout << "\tpassengers: ";
		for (const auto p : u->passengers) {
			std::cout
				<< "\t\ttag: " << p.tag << std::endl
				<< "\t\thealth: " << p.health << std::endl
				<< "\t\thealth_max: " << p.health_max << std::endl
				<< "\t\tshield: " << p.shield_max << std::endl
				<< "\t\tshield_max: " << p.shield_max << std::endl
				<< "\t\tenergy: " << p.energy << std::endl
				<< "\t\tenergy_max: " << p.energy_max << std::endl
				<< "\t\tunit_type: " << UnitTypeToName(p.unit_type) << " (" << p.unit_type << ")" << std::endl
				;
		}

		std::cout
			<< "\tcargo_space_taken: " << u->cargo_space_taken << std::endl
			<< "\tcargo_space_max: " << u->cargo_space_max << std::endl
			<< "\tassigned_harvesters: " << u->assigned_harvesters << std::endl
			<< "\tideal_harvesters: " << u->ideal_harvesters << std::endl
			<< "\tengaged_target_tag: " << u->engaged_target_tag << std::endl
			;

		std::cout << "\tbuffs: ";
		for (auto b : u->buffs) {
			std::cout << "\t\t" << BuffIDToName(b) << " (" << b << ")" << std::endl;
		}
	}

	std::cout
		<< "\tis_powered: " << u->is_powered << std::endl  // is this only valid for player's units?
		<< "\tbool is_alive: " << u->is_alive << std::endl
		<< "\tlast_seen_game_loop: " << u->last_seen_game_loop << std::endl
		;
}

const char* player_type_to_str(PlayerType t) {
	switch (t) {
	case PlayerType::Participant:  return "Participant";
	case PlayerType::Computer:     return "Computer";
	case PlayerType::Observer:     return "Observer";
	}
	return "UNKNOWN";
}

const char* race_to_str(Race r) {
	switch (r) {
	case Race::Terran:   return "Terran";
	case Race::Zerg:     return "Zerg";
	case Race::Protoss:  return "Protoss";
	case Race::Random:   return "Random";
	}
	return "UNKNOWN";
}

const char* difficulty_to_str(Difficulty d) {
	switch (d) {
	case Difficulty::VeryEasy:      return "VeryEasy";
	case Difficulty::Easy:          return "Easy";
	case Difficulty::Medium:        return "Medium";
	case Difficulty::MediumHard:    return "MediumHard";
	case Difficulty::Hard:          return "Hard";
	case Difficulty::HardVeryHard:  return "HardVeryHard";
	case Difficulty::VeryHard:      return "VeryHard";
	case Difficulty::CheatVision:   return "CheatVision";
	case Difficulty::CheatMoney:    return "CheatMoney";
	case Difficulty::CheatInsane:   return "CheatInsane";
	}
	return "UNKNOWN";
}

void dump_game_info(const GameInfo& g) {
	std::cout
		<< "map_name: " << g.map_name << std::endl
		<< "map width x height: " << g.width << " x " << g.height << std::endl
		//! Grid showing which cells are pathable by units.
		//ImageData pathing_grid;
		//! Height map of terrain.
		//ImageData terrain_height;
		//! Grid showing which cells can accept placement of structures.
		//ImageData placement_grid;
		<< "playable_min - _max: (" << g.playable_min.x << "," << g.playable_min.y << ") - (" << g.playable_max.x << "," << g.playable_max.y << ")" << std::endl
		;

	std::cout << "enemy_start_locations:" << std::endl;
	for (auto eloc : g.enemy_start_locations) {
		std::cout << "\t(" << eloc.x << "," << eloc.y << ")" << std::endl;
	}

	// TODO: convenience function to get one's own start location
	// TODO: function that translates location to direction/quadrant of the map
	std::cout << "start_locations:" << std::endl;
	for (auto loc : g.start_locations) {
		std::cout << "\t(" << loc.x << "," << loc.y << ")" << std::endl;
	}

	// InterfaceOptions options;

	std::cout << "player_info:" << std::endl;
	for (auto p : g.player_info) {
		std::cout
			<< "\tplayer_id: " << p.player_id << std::endl
			<< "\tplayer_type: " << player_type_to_str(p.player_type) << " (" << p.player_type << ")" << std::endl
			<< "\trace_requested: " << race_to_str(p.race_requested) << " (" << p.race_requested << ")" << std::endl
			<< "\trace_actual: " << race_to_str(p.race_actual) << " (" << p.race_actual << ")" << std::endl
			<< "\tdifficulty: " << difficulty_to_str(p.difficulty) << " (" << p.difficulty << ")" << std::endl
			;
	}
}