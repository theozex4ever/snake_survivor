# Snake Survivor

A snake game where the snake auto-fires at waves of enemies that chase it, and the player picks an upgrade between waves.

## Language

**Run**:
One play-through, from choosing a speed until the snake dies. Score, upgrades and wave progress all belong to a single run.
_Avoid_: Game, match, session

**Wave**:
A numbered batch of enemies within a run. It is cleared when all of its enemies have spawned and been killed.
_Avoid_: Level, round

**Upgrade**:
A boost the player picks from three Offers after each cleared wave. It changes the run's Stats for the rest of the run, or adds HP.
_Avoid_: Perk, power-up

**Offer**:
One of the three Upgrades shown after a cleared wave, together with a preview of what picking it would change.
_Avoid_: Choice, card

**Stats**:
The numbers of a run that Upgrades change: how often the snake moves and fires, how fast, big, damaging and piercing its bullets are, and how long it stays invulnerable after a hit. A run starts from the chosen speed and default values. HP is not a Stat, because enemies wear it down.
_Avoid_: Loadout, attributes
