## Build Order Analyser

Shows exactly what turn every unit you have ever seen was built on. Good for
knowing if the enemy saved funds, or if they have a hidden unit that you
haven't seen yet.

It can also let you make educated guesses as to the location of other units.

For example:

> 1. I can see that **this recon was built on turn 3.**
> 2. That's very early - it means **my opponent's capture game is delayed.**
> 3. Because of that, I know **my opponent cannot possibly have built a tank
>    until turn 7** at the earliest (instead of turn 6), without base skipping

### Usage:

```
./build_order_analyser.py <game_id>
```

### Example output:

```
...

=== DAY 5.0 (opponent) ===
Total: $7000, (+$1000)
Infantry (10HP) - At 4x4

=== DAY 5.5 (my-username) ===
Total: $19000, (+$9000)
Tank (10HP) - At 12x9
Infantry (10HP) - At 11x9
Infantry (10HP) - At 4x1

=== DAY 6.0 (opponent) ===
Total: $15000, (+$8000)
Tank (8HP) - At 13x13
Infantry (10HP) - At 10x13

=== DAY 6.5 (my-username) ===
Total: $28000, (+$9000)
Tank (5HP) - At 13x8
Infantry (10HP) - At 9x6
Infantry (10HP) - At 7x1

... more lines
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
