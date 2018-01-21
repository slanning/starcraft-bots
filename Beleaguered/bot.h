#pragma once

#include "sc2api/sc2_api.h"
#include "sc2lib/sc2_lib.h"

using namespace sc2;

class Bot : public Agent {
private:
	bool TryBuildStructure(ABILITY_ID ability_type_for_structure, UNIT_TYPEID unit_type = UNIT_TYPEID::TERRAN_SCV);
	bool TryBuildSupplyDepot();
	bool TryBuildBarracks();
	size_t CountUnitType(UNIT_TYPEID unit_type);
	const Unit* FindNearestMineralPatch(const Point2D& start);

public:
	Bot();
	void OnGameStart() override;
	void OnGameEnd() override;
	void OnStep() override;
	void OnUnitIdle(const Unit* unit) override;
	void OnUnitCreated(const Unit* unit) override;
};
