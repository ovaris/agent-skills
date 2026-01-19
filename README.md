# Agent Skills 🤖

A collection of functional skills and tools for Clawdbot and other AI agents. These skills are designed to provide structured, reliable access to various services and data sources.

## Available Skills

### 🇫🇮 [nordpool-fi](./nordpool-fi)
Fetches hourly electricity prices for the Finland region using the Porssisahko.net API.
- **Features:** Automatic UTC to Finland time conversion, 15-min data averaging, and optimal charging window calculation (3h, 4h, 5h).
- **Usage:** Perfect for home automation and EV charging optimization.

### 🚗 [tesla-commands](./tesla-commands)
Control your Tesla vehicle via the MyTeslaMate API.
- **Features:** Wake up vehicle, check battery status/location, set charge limits, and manage climate/schedules.
- **Usage:** Designed for multi-vehicle account support and automation.

---

## How to use

Each skill folder contains a `SKILL.md` file which serves as the manual for AI agents, and a `bin/` directory containing the executable scripts.

### Manual Installation
1. Clone this repository: `git clone https://github.com/ovaris/agent-skills.git`
2. Navigate to the desired skill.
3. Follow the instructions in the respective `SKILL.md`.

## Contributions
Feel free to open issues or PRs if you have suggestions for new skills or improvements to existing ones.

## License
MIT
