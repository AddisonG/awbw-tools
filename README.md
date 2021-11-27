## Build Order Analyser

This shows exactly what turn every unit you can see was built on. This can be
good for knowing if the enemy saved funds, or if they have a hidden unit that
you haven't seen yet.

### Usage:

```
./build_order_analyser.py <game_id>
```

### Example output:

```
...
=== DAY 5.0 (my-username) ===
Infantry    (95895361)
Infantry    (95895840)
Recon       (95895853)
=== DAY 5.5 (other-username) ===
Infantry    (95896061)
Recon       (95896095)
Recon       (95896101)
=== DAY 6.0 (my-username) ===
Artillery   (95902744)
Infantry    (95902748)
Infantry    (95902751)
=== DAY 6.5 (other-username) ===
Tank        (95905219)
Infantry    (95905226)
Infantry    (95905236)
=== DAY 7.0 (my-username) ===
Tank        (95996096)
Infantry    (95996098)
Infantry    (95996100)
...
```


## Player Analyser

Shows what ratio of units players built in previous games, and the order that
each new unit appeared. This can help reveal if players have a tendency to
always open with a certain unit (e.g: recon/tank), and show if they are likely
to follow up with artillery, b-copter, or anti-air.

### Usage:

```
# This will use your own username (from creds.json) if none is specified
./player_analyser.py [username]
```

### Example output:

```
ANALYSING GAME 123456. SomeOtherUser playing as Adder
==12-TURN RATIOS==
{'Artillery': '8.33%', 'Tank': '33.33%', 'Recon': '16.67%', 'B-Copter': '25.0%', 'Anti-Air': '16.67%'}

ANALYSING GAME 234567. SomeOtherUser playing as Sonja
==12-TURN RATIOS==
{'Tank': '43.48%', 'B-Copter': '26.09%', 'Recon': '8.7%', 'Anti-Air': '13.04%', 'Md.Tank': '4.35%', 'Mech': '4.35%'}
```
