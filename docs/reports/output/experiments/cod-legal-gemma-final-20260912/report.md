Artifacts: [run directory](<../../../../../output/experiments/cod-legal-gemma-final-20260912>). Unlinked artifact names below are relative to that directory.

# Fictional legal CoD Gemma probe

Six fixed English synthetic questions: prior consent, conjunctive exception, annex scope, actor/timing, missing appendix, authority attribution. Balanced YES/NO/UNKNOWN. Four separate locally authored legal examples. Exact paper CoD instruction plus fictional-rule task definition. Temperature0/output512/no thinking budget/no output grammar. Current local Gemma NVFP4 checkpoint. This is a short-rule format/correctness probe, not actual-law/dev200 accuracy.

OFF zero-shot:4/6 correct, mean40.67 tokens. L4 notes say no violation but finalYES; L6 mistakes missing authority evidence for proven absence. OFF4shot:6/6 correct, mean22.17 tokens, every note <=5 whitespace words. ON either condition:6/6 hit512 with509 body tokens and unclosed thought channel; no actual final answers. Parser fallback can expose unclosed thought as answer; explicitly exclude such output from final scoring (one internal draft contained #### YES). Fewshot benefits observed in this tiny authored set; no general accuracy/budget guarantee. Earlier aborted run excluded: example1 necessary/sufficient wording corrected before final run.

## L1 ON=False shots=0
Correct final=True body=0 total=37 finish=stop

```text
- Subletting occurred June 3.
- Consent given June 5.
- Consent was not prior.
- Breach occurred on June 3.

#### YES<turn|>
```

## L2 ON=False shots=0
Correct final=True body=0 total=38 finish=stop

```text
1. Emergency exists: True.
2. Dispatcher authorization: Refused.
3. Both conditions met: False.
4. Prohibited: Yes.

#### YES<turn|>
```

## L3 ON=False shots=0
Correct final=True body=0 total=34 finish=stop

```text
1. Annex covers pumps.
2. BETA is certified equivalent.
3. Annex overrides ALPHA requirement.
4. Labeling requirement met.

#### NO<turn|>
```

## L4 ON=False shots=0
Correct final=False body=0 total=53 finish=stop

```text
1. Rule: No certificate before selection.
2. Rule: Declaration before, certificate after.
3. Doc A: Declaration with bids.
4. Doc B: Certificate after selection.
5. Compliance check: No violation.

#### YES<turn|>
```

## L5 ON=False shots=0
Correct final=True body=0 total=54 finish=stop

```text
1. Rule: >10 days after notification.
2. Notification: May 1.
3. Receipt: Unknown (Appendix R missing).
4. Decision: May 20.
5. Cannot determine receipt date.

#### UNKNOWN<turn|>
```

## L6 ON=False shots=0
Correct final=False body=0 total=28 finish=stop

```text
1. Rule: written authority required.
2. Fact: email used.
3. Fact: authority unknown.

#### NO<turn|>
```

## L1 ON=False shots=4
Correct final=True body=0 total=30 finish=stop

```text
Subletting occurred June 3.
Consent given June 5.
Consent was not prior.
Breach occurred.
#### YES<turn|>
```

## L2 ON=False shots=4
Correct final=True body=0 total=17 finish=stop

```text
Emergency exists.
Authorization refused.
Both conditions not met.
#### YES<turn|>
```

## L3 ON=False shots=4
Correct final=True body=0 total=20 finish=stop

```text
Only pumps delivered.
Annex overrides main contract.
BETA is allowed.
#### NO<turn|>
```

## L4 ON=False shots=4
Correct final=True body=0 total=30 finish=stop

```text
Document A: Bidders' declaration.
Document B: Post-selection certificate.
Rule allows both.
No violation.
#### NO<turn|>
```

## L5 ON=False shots=4
Correct final=True body=0 total=20 finish=stop

```text
Receipt date unknown.
Appendix R missing.
Cannot determine lateness.
#### UNKNOWN<turn|>
```

## L6 ON=False shots=4
Correct final=True body=0 total=16 finish=stop

```text
Email used, authority unknown.
Authority not provided.
#### UNKNOWN<turn|>
```

## L1 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: A tenant must obtain written consent before subletting. Subletting without that consent is a breach.
    *   Facts: A tenant sublet a room on June 3. The landlord first gave written consent on June 5.
    *   Question: Did the tenant breach the rule on June 3?

    *   Rule: Consent must be obtained *before* subletting.
    *   Fact 1: Subletting occurred on June 3.
    *   Fact 2: Written consent was given on June 5.
    *   Comparison: June 3 (subletting) is before June 5 (consent).
    *   Conclusion: Consent was not obtained *before* the subletting. Therefore, the rule was breached.

    *   Step 1: Subletting date: June 3. (4 words)
    *   Step 2: Consent date: June 5. (4 words)
    *   Step 3: Consent after subletting. (3 words)
    *   Step 4: Breach occurred. (3 words)

    *   The question asks if the tenant breached the rule on June 3.
    *   Since the consent was given on June 5, the consent was not obtained *before* the subletting on June 3.
    *   Therefore, the breach occurred.

    *   Rule: Consent before subletting.
    *   Fact: Subletting June 3, Consent June 5.
    *   Result: Breach.

    *   Step 1: Subletting on June 3.
    *   Step 2: Consent on June 5.
    *   Step 3: Consent after subletting.
    *   Step 4: Breach is YES.

    *   Wait, the question asks "Did the tenant breach the rule on June 3?".
    *   The rule says: "A tenant must obtain written consent before subletting. Subletting without that consent is a breach."
    *   On June 3, the tenant sublet without consent (since consent came on June 5).
    *   So, YES, the tenant breached the rule.

    *   Step 1: Subletting date June 3.
    *   Step 2: Consent date June 5.
    *   
```

## L2 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: Night deliveries are prohibited unless (Emergency AND Dispatcher Authorization in advance).
    *   Facts:
        1.  An emergency existed.
        2.  The dispatcher expressly refused authorization.
        3.  A night delivery occurred.
    *   Question: Was the delivery prohibited?

    *   Condition for exception: (Emergency) AND (Dispatcher Authorization).
    *   Fact 1: Emergency = True.
    *   Fact 2: Dispatcher Authorization = False (refused).
    *   Condition (Emergency AND Dispatcher Authorization) = (True AND False) = False.
    *   Since the exception condition is False, the prohibition remains in effect.
    *   Therefore, the delivery was prohibited.

    *   Step 1: Check emergency status. (Emergency exists)
    *   Step 2: Check authorization status. (Authorization refused)
    *   Step 3: Evaluate exception condition. (Both required, one failed)
    *   Step 4: Determine if prohibited. (Prohibition applies)

    *   Step 1: Emergency exists. (3 words)
    *   Step 2: Authorization refused. (2 words)
    *   Step 3: Exception condition failed. (3 words)
    *   Step 4: Delivery was prohibited. (3 words)

    *   Rule: Prohibited unless (Emergency AND Authorization).
    *   Fact: Emergency (Yes), Authorization (No).
    *   Result: (Yes AND No) = No.
    *   Since the exception is not met, the delivery is prohibited.

    *   Wait, the question asks "Was the delivery prohibited?".
    *   If the exception is not met, the delivery is prohibited.
    *   The answer is YES.

    *   Step 1: Emergency exists.
    *   Step 2: Authorization refused.
    *   Step 3: Exception not met.
    *   Step 4: Delivery is prohibited.

    *   Step 1: Emergency exists. (3)
    *   Step 2: Authorization refused. (2)
    *   Step 3: Exception not met. (3)
    *   Step 4: Prohibited. (1)

    *   Wait, the prompt asks for "YES" or "NO" or "
```

## L3 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule 1: An annex overrides the main contract *only* for products explicitly listed in that annex.
    *   Rule 2 (Main Contract): Every supplied component must carry label ALPHA.
    *   Rule 3 (Annex): Pumps may carry any certified equivalent label.
    *   Fact 1: The supplier delivered only pumps bearing certified equivalent label BETA.
    *   Question: Did those deliveries breach the labeling requirement?

    *   Step 1: Identify the product type. (Pumps)
    *   Step 2: Check if product is in annex. (Pumps are in annex)
    *   Step 3: Determine if annex overrides main contract. (Yes, for pumps)
    *   Step 4: Apply the override rule. (Pumps can use BETA)
    *   Step 5: Check if BETA is a certified equivalent label. (Yes, it is)
    *   Step 6: Conclude if there's a breach. (No breach)

    *   Step 1: Identify product (Pumps). (5 words: Identify product: Pumps)
    *   Step 2: Check annex inclusion. (4 words: Pumps in annex)
    *   Step 3: Apply override rule. (3 words: Annex overrides ALPHA)
    *   Step 4: Check label BETA. (3 words: BETA is equivalent)
    *   Step 5: Determine breach. (3 words: No breach occurred)

    *   Rule: Annex overrides main contract for listed products.
    *   Main Contract: All components must have ALPHA.
    *   Annex: Pumps can have any certified equivalent label.
    *   Fact: Delivered pumps have label BETA (certified equivalent).
    *   Conclusion: Since pumps are in the annex, the requirement for ALPHA is overridden by the requirement for a certified equivalent label. BETA is a certified equivalent label. Therefore, no breach.

    *   Wait, let's re-read: "An annex overrides the main contract only for products explicitly listed in that annex."
    *   Main contract: "Every supplied component must carry label ALPHA."
    *   Annex: "Pumps may carry any certified equivalent label."
    *   Fact: "The supplier delivered only pumps bearing certified equivalent label BETA."
    *   Is BETA a "certified equivalent label"? The fact says
```

## L4 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: Agency must not demand external auditor's certificate *before* selection.
    *   Rule: Agency *may* demand bidder's own signed declaration *before* selection.
    *   Rule: Agency *may* demand external auditor's certificate *after* selection.
    *   Document A: Bidders must submit their own declaration with their bids (before selection).
    *   Document B: Only the selected contractor must obtain and submit an external auditor's certificate, after selection.
    *   Question: Do these requirements violate the rule?

    *   Requirement 1 (Document A): Submit own declaration with bids (before selection).
        *   Rule says: "It may demand the bidder's own signed declaration before selection".
        *   Conclusion: This is allowed.
    *   Requirement 2 (Document B): Selected contractor must submit external auditor's certificate after selection.
        *   Rule says: "It may demand... an external auditor's certificate afterward [after selection]".
        *   Conclusion: This is allowed.

    *   Both requirements follow the rule.
    *   Therefore, they do *not* violate the rule.

    *   Question: "Do these requirements violate the rule?"
    *   If they don't violate, the answer is NO.

    *   Step 1: Check Document A. (3 words)
    *   Step 2: Check Document B. (3 words)
    *   Step 3: Compare with rule. (3 words)
    *   Step 4: Determine violation. (3 words)

    *   Document A: Declaration before selection. (Allowed)
    *   Document B: Certificate after selection. (Allowed)
    *   Result: No violation.

    *   Rule: No certificate before selection.
    *   Doc A: Declaration before selection (Allowed).
    *   Doc B: Certificate after selection (Allowed).
    *   Question: Do they violate?
    *   Answer: NO.

    *   Step 1: Check Document A.
    *   Step 2: Check Document B.
    *   Step 3: Compare with rule.
    *   Step 4: Conclude violation.

    *   Step 1: Check Document A.
    *   Step 2: Check Document B.
```

## L5 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: Agency can reject as late *only if* receipt > 10 days after notification.
    *   Notification: May 1.
    *   Receipt date: Recorded in Appendix R (not provided).
    *   Decision signed: May 20.
    *   Question: Was rejection for lateness permitted?

    *   Step 1: Identify notification date (May 1).
    *   Step 2: Identify receipt date (Unknown, Appendix R missing).
    *   Step 3: Check rule condition (Receipt > 10 days after May 1).
    *   Step 4: Determine if receipt > May 11.
    *   Step 5: Since receipt date is unknown, cannot determine.

    *   Step 1: Notification is May 1. (5 words)
    *   Step 2: Receipt date is unknown. (4 words)
    *   Step 3: Rule requires receipt > 11. (5 words)
    *   Step 4: Cannot determine receipt date. (4 words)
    *   Step 5: Result is UNKNOWN. (3 words)

    *   Rule: Reject if receipt > 10 days after notification.
    *   Notification: May 1.
    *   10 days after May 1 is May 11.
    *   Receipt must be after May 11 for rejection to be permitted.
    *   Receipt date is in Appendix R (not provided).
    *   Since the receipt date is unknown, we cannot know if it was after May 11.
    *   Therefore, the conclusion is UNKNOWN.

    *   Step 1: Notification is May 1.
    *   Step 2: Receipt date is missing.
    *   Step 3: Rule needs receipt > 11.
    *   Step 4: Receipt date is unknown.
    *   Step 5: Conclusion is UNKNOWN.

    *   Step 1: Notification date is May 1.
    *   Step 2: Receipt date is unknown.
    *   Step 3: Rule requires receipt > 11.
    *   Step 4: Cannot determine receipt date.
    *   Step 5: Result is UNKNOWN.

    *   Step 1
```

## L6 ON=True shots=0
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: A company is bound by a settlement signed by an employee *only if* that employee has written authority from the company.
    *   Fact 1: An employee signed a settlement using the company's email account.
    *   Fact 2: The record contains no information about whether written authority exists.
    *   Question: Is the company bound by the settlement?

    *   Condition for being bound: Written authority exists.
    *   Fact: No information about written authority.
    *   Conclusion: Since the existence of written authority is unknown, the company's binding status is unknown.

    *   Step 1: Check rule condition. (Rule: written authority required)
    *   Step 2: Check facts. (Fact: no info on authority)
    *   Step 3: Determine conclusion. (Conclusion: unknown)

    *   Step 1: Rule requires written authority. (4 words)
    *   Step 2: Authority status is unknown. (4 words)
    *   Step 3: Conclusion is unknown. (3 words)

    *   Rule: Bound only if written authority.
    *   Fact: No info on authority.
    *   Result: UNKNOWN.

    *   Step 1: Rule requires written authority.
    *   Step 2: Authority status is unknown.
    *   Step 3: Conclusion is unknown.

    *   Wait, the prompt asks for "only keep a minimum draft for each thinking step, with 5 words at most."

    *   Step 1: Rule: written authority required.
    *   Step 2: Authority status is unknown.
    *   Step 3: Result is UNKNOWN.

    *   Let's re-verify the logic.
    *   Rule: Bound $\implies$ Written Authority.
    *   Fact: Written Authority = Unknown.
    *   If Written Authority is False, then Not Bound.
    *   If Written Authority is True, then Bound.
    *   Since Written Authority is Unknown, the binding status is UNKNOWN.

    *   Step 1: Rule requires written authority.
    *   Step 2: Authority status is unknown.
    *   Step 3: Conclusion is UNKNOWN.

    *   Wait, the prompt says "Return the answer at the end
```

## L1 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: A tenant must obtain written consent before subletting. Subletting without that consent is a breach.
    *   Facts: A tenant sublet a room on June 3. The landlord first gave written consent on June 5.
    *   Question: Did the tenant breach the rule on June 3?

    *   Step 1: Identify the rule. (Rule: Consent before subletting).
    *   Step 2: Identify the event. (Subletting on June 3).
    *   Step 3: Identify the consent. (Consent given on June 5).
    *   Step 4: Compare dates. (June 3 is before June 5).
    *   Step 5: Determine if consent was obtained *before* the sublet. (No, consent was after).
    *   Step 6: Conclude. (Breach occurred).

    *   Subletting date: June 3.
    *   Consent date: June 5.
    *   Consent was after subletting.
    *   Therefore, a breach occurred.

    *   A: Subletting occurred June 3.
    *   A: Consent given June 5.
    *   A: Consent after subletting.
    *   A: Breach occurred.

    *   Subletting on June 3.
    *   Consent on June 5.
    *   Consent after subletting.
    *   #### YES

    *   "Subletting on June 3." (4 words)
    *   "Consent on June 5." (4 words)
    *   "Consent after subletting." (3 words)
    *   "#### YES"

    *   Rule: Consent *before* subletting.
    *   Fact: Subletting (June 3), Consent (June 5).
    *   Is June 3 before June 5? Yes.
    *   Was consent obtained *before* the sublet? No.
    *   Therefore, the rule was breached.

    *   A: Subletting on June 3.
    *   A: Consent on June 5.
    *   A: Consent after subletting.
    *   #### YES

    *   Wait, the prompt asks for the answer in the same format
```

## L2 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: Night deliveries are prohibited unless BOTH (an emergency exists AND the dispatcher authorizes the delivery in advance).
    *   Facts:
        *   An emergency existed.
        *   The dispatcher expressly refused authorization.
        *   A night delivery occurred.
    *   Question: Was the delivery prohibited?

    *   Condition for NOT being prohibited: (Emergency AND Dispatcher Authorization).
    *   Fact 1: Emergency = True.
    *   Fact 2: Dispatcher Authorization = False (refused).
    *   Condition (Emergency AND Authorization) = (True AND False) = False.
    *   Since the condition for exemption is False, the prohibition applies.

    *   Step 1: Check emergency status. (Emergency exists)
    *   Step 2: Check authorization status. (Authorization refused)
    *   Step 3: Evaluate BOTH condition. (Both not met)
    *   Step 4: Determine if prohibited. (Prohibited)

    *   Emergency exists.
    *   Authorization refused.
    *   Both conditions unmet.
    *   Prohibition applies.

    *   A: Emergency exists.
    *   A: Authorization refused.
    *   A: Both conditions not met.
    *   A: Prohibited.

    *   Wait, the prompt asks for the answer at the end after `####`.
    *   The format of the previous examples:
        *   Q: ... A: [Reasoning] #### [YES/NO/UNKNOWN]
    *   Let's re-examine the structure.
    *   Q: Rule: ... Facts: ... Question?
    *   A: [Reasoning] #### [Conclusion]

    *   Rule: Prohibited unless (Emergency AND Authorization).
    *   Fact: Emergency (Yes), Authorization (No).
    *   Result: Prohibited.

    *   Step 1: Emergency exists.
    *   Step 2: Authorization refused.
    *   Step 3: Both not met.
    *   Step 4: Prohibited.

    *   Wait, the prompt asks for the answer at the end.
    *   The user provided the start of the answer: "A:".
    *   I need to complete the "A:" part.

    *   Let's
```

## L3 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: An annex overrides the main contract *only* for products explicitly listed in that annex.
    *   Main contract: Every supplied component must carry label ALPHA.
    *   Annex: Pumps may carry any certified equivalent label.
    *   Facts: The supplier delivered only pumps bearing certified equivalent label BETA.
    *   Question: Did those deliveries breach the labeling requirement?

    *   Step 1: Identify the product. (Pumps)
    *   Step 2: Check if product is in annex. (Pumps are in annex)
    *   Step 3: Check the rule for that product. (Annex overrides main contract for pumps)
    *   Step 4: Check the label used. (Label BETA)
    *   Step 5: Check if BETA is allowed. (Annex allows "any certified equivalent label")
    *   Step 6: Determine if it breaches the main contract. (No, because the annex overrides the ALPHA requirement for pumps)

    *   Step 1: Product is pumps. (Pumps in annex)
    *   Step 2: Annex allows equivalent labels. (BETA is equivalent)
    *   Step 3: Annex overrides ALPHA. (ALPHA requirement bypassed)
    *   Step 4: No breach occurred. (No breach)

    *   A: Pumps in annex.
    *   A: Annex allows equivalent.
    *   A: ALPHA requirement overridden.
    *   A: No breach.

    *   A: Pumps in annex.
    *   A: Annex allows equivalent.
    *   A: ALPHA requirement overridden.
    *   A: No breach.

    *   Wait, the format requires a brief draft for each step (max 5 words) and then the final answer after ####.

    *   Step 1: Pumps in annex.
    *   Step 2: Annex allows equivalent.
    *   Step 3: ALPHA requirement overridden.
    *   Step 4: No breach.

    *   Let's refine the draft:
    *   Pumps in annex.
    *   Annex allows equivalent labels.
    *   ALPHA requirement overridden.
    *   No breach.

    *   Final check:
    *   Rule: Annex overrides main contract for listed products.
    *   Main: ALPHA.

```

## L4 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: An agency must not demand an external auditor's certificate *before* selecting a contractor.
    *   Rule: It *may* demand the bidder's own signed declaration *before* selection.
    *   Rule: It *may* demand an external auditor's certificate *afterward* (after selection).
    *   Document A: Bidders must submit their own declaration with their bids.
    *   Document B: Only the selected contractor must obtain and submit an external auditor's certificate, after selection.
    *   Question: Do these requirements violate the rule?

    *   Document A: Bidders submit declaration with bids. (This is "before selection"). The rule says the agency *may* demand this. So, this is allowed.
    *   Document B: Selected contractor submits external auditor's certificate *after* selection. The rule says the agency *may* demand this *afterward*. So, this is allowed.

    *   Requirement A (Declaration before selection) is explicitly allowed.
    - Requirement B (External certificate after selection) is explicitly allowed.
    - Neither requirement violates the "must not demand... before" rule.

    *   Step 1: Check Document A.
    *   Step 2: Check Document B.
    *   Step 3: Compare with rule.
    *   Step 4: Determine violation.

    *   Step 1: Document A: declaration before. (3 words)
    *   Step 2: Document B: certificate after. (3 words)
    *   Step 3: Both allowed. (2 words)
    *   Step 4: No violation. (2 words)

    *   A: Declaration before selection.
    *   B: Certificate after selection.
    *   Both follow rules.
    *   No violation.

    *   A: Declaration before selection.
    *   B: Certificate after selection.
    *   Both are permitted.
    *   No violation.

    *   A: Declaration before selection.
    *   B: Certificate after selection.
    *   Both follow rules.
    *   No violation.

    *   A: Declaration before selection.
    *   B: Certificate after selection.
    *   Both are allowed.
    *   No violation.

    *   A:
```

## L5 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: Agency may reject a filing as late *only if* receipt occurred > 10 days after notification.
    *   Notification: May 1.
    *   Receipt date: Recorded in Appendix R (not provided).
    *   Rejection decision signed: May 20.
    *   Question: Was rejection for lateness permitted?

    *   Condition for rejection: Receipt > 10 days after notification.
    *   Notification date: May 1.
    *   Threshold for lateness: Receipt must be after May 11 (May 1 + 10 days).
    *   Fact: Receipt date is in Appendix R.
    *   Fact: Appendix R is not provided.
    *   Conclusion: The receipt date is unknown.

    *   Since the receipt date is unknown, we cannot determine if it was more than 10 days after May 1.
    *   Therefore, we cannot determine if the rejection for lateness was permitted.

    *   Step 1: Identify notification date. (May 1)
    *   Step 2: Identify threshold. (May 11)
    *   Step 3: Check receipt date. (Unknown)
    *   Step 4: Determine if threshold met. (Unknown)

    *   Step 1: Notification May 1.
    *   Step 2: Threshold May 11.
    *   Step 3: Receipt date unknown.
    *   Step 4: Cannot determine lateness.

    *   A: Receipt date unknown.
    *   A: Appendix R missing.
    *   A: Threshold unknown.
    *   A: Result unknown.

    *   Wait, the prompt asks for the answer at the end after a separator ####.
    *   The format of the previous examples shows the reasoning steps first, then the final answer.

    *   Example 1:
        A: Three overdue books.
        Required threshold satisfied.
        #### YES

    *   Example 2:
        A: Exactly forty attendees.
        Threshold requires more.
        #### NO

    *   Example 3:
        A: Purchase date missing.
        Elapsed time unknown.
        #### UNKNOWN

    *   Example 4:
        A: Online application verified.
        Certificate
```

## L6 ON=True shots=4
Correct final=False body=509 total=512 finish=length

```text
<|channel>thought
*   Rule: A company is bound by a settlement signed by an employee *only if* that employee has written authority from the company.
    *   Facts: An employee signed a settlement using the company's email account. The record contains no information about whether written authority exists.
    *   Question: Is the company bound by the settlement?

    *   Condition for being bound: Employee must have written authority.
    *   Fact 1: Employee signed using company email.
    *   Fact 2: No information about written authority.

    *   The rule states a condition (written authority) is necessary for the company to be bound.
    *   The facts do not state whether the employee has written authority or not.
    *   Therefore, the information is insufficient to determine if the company is bound.

    *   Step 1: Identify rule condition. (Rule: written authority required)
    *   Step 2: Check facts. (Authority unknown)
    *   Step 3: Determine result. (Unknown)

    *   A: Written authority unknown.
    *   A: Authority not specified.
    *   A: Authority status unknown.

    *   Rule: Bound if written authority exists.
    *   Fact: No info on authority.
    *   Conclusion: UNKNOWN.

    *   A: Written authority unknown.
    *   A: Authority status unknown.
    *   A: Authority not mentioned.

    Let's look at the previous examples:
    Q1: Three overdue books. Required threshold satisfied. #### YES
    Q2: Exactly forty attendees. Threshold requires more. #### NO
    Q3: Purchase date missing. Elapsed time unknown. #### UNKNOWN
    Q4: Online application verified. Certificate exception applies. Signature unnecessary. #### NO

    Following the pattern:
    A: Written authority unknown.
    A: Authority status unknown.
    A: Authority not specified.

    Let's try:
    A: Written authority unknown.
    A: Authority status unknown.

    Wait, the prompt asks for the answer at the end after a separator ####.

    Let's refine the "A:" part.
    A: Written authority unknown.
    A: Authority status unknown.
    A: Authority not specified.

    Let's look at the structure:
    A:
```
