# Dune themed LLM using neo4j




# 📘 Dune Graph Schema (Neo4j)

This graph models the universe of *Dune* using Neo4j. The structure includes key entities (nodes) and how they relate (edges/relationships).

---

## 🧱 Node Types (Labels) and Properties

### 🧍‍♂️ `Character`
Represents a person in the Dune universe.
| Property     | Type    | Description                      |
|--------------|---------|----------------------------------|
| `name`       | String  | Full name (unique)               |
| `gender`     | String  | Optional                         |
| `birth_year` | String  | Optional                         |
| `is_main`    | Boolean | Whether this is a main character |

---

### 🏠 `House`
Represents a noble house or political faction.
| Property  | Type   | Description                     |
|-----------|--------|---------------------------------|
| `name`    | String | House name (unique)             |
| `planet`  | String | Home planet                     |
| `status`  | String | e.g. "Great House", "Fallen"    |

---

### 🌍 `Planet`
Represents a known planet in the universe.
| Property     | Type   | Description                |
|--------------|--------|----------------------------|
| `name`       | String | Planet name (unique)       |
| `climate`    | String | e.g. "Desert", "Temperate" |
| `famous_for` | String | e.g. "Spice", "Water"      |

---

### 🧕 `Faction`
Represents political, religious or military groups.
| Property  | Type   | Description                        |
|-----------|--------|------------------------------------|
| `name`    | String | Faction name (unique)              |
| `type`    | String | e.g. "Religious Order", "Tribal"   |

---

### 🌶️ `Substance`
Special materials or substances (e.g., spice).
| Property  | Type   | Description                       |
|-----------|--------|-----------------------------------|
| `name`    | String | Name of substance (unique)        |
| `effect`  | String | Description of its effects        |

---

### 🧠 `Ability`
Represents special powers or learned skills.
| Property     | Type   | Description                    |
|--------------|--------|--------------------------------|
| `name`       | String | Ability name (unique)          |
| `granted_by` | String | Source: training, spice, etc.  |

---

### 📜 `Prophecy`
Mystical predictions or religious beliefs.
| Property     | Type   | Description                    |
|--------------|--------|--------------------------------|
| `name`       | String | Prophecy name (unique)         |
| `description`| String | What the prophecy describes     |

---

## 🔗 Relationship Types

| Relationship             | From → To             | Description                            |
|--------------------------|-----------------------|----------------------------------------|
| `BELONGS_TO`             | `Character` → `House` | Character's house affiliation          |
| `CONTROLS`               | `House` → `Planet`    | Which planet a house rules             |
| `LIVES_ON`               | `Character` → `Planet`| Where a character currently resides    |
| `PART_OF`                | `Character` → `Faction`| Group or order membership             |
| `CONSUMES`               | `Character` → `Substance`| Use of spice or other materials     |
| `FOUND_ON`               | `Substance` → `Planet`| Where the material is sourced          |
| `HAS_ABILITY`            | `Character` → `Ability`| Powers or learned skills              |
| `FOLLOWS_PROPHECY`       | `Character` → `Prophecy`| Linked to belief systems             |
| `ENEMY_OF`               | `Character` → `Character`| Known enmity                          |
| `MARRIED_TO`             | `Character` ↔ `Character`| Marriage (bidirectional)             |
| `AT_WAR_WITH`            | `House` ↔ `House`      | Hostility between houses               |
| `OPPOSES`                | `Faction` ↔ `Faction`  | Conflict between groups                |
