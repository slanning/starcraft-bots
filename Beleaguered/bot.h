#pragma once

#include "sc2api/sc2_api.h"
#include "sc2lib/sc2_lib.h"

using namespace sc2;

class Bot : public Agent {
private:
	size_t CountUnitType(UNIT_TYPEID unit_type);
	bool TryBuildStructure(ABILITY_ID ability_type_for_structure, UNIT_TYPEID unit_type = UNIT_TYPEID::TERRAN_SCV);
	bool TryBuildSupplyDepot();
	const Unit* FindNearestMineralPatch(const Point2D& start);
	bool TryBuildBarracks();

public:
	Bot();
	void OnGameStart() override;
	void OnStep() override;
	void OnUnitIdle(const Unit* unit) override;
};
