# note: this has some things specific to my current macro practice/drill for Terran
# so...sorry I didn't vibe-code other SC2 factions

# activate venv: source venv/Scripts/activate
# example execution:
# $ python analyze_build.py <SC2 username> "C:\Users\<...>\Replays\Multiplayer\Old Sun Temple LE (2).SC2Replay"
# for installing s2protocol see end of this file
import pprint
import sys
import mpyq
from s2protocol import versions

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_build.py <SC2 username> <replay file name>")
        sys.exit(1)
    analyze_macro_drill(sys.argv[2], sys.argv[1], debug=False)

def analyze_macro_drill(replay_path, my_player_name, debug=True):
    if debug:
        print("opening replay: " + replay_path)
    
    # 1. Open MPQ archive
    archive = mpyq.MPQArchive(replay_path)
    
    # 2. Extract header and base build version
    header_contents = archive.header['user_data_header']['content']
    header = versions.latest().decode_replay_header(header_contents)
    base_build = header['m_version']['m_baseBuild']
    protocol = versions.build(base_build)
    
    # 3. Decode Details to find your Player ID
    details_data = archive.read_file('replay.details')
    details = protocol.decode_replay_details(details_data)
    
    my_player_id_1based = None
    for idx, player in enumerate(details['m_playerList'], start=1):
        name = player.get('m_name', b'')
        if isinstance(name, bytes):
            name = name.decode('utf-8', errors='ignore')
        if name.lower() == my_player_name.lower():
            my_player_id_1based = idx
            break
            
    if not my_player_id_1based:
        print(f"Error: Could not find player matching '{my_player_name}' in replay details.")
        return

    # 4. Decode Tracker Events
    tracker_data = archive.read_file('replay.tracker.events')
    tracker_events = list(protocol.decode_replay_tracker_events(tracker_data))

    LOOPS_PER_SEC = 22.4   # Standard for 'Faster' game speed
    
    building_events = []
    unit_production_events = []
    
    scv_count = 0
    marine_count = 0
    
    target_minutes = {120: "2:00", 180: "3:00", 240: "4:00", 300: "5:00"}
    snapshots = {}
    
    final_minerals = 0
    final_supply_used = 0
    final_supply_max = 0
    final_seconds = 0
    num_supply_depots = 0
    num_barracks = 0
    num_ccs = 1

    food_used = 0
    food_made = 0

    # Initialize tracking for the closest snapshot to each target minute
    best_snapshot_diff = {t_sec: float('inf') for t_sec in target_minutes.keys()}

    last_stats_loop = {}
    last_was_capped = {}  # Track whether the player was capped at the previous stats event
    supply_capped_seconds = 0.0

    # Dictionaries to track mapping data safely over missing structural keys
    unit_tag_registry = {}
    building_owner_registry = {}

    my_user_id = None
    for setup_event in tracker_events:
        if (
            'PlayerSetup' in setup_event.get('_event', '')
            and setup_event.get('m_playerId') == my_player_id_1based
        ):
            my_user_id = setup_event.get('m_userId')
            break

    for event in tracker_events:
        evt_type = event.get('_event', '')
        loop = event.get('_gameloop', 0)
        seconds = loop / LOOPS_PER_SEC
        if 'PlayerStats' in evt_type:
            final_seconds = seconds
        
        p_id_stats = event.get('m_playerId')
        control_id = event.get('m_controlPlayerId')
        tag_idx    = event.get('m_unitTagIndex')
        
        is_stats_match = (p_id_stats == my_player_id_1based)
        is_unit_match = (control_id == my_player_id_1based)

        # Cache types and builders globally since UnitDone drops player ID metrics completely
        if tag_idx is not None:
            unit_type_raw = event.get('m_unitTypeName', b'')
            if isinstance(unit_type_raw, bytes):
                unit_type_raw = unit_type_raw.decode('utf-8', errors='ignore')
            if unit_type_raw:
                unit_tag_registry[tag_idx] = unit_type_raw
            if is_unit_match:
                building_owner_registry[tag_idx] = True

        if debug and loop > 0 and is_unit_match:
            pprint.pprint(event)

        # Process Player Stats (Snapshots & Supply Blocks)
        if 'PlayerStats' in evt_type and is_stats_match:
            stats = event.get('m_stats', {})
            food_used = stats.get('m_scoreValueFoodUsed', 0) // 4096
            food_made = stats.get('m_scoreValueFoodMade', 0) // 4096
            minerals = stats.get('m_scoreValueCurrentMinerals', stats.get('m_scoreValueMineralsCurrent', 0))

            is_currently_capped = (food_used >= food_made and food_made > 0)

            if p_id_stats in last_stats_loop:
                delta_loops = loop - last_stats_loop[p_id_stats]
                delta_seconds = delta_loops / LOOPS_PER_SEC

                was_capped_before = last_was_capped.get(p_id_stats, False)
                if is_currently_capped and was_capped_before:
                    supply_capped_seconds += delta_seconds
                elif is_currently_capped or was_capped_before:
                    supply_capped_seconds += (delta_seconds / 2.0)
            
            last_stats_loop[p_id_stats] = loop
            last_was_capped[p_id_stats] = is_currently_capped

            for t_sec in target_minutes.keys():
                target_loop = int(t_sec * LOOPS_PER_SEC)
                diff = abs(loop - target_loop)
                if diff < best_snapshot_diff[t_sec]:
                    best_snapshot_diff[t_sec] = diff
                    snapshots[t_sec] = {
                        "minerals": minerals,
                        "supply_used": food_used,
                        "supply_max": food_made
                    }
                
            final_minerals = minerals
            final_supply_used = food_used
            final_supply_max = food_made

        # Process Building / Unit Events (Ignoring loop 0 map initialization)
        elif ('UnitInit' in evt_type or 'UnitBorn' in evt_type or 'UnitDone' in evt_type) and loop > 0:
            # Check either explicit matching or cached tag lookup for owner state
            if not is_unit_match and not building_owner_registry.get(tag_idx, False):
                continue

            unit_type = unit_tag_registry.get(tag_idx, 'Unknown')
            if debug:
                print("unit_type: " + unit_type)
            
            total_scv_count = scv_count + 12
            mm = int(seconds // 60)
            ss = int(seconds % 60)
            time_str = f"{mm:02d}:{ss:02d}"

            # ----------------------------------------------------
            # 1. UNIT PRODUCTION EVENTS
            # ----------------------------------------------------
            # UnitBorn gives the completion loop. Tracker events do not
            # provide the actual start of ordinary SCV/Marine training.
            # Infer it by subtracting the standard training duration.
            unit_event_desc = None
            unit_label = None
            training_seconds = None

            if 'UnitBorn' in evt_type:
                if 'SCV' in unit_type:
                    scv_count += 1
                    total_scv_count = scv_count + 12
                    unit_label = 'SCV'
                    training_seconds = 12.0
                    unit_event_desc = (
                        f"SCV completed (SCVs: {total_scv_count}, "
                        f"Marines: {marine_count})"
                    )
                elif 'Marine' in unit_type:
                    marine_count += 1
                    unit_label = 'Marine'
                    training_seconds = 18.0
                    unit_event_desc = (
                        f"Marine completed (SCVs: {total_scv_count}, "
                        f"Marines: {marine_count})"
                    )

            if unit_label is not None and training_seconds is not None:
                # This is an inferred production-start time, not a recorded
                # tracker event. The standard train time is assumed to apply.
                training_loops = round(training_seconds * LOOPS_PER_SEC)
                start_loop = max(0, loop - training_loops)
                start_seconds = start_loop / LOOPS_PER_SEC
                start_mm = int(start_seconds // 60)
                start_ss = int(start_seconds % 60)
                start_time_str = f"{start_mm:02d}:{start_ss:02d}"

                unit_production_events.append((
                    start_loop,
                    start_time_str,
                    f"{unit_label} training started (inferred; "
                    f"{training_seconds:g}s train time)"
                ))

            if unit_event_desc:
                unit_production_events.append((loop, time_str, unit_event_desc))

            # ----------------------------------------------------
            # 2. BUILDING EVENTS (Starts & Completions)
            # ----------------------------------------------------
            is_building = unit_type and not any(u in unit_type for u in ['SCV', 'Marine', 'Probe', 'Zealot', 'Stalker', 'Observer', 'Sentry'])

            if is_building:
                if 'UnitInit' in evt_type:
                    building_events.append((time_str, f"{unit_type} started (supply: {food_used}/{food_made}, SCVs: {total_scv_count} Marines: {marine_count})"))

                elif 'UnitDone' in evt_type:
                    building_events.append((time_str, f"{unit_type} completed (supply: {food_used}/{food_made}, SCVs: {total_scv_count} Marines: {marine_count})"))
                    
                    if 'SupplyDepot' in unit_type:
                        num_supply_depots += 1
                    elif 'Barracks' in unit_type:
                        num_barracks += 1
                    elif 'CommandCenter' in unit_type:
                        num_ccs += 1

    if my_user_id is not None:
        game_data = archive.read_file('replay.game.events')
        ability_summary = {}

        for event in protocol.decode_replay_game_events(game_data):
            if event.get('_event') != 'NNet.Game.SCmdEvent':
                continue

            raw_user_id = event.get('_userid', {})
            user_id = (
                raw_user_id.get('m_userId')
                if isinstance(raw_user_id, dict)
                else raw_user_id
            )

            if user_id != my_user_id:
                continue

            ability = event.get('m_abil')
            if not ability:
                continue

            key = (
                ability.get('m_abilLink'),
                ability.get('m_abilCmdIndex')
            )

            entry = ability_summary.setdefault(
                key, {"count": 0, "first_times": []}
            )
            entry["count"] += 1

            if len(entry["first_times"]) < 5:
                seconds = event['_gameloop'] / LOOPS_PER_SEC
                mm = int(seconds // 60)
                ss = int(seconds % 60)
                entry["first_times"].append(f"{mm:02d}:{ss:02d}")

        if debug:
            print("\nCOMMAND ABILITY DIAGNOSTICS")
            for (link, cmd), info in sorted(ability_summary.items()):
                times = ", ".join(info["first_times"])
                print(
                    f"Ability link: {link}, command: {cmd}, "
                    f"count: {info['count']}, first times: {times}"
                )
    else:
        print("\nCould not map player to game-event user ID.")

    # Print Formatted Report matching your target design
    print("=" * 40)
    print(" REPLAY: Terran Macro Drill Report")
    print("=" * 40)
    minutes, seconds = divmod(final_seconds, 60)
    print(f"Duration: {int(minutes):02d}:{seconds:05.2f}\n")
    
    print("BUILDING EVENTS")
    if building_events:
        for t_str, desc in building_events:
            print(f"{t_str}  {desc}")
    else:
        print("No matching building events recorded.")

    print("\nUNIT PRODUCTION EVENTS (INFERRED STARTS + COMPLETIONS)")
    if unit_production_events:
        for _, t_str, desc in sorted(
            unit_production_events, key=lambda item: item[0]
        ):
            print(f"{t_str}  {desc}")
    else:
        print("No matching unit production events recorded.")

    print("\nBUILDINGS")
    print(f"Supply Depots: {num_supply_depots}")
    print(f"Barracks: {num_barracks}")
    print(f"CommandCenters: {num_ccs}")

    print(f"\nUNIT PRODUCTION")
    print(f"SCVs produced:    {scv_count} (plus 12 started with)")
    print(f"Marines produced: {marine_count}")
    
    print(f"\nSNAPSHOTS")
    for t_sec, label in target_minutes.items():
        snap = snapshots.get(t_sec, {"minerals": 0, "supply_used": 0, "supply_max": 0})
        print(f"{label}     Supply: {snap['supply_used']}/{snap['supply_max']} | Minerals Bank: {snap['minerals']}")

    print(f"\nFINAL SUMMARY")
    print(f"Minerals Bank: {final_minerals}")
    print(f"Supply:        {final_supply_used}/{final_supply_max}")
    cap_sec = int(supply_capped_seconds)
    print(f"Time Supply Capped: {cap_sec // 60}:{cap_sec % 60:02d}")
    print("=" * 40)


if __name__ == "__main__":
    main()

# r quote because there's Windows "C:\Users" file paths and python thinks "\U" is some unicode escape sequence

r"""
I'm not normally a python or Windows programmer, so... I'm doing this from "Git Bash" with some vibing with Gemini and ChatGPT.

You need to install python and pip first.

### Step 1: Verify Python and Git Bash

(in Git Bash terminal)

python --version
# or python3 --version

pip --version

*Note: If `python` isn't found or points to the Windows Microsoft Store stub, make sure Python is added to your Windows PATH environment variable.*

### Step 2: Create a Workspace and Virtual Environment

In Python, it's best practice to use a virtual environment (`venv`) for projects so you don't pollute your global Python installation.

In Git Bash, navigate to where you want to keep your project and set things up:

[note: on Windows this doesn't work, but see below]

```bash
# Create a project folder and enter it
mkdir sc2-parser
cd sc2-parser

# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment (syntax for Git Bash / Linux style)
source venv/bin/activate

```

Once activated, your terminal prompt will usually change to show `(venv)` on the left. (To deactivate later when you're done, you can just type `deactivate`).


In Step 2, I did I did `mkdir sc2-parser; cd sc2-parser; python -m venv venv;` but for `source venv/bin/activate` there's no `bin` directory under `venv`.
Instead, there is a `venv/Scripts/` directory; here's how it tab-completes under that:

```
$ source venv/Scripts/
Activate.ps1    activate.bat    deactivate.bat  pip3.15.exe     python.exe
activate        activate.fish   pip.exe         pip3.exe        pythonw.exe
``` 

Gemini said my setup was fine, but instead use `source venv/Scripts/activate` on Windows.
That seems to've worked, and both python and pip point to the sc2-parser/venv/Scripts/ directory.


Step 3)
pip install --upgrade pip          # this gave an error, but I just ran the next install part	
pip install s2protocol mpyq

Then at the end of that it said:

[notice] A new release of pip is available: 26.2.2 -> 26.3
[notice] To update, run: python.exe -m pip install --upgrade pip

I ran that and it worked.


Step 4)

This is a script to test if you have things installed correctly:

$ cat parse_replay.py

import mpyq
from s2protocol import versions

# parse_replay.py
# make sure to activate venv: source venv/Scripts/activate

# Path to a StarCraft II replay file on Windows
# Note: In Python strings, either use raw strings (r"C:\...") or forward slashes
# CHANGE THIS
#replay_path = r"C:\Users\YOUR_USERNAME\Documents\StarCraft II\Accounts\..." 

# 1. Open the MPQ archive
archive = mpyq.MPQArchive(replay_path)

# 2. Extract the header data
contents = archive.header['user_data_header']['content']

# 3. Decode the header using the latest version module
# (s2protocol dynamically handles multiple game versions)
header = versions.latest().decode_replay_header(contents)

print(f"Game Base Build: {header['m_version']['m_baseBuild']}")
print("Replay successfully parsed!")


Step 5)
$ python parse_replay.py
Traceback (most recent call last):
  File "C:\Users\[myuser]\SC2\sc2-parser\parse_replay.py", line 2, in <module>
    from s2protocol import versions
  File "C:\Users\[myuser]\SC2\sc2-parser\venv\Lib\site-packages\s2protocol\versions\__init__.py", line 4, in <module>
    import imp
ModuleNotFoundError: No module named 'imp'

Gemini says this is because my python is too new... Following its instructions:
Downloading Python 3.11.0b5 - July 26, 2022 (from https://www.python.org/downloads/windows/ )
(there were some .0rc versions later than that, but I assumed they were release candidates for the next version)
Start the installer and make sure it adds this version to PATH
In git bash, sc2-parser directory wipe out old venv:
deactivate
rm -r venv

Create a new venv:
py -3.11 -m venv venv

source venv/Scripts/activate
pip install --upgrade pip   # same error as before, use this instead: python.exe -m pip install --upgrade pip
pip install s2protocol mpyq

$ pip --version
pip 26.3 from C:\Users\lanni\SC2\sc2-parser\venv\Lib\site-packages\pip (python 3.11)
[that upgraded from 22.2]

Try running the script again: (this is in the new venv in git bash)
$ python parse_replay.py
Game Base Build: 98310
Replay successfully parsed!

Yay...
"""


"""

Example output:

========================================
 REPLAY: Terran Macro Drill Report
========================================
Duration: 05:01.61

BUILDING EVENTS
00:19  SupplyDepot started (supply: 14/15, SCVs: 13 Marines: 0)
00:40  SupplyDepot completed (supply: 15/15, SCVs: 15 Marines: 0)
00:42  Barracks started (supply: 15/15, SCVs: 15 Marines: 0)
01:28  Barracks completed (supply: 19/23, SCVs: 18 Marines: 0)
01:29  SupplyDepot started (supply: 19/23, SCVs: 18 Marines: 0)
01:39  CommandCenter started (supply: 20/23, SCVs: 19 Marines: 0)
01:50  SupplyDepot completed (supply: 22/23, SCVs: 20 Marines: 0)
02:02  SupplyDepot started (supply: 24/31, SCVs: 21 Marines: 1)
02:14  Barracks started (supply: 25/31, SCVs: 22 Marines: 2)
02:23  SupplyDepot completed (supply: 27/31, SCVs: 23 Marines: 2)
02:35  Barracks started (supply: 27/39, SCVs: 24 Marines: 3)
02:49  SupplyDepot started (supply: 30/39, SCVs: 25 Marines: 4)
02:50  CommandCenter completed (supply: 30/39, SCVs: 25 Marines: 4)
03:00  Barracks completed (supply: 33/54, SCVs: 26 Marines: 4)
03:08  Barracks started (supply: 34/54, SCVs: 28 Marines: 5)
03:11  SupplyDepot completed (supply: 34/54, SCVs: 28 Marines: 5)
03:22  Barracks completed (supply: 39/62, SCVs: 30 Marines: 5)
03:36  SupplyDepot started (supply: 44/62, SCVs: 32 Marines: 7)
03:47  Barracks started (supply: 45/62, SCVs: 34 Marines: 10)
03:54  Barracks completed (supply: 49/62, SCVs: 35 Marines: 10)
03:58  SupplyDepot completed (supply: 51/62, SCVs: 36 Marines: 10)
04:26  SupplyDepot started (supply: 63/70, SCVs: 40 Marines: 17)
04:33  Barracks completed (supply: 64/70, SCVs: 42 Marines: 17)
04:46  SupplyDepot started (supply: 70/70, SCVs: 44 Marines: 21)
04:47  SupplyDepot completed (supply: 70/70, SCVs: 44 Marines: 21)

UNIT PRODUCTION EVENTS (INFERRED STARTS + COMPLETIONS)
00:00  SCV training started (inferred; 12s train time)
00:12  SCV completed (SCVs: 13, Marines: 0)
00:12  SCV training started (inferred; 12s train time)
00:24  SCV completed (SCVs: 14, Marines: 0)
00:26  SCV training started (inferred; 12s train time)
00:38  SCV completed (SCVs: 15, Marines: 0)
00:40  SCV training started (inferred; 12s train time)
00:52  SCV completed (SCVs: 16, Marines: 0)
00:52  SCV training started (inferred; 12s train time)
01:04  SCV completed (SCVs: 17, Marines: 0)
01:04  SCV training started (inferred; 12s train time)
01:16  SCV completed (SCVs: 18, Marines: 0)
01:18  SCV training started (inferred; 12s train time)
01:30  SCV completed (SCVs: 19, Marines: 0)
01:30  SCV training started (inferred; 12s train time)
01:36  Marine training started (inferred; 18s train time)
01:42  SCV completed (SCVs: 20, Marines: 0)
01:42  SCV training started (inferred; 12s train time)
01:54  Marine training started (inferred; 18s train time)
01:54  Marine completed (SCVs: 20, Marines: 1)
01:54  SCV completed (SCVs: 21, Marines: 1)
01:54  SCV training started (inferred; 12s train time)
02:06  SCV completed (SCVs: 22, Marines: 1)
02:06  SCV training started (inferred; 12s train time)
02:12  Marine training started (inferred; 18s train time)
02:12  Marine completed (SCVs: 22, Marines: 2)
02:18  SCV completed (SCVs: 23, Marines: 2)
02:18  SCV training started (inferred; 12s train time)
02:29  Marine training started (inferred; 18s train time)
02:30  Marine completed (SCVs: 23, Marines: 3)
02:30  SCV completed (SCVs: 24, Marines: 3)
02:30  SCV training started (inferred; 12s train time)
02:42  SCV completed (SCVs: 25, Marines: 3)
02:42  SCV training started (inferred; 12s train time)
02:47  Marine training started (inferred; 18s train time)
02:47  Marine completed (SCVs: 25, Marines: 4)
02:53  SCV training started (inferred; 12s train time)
02:55  SCV completed (SCVs: 26, Marines: 4)
02:55  SCV training started (inferred; 12s train time)
03:05  Marine training started (inferred; 18s train time)
03:05  Marine completed (SCVs: 26, Marines: 5)
03:05  SCV completed (SCVs: 27, Marines: 5)
03:05  SCV training started (inferred; 12s train time)
03:07  SCV completed (SCVs: 28, Marines: 5)
03:07  SCV training started (inferred; 12s train time)
03:08  Marine training started (inferred; 18s train time)
03:17  SCV completed (SCVs: 29, Marines: 5)
03:17  SCV training started (inferred; 12s train time)
03:19  SCV completed (SCVs: 30, Marines: 5)
03:19  SCV training started (inferred; 12s train time)
03:23  Marine training started (inferred; 18s train time)
03:23  Marine completed (SCVs: 30, Marines: 6)
03:26  Marine training started (inferred; 18s train time)
03:26  Marine completed (SCVs: 30, Marines: 7)
03:27  Marine training started (inferred; 18s train time)
03:29  SCV completed (SCVs: 31, Marines: 7)
03:30  SCV training started (inferred; 12s train time)
03:31  SCV completed (SCVs: 32, Marines: 7)
03:31  SCV training started (inferred; 12s train time)
03:41  Marine training started (inferred; 18s train time)
03:41  Marine completed (SCVs: 32, Marines: 8)
03:42  SCV completed (SCVs: 33, Marines: 8)
03:42  SCV training started (inferred; 12s train time)
03:43  SCV completed (SCVs: 34, Marines: 8)
03:43  SCV training started (inferred; 12s train time)
03:43  Marine training started (inferred; 18s train time)
03:44  Marine completed (SCVs: 34, Marines: 9)
03:44  Marine training started (inferred; 18s train time)
03:45  Marine completed (SCVs: 34, Marines: 10)
03:54  SCV completed (SCVs: 35, Marines: 10)
03:54  SCV training started (inferred; 12s train time)
03:55  SCV completed (SCVs: 36, Marines: 10)
03:55  SCV training started (inferred; 12s train time)
03:58  Marine training started (inferred; 18s train time)
03:59  Marine completed (SCVs: 36, Marines: 11)
04:00  Marine training started (inferred; 18s train time)
04:01  Marine training started (inferred; 18s train time)
04:01  Marine completed (SCVs: 36, Marines: 12)
04:02  Marine training started (inferred; 18s train time)
04:02  Marine completed (SCVs: 36, Marines: 13)
04:06  SCV completed (SCVs: 37, Marines: 13)
04:06  SCV training started (inferred; 12s train time)
04:07  SCV completed (SCVs: 38, Marines: 13)
04:07  SCV training started (inferred; 12s train time)
04:16  Marine training started (inferred; 18s train time)
04:16  Marine completed (SCVs: 38, Marines: 14)
04:18  Marine training started (inferred; 18s train time)
04:18  Marine completed (SCVs: 38, Marines: 15)
04:18  SCV completed (SCVs: 39, Marines: 15)
04:18  SCV training started (inferred; 12s train time)
04:19  Marine training started (inferred; 18s train time)
04:19  Marine completed (SCVs: 39, Marines: 16)
04:19  SCV completed (SCVs: 40, Marines: 16)
04:19  SCV training started (inferred; 12s train time)
04:20  Marine training started (inferred; 18s train time)
04:20  Marine completed (SCVs: 40, Marines: 17)
04:30  SCV completed (SCVs: 41, Marines: 17)
04:30  SCV training started (inferred; 12s train time)
04:31  SCV completed (SCVs: 42, Marines: 17)
04:31  SCV training started (inferred; 12s train time)
04:34  Marine training started (inferred; 18s train time)
04:34  Marine completed (SCVs: 42, Marines: 18)
04:35  Marine training started (inferred; 18s train time)
04:36  Marine completed (SCVs: 42, Marines: 19)
04:37  Marine training started (inferred; 18s train time)
04:37  Marine training started (inferred; 18s train time)
04:37  Marine completed (SCVs: 42, Marines: 20)
04:38  Marine training started (inferred; 18s train time)
04:38  Marine completed (SCVs: 42, Marines: 21)
04:42  SCV completed (SCVs: 43, Marines: 21)
04:43  SCV completed (SCVs: 44, Marines: 21)
04:47  SCV training started (inferred; 12s train time)
04:47  SCV training started (inferred; 12s train time)
04:52  Marine completed (SCVs: 44, Marines: 22)
04:53  Marine completed (SCVs: 44, Marines: 23)
04:55  Marine completed (SCVs: 44, Marines: 24)
04:55  Marine completed (SCVs: 44, Marines: 25)
04:56  Marine completed (SCVs: 44, Marines: 26)
04:59  SCV completed (SCVs: 45, Marines: 26)
04:59  SCV completed (SCVs: 46, Marines: 26)

BUILDINGS
Supply Depots: 6
Barracks: 5
CommandCenters: 2

UNIT PRODUCTION
SCVs produced:    34 (plus 12 started with)
Marines produced: 26

SNAPSHOTS
2:00     Supply: 24/31 | Minerals Bank: 100
3:00     Supply: 33/54 | Minerals Bank: 190
4:00     Supply: 54/70 | Minerals Bank: 85
5:00     Supply: 78/78 | Minerals Bank: 105

FINAL SUMMARY
Minerals Bank: 135
Supply:        78/78
Time Supply Capped: 0:33
========================================


"""
