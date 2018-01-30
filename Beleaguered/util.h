#pragma once

#include "sc2api/sc2_api.h"

using namespace sc2;

const char* display_type_to_str(Unit::DisplayType);
const char* alliance_to_str(Unit::Alliance);
const char* cloak_state_to_str(Unit::CloakState);
void dump_unit(const Unit *);
