

## Build Order Analyser

This shows exactly what turn every unit you can see was built on. This can be good for knowing if the enemy saved funds, or if they have a hidden unit that you haven't seen yet.

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
