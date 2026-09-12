Artifacts: [run directory](<../../../../../output/experiments/cod-plain-gemma-20260912>). Unlinked artifact names below are relative to that directory.

# Verbatim-paper CoD generic Gemma probe

Paper wording and author8 examples or zero-shot; single user payload per author code. Synthetic arithmetic5, no procurement. Temp0, total512, no separate thinking cap, no output schema. Paper a minimum differs from repo minimum; use paper. Capability smoke check, not benchmark reproduction.

OFF both conditions correct5/5, short notes/equations. Eight-shot average31.8 vs zero-shot53.4 total tokens. This is terse CoD-like behavior, not strict whitespace5 compliance (equations and some lines exceed it). ON both conditions no final answer before512;509 actual thinking body tokens with open channel, repetitive calculations. Arithmetic intermediate values are correct; missing final answers are completion failures, not demonstrated arithmetic errors. Does not establish impossibility at other budgets/sampling/checkpoints. Parser accounts for unclosed thinking channels rather than misreporting zero.

## A thinking=False shots=0
Correct final=True thinking body=0 total=34 finish=stop

```text
1. Start with 17.
2. Add 8.
3. Subtract 6.
4. Final calculation.

#### 19<turn|>
```

## B thinking=False shots=0
Correct final=True thinking body=0 total=56 finish=stop

```text
1. Total boxes: 4.
2. Pencils per box: 7.
3. Total pencils: 28.
4. Pencils used: 9.
5. Subtract 9 from 28.

#### 19<turn|>
```

## C thinking=False shots=0
Correct final=True thinking body=0 total=56 finish=stop

```text
1. Cost per ticket: $6.
2. Total cost: 3 * 6 = 18.
3. Paid amount: $25.
4. Change: 25 - 18 = 7.

#### 7<turn|>
```

## D thinking=False shots=0
Correct final=True thinking body=0 total=67 finish=stop

```text
1. Start with 48 liters.
2. One quarter is 12.
3. Subtract 12 from 48.
4. Result is 36.
5. Add 5 to 36.
6. Final total is 41.

#### 41<turn|>
```

## E thinking=False shots=0
Correct final=True thinking body=0 total=54 finish=stop

```text
1. 60 * 2 = 120.
2. 40 * 3 = 120.
3. 120 + 120 = 240.

#### 240<turn|>
```

## A thinking=False shots=8
Correct final=True thinking body=0 total=26 finish=stop

```text
17 + 8 = 25; 25 - 6 = 19. #### 19<turn|>
```

## B thinking=False shots=8
Correct final=True thinking body=0 total=25 finish=stop

```text
4 * 7 = 28; 28 - 9 = 19. #### 19<turn|>
```

## C thinking=False shots=8
Correct final=True thinking body=0 total=24 finish=stop

```text
3 * 6 = 18; 25 - 18 = 7. #### 7<turn|>
```

## D thinking=False shots=8
Correct final=True thinking body=0 total=40 finish=stop

```text
One quarter of 48 is 12.
48 - 12 = 36.
36 + 5 = 41.

#### 41<turn|>
```

## E thinking=False shots=8
Correct final=True thinking body=0 total=44 finish=stop

```text
60 * 2 = 120; 40 * 3 = 120; 120 + 120 = 240. #### 240<turn|>
```

## A thinking=True shots=0
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Initial marbles: 17
    *   Received: 8
    *   Gave away: 6
    *   Goal: Find the remaining marbles.

    *   Step 1: Add initial and received.
    *   Step 2: Subtract given away.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 plus 8 is 25.
    *   Step 2: 25 minus 6 is 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 plus 8 is 25.
    *   Step 2: 25 minus 6 is 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 2
```

## B thinking=True shots=0
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Input: "Four boxes contain 7 pencils each. Nine pencils are used. How many pencils remain?"
    *   Constraint: Think step by step, but only keep a minimum draft for each thinking step (max 5 words per step).
    *   Output format: Final answer after `####`.

    *   Step 1: Calculate total pencils.
        *   Draft: 4 boxes * 7 pencils.
        *   Step 1 (5 words): 4 times 7 is 28.
    *   Step 2: Subtract used pencils.
        *   Draft: 28 - 9.
        *   Step 2 (5 words): 28 minus 9 is 19.
    *   Step 3: Final result.
        *   Draft: 19 pencils.
        *   Step 3 (5 words): 19 pencils remain.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28. (4 words)
    *   Step 2: 28 - 9 = 19. (4 words)

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *Wait, the prompt says "Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most."*

    Let's refine the thinking steps:
    1. Total pencils: 4 * 7 = 28.
    2. Subtract used: 28 - 9 = 19.

    *Drafting the response:*
    4 * 7 = 28
    28 - 9 = 19

    Wait, the prompt asks for the answer at the end after `####`.

    Let's re-read: "Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. Return the answer at the end of the response after a separator ####."

    Step 1: 4 * 7 = 28
    Step 2:
```

## C thinking=True shots=0
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Ticket cost: $6.
    *   Number of tickets: 3.
    *   Amount paid: $25.
    *   Goal: Calculate the change received.

    *   Step 1: Calculate total cost of tickets.
    *   Step 2: Subtract total cost from amount paid.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18. (3 * 6 = 18)
    *   Step 2: 25 - 18 = 7. (25 - 18 = 7)

    *   Step 1: 3 * 6 = 18. (3 * 6 = 18)
    *   Step 2: 25 - 18 = 7. (25 - 18 = 7)

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 3 * 6 = 18.
    *   Step 2: 
```

## D thinking=True shots=0
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Initial amount: 48 liters.
    *   Action 1: One quarter is drained.
    *   Action 2: 5 liters are added.
    *   Goal: Find the final amount in the tank.

    *   Step 1: Calculate one quarter of 48.
    *   Step 2: Subtract that amount from 48.
    *   Step 3: Add 5 to the result.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Step 1: 48 / 4 = 12. (4 words)
    *   Step 2: 48 - 12 = 36. (4 words)
    *   Step 3: 36 + 5 = 41. (4 words)

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Wait, the prompt says "Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most."
    *   The final answer should be the result.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Step 
```

## E thinking=True shots=0
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Part 1: 60 km/h for 2 hours.
    *   Part 2: 40 km/h for 3 hours.
    *   Goal: Total distance in kilometers.

    *   Step 1: Calculate distance for Part 1.
    *   Step 2: Calculate distance for Part 2.
    *   Step 3: Sum the distances.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120. (5 words: 60 times 2 is 120)
    *   Step 2: 40 * 3 = 120. (5 words: 40 times 3 is 120)
    *   Step 3: 120 + 120 = 240. (5 words: 120 plus 120 is 240)

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Wait, the prompt says "Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most."
    *   This means the *thinking process* should be shown in the response, but the *drafts* within the thinking process must be short.

    *   Let's re-read: "Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. Return the answer at the end of the response after a separator ####."

    *
```

## A thinking=True shots=8
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Mia has 17 marbles.
    *   She receives 8 more.
    *   She gives away 6.
    *   Question: How many marbles remain?

    *   Step 1: Initial marbles + received marbles = 17 + 8.
    *   Step 2: Total marbles - given away marbles = (17 + 8) - 6.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   Step 1: 17 + 8 = 25.
    *   Step 2: 25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 -  6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   25 - 6 = 19.

    *   17 + 8 = 25.
    *   2
```

## B thinking=True shots=8
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Input: "Four boxes contain 7 pencils each. Nine pencils are used. How many pencils remain?"
    *   Goal: Calculate the number of remaining pencils.
    *   Constraint: Think step by step, minimum draft (max 5 words per step), return answer after ####.

    *   Step 1: Calculate total pencils.
        *   4 boxes * 7 pencils/box = 28 pencils.
    *   Step 2: Subtract used pencils.
        *   28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *   Step 2: 28 - 9 = 19.

    *   Step 1: 4 * 7 = 28.
    *
```

## C thinking=True shots=8
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Ticket cost: $6.
    *   Quantity: 3 tickets.
    *   Amount paid: $25.
    *   Goal: Find the change received.

    *   Step 1: Calculate total cost of tickets.
    *   Step 2: Subtract total cost from amount paid.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18 = 7.

    *   Step 1: 6 * 3 = 18.
    *   Step 2: 25 - 18
```

## D thinking=True shots=8
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Initial volume: 48 liters.
    *   Action 1: One quarter is drained.
    *   Action 2: 5 liters are added.
    *   Goal: Find the final volume.

    *   Step 1: Calculate one quarter of 48.
        *   48 / 4 = 12.
    *   Step 2: Subtract the drained amount from the initial volume.
        *   48 - 12 = 36.
    *   Step 3: Add the 5 liters.
        *   36 + 5 = 41.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Step 1: One quarter of 48. (4 words)
    *   Step 2: Subtract 12 from 48. (5 words)
    *   Step 3: Add 5 to 36. (5 words)

    *   48 / 4 = 12.
    *   48 - 12 = 36.
    *   36 + 5 = 41.

    *   48 / 4 = 12.
    *   48 - 12 = 36.
    *   36 + 5 = 41.

    *   48 / 4 = 12.
    *   48 - 12 = 36.
    *   36 + 5 = 41.

    *   Wait, the prompt asks for the answer in the format: `A: [steps]. #### [answer]`.

    *   Step 1: 48 / 4 = 12.
    *   Step 2: 48 - 12 = 36.
    *   Step 3: 36 + 5 = 41.

    *   Let's refine the steps for the final output.
    *   48 / 4 = 12; 48 - 12 = 3
```

## E thinking=True shots=8
Correct final=False thinking body=509 total=512 finish=length

```text
<|channel>thought
*   Input: A series of math word problems with their solutions.
    *   Task: Solve the final problem: "A train travels at 60 kilometers per hour for 2 hours, then 40 kilometers per hour for 3 hours. What total distance does it travel in kilometers?"
    *   Constraint: Think step by step, but only keep a minimum draft for each thinking step (max 5 words per step). Return the answer after `####`.

    *   Part 1: 60 km/h for 2 hours.
    *   Part 2: 40 km/h for 3 hours.
    *   Goal: Total distance.

    *   Step 1: Calculate distance 1.
    *   Step 2: Calculate distance 2.
    *   Step 3: Sum the distances.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60 * 2 = 120.
    *   Step 2: 40 * 3 = 120.
    *   Step 3: 120 + 120 = 240.

    *   Step 1: 60
```
