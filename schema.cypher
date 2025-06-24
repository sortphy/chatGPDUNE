// === CHARACTER ===
CREATE CONSTRAINT character_name_unique IF NOT EXISTS
FOR (c:Character)
REQUIRE c.name IS UNIQUE;

// Example properties (not enforced, just for documentation):
// - name: String
// - gender: String
// - birth_year: Integer or String
// - is_main: Boolean

// === HOUSE ===
CREATE CONSTRAINT house_name_unique IF NOT EXISTS
FOR (h:House)
REQUIRE h.name IS UNIQUE;

// Properties:
// - name: String
// - planet: String
// - status: String

// === PLANET ===
CREATE CONSTRAINT planet_name_unique IF NOT EXISTS
FOR (p:Planet)
REQUIRE p.name IS UNIQUE;

// Properties:
// - name: String
// - climate: String
// - famous_for: String

// === FACTION ===
CREATE CONSTRAINT faction_name_unique IF NOT EXISTS
FOR (f:Faction)
REQUIRE f.name IS UNIQUE;

// Properties:
// - name: String
// - type: String

// === SUBSTANCE ===
CREATE CONSTRAINT substance_name_unique IF NOT EXISTS
FOR (s:Substance)
REQUIRE s.name IS UNIQUE;

// Properties:
// - name: String
// - effect: String

// === ABILITY ===
CREATE CONSTRAINT ability_name_unique IF NOT EXISTS
FOR (a:Ability)
REQUIRE a.name IS UNIQUE;

// Properties:
// - name: String
// - granted_by: String

// === PROPHECY ===
CREATE CONSTRAINT prophecy_name_unique IF NOT EXISTS
FOR (p:Prophecy)
REQUIRE p.name IS UNIQUE;

// Properties:
// - name: String
// - description: String
