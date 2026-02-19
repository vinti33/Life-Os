
import re

def extract_times(text):
    valid_times = []
    text_lower = text.lower()
    
    # regex 1: Times with colons (e.g. 10:00, 10:00am)
    # Group 1 captures the time
    r1 = re.compile(r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b')
    for match in r1.finditer(text_lower):
        valid_times.append(match.group(1))

    # regex 2: Times with AM/PM (e.g. 5am, 5 pm)
    r2 = re.compile(r'\b(\d{1,2}\s*[ap]m)\b')
    for match in r2.finditer(text_lower):
        valid_times.append(match.group(1))

    # regex 3: Times with prepositions (e.g. at 5, to 5)
    # Look for preposition then number
    r3 = re.compile(r'\b(?:at|to|from|until|by)\s+(\d{1,2}(?::\d{2})?)\b')
    for match in r3.finditer(text_lower):
        valid_times.append(match.group(1))

    # Deduplicate and sort (preserving order of appearance might be better but let's see)
    # The current agent returns list in order of appearance.
    # My regex approach might mix order if I iterate by regex.
    # Better to combine regex or scan once with alternatives.
    
    return valid_times

def extract_times_combined(text):
    """
    Combined regex to preserve order.
    Pattern:
    (TimeWithColon) | (TimeWithAMPM) | (Preposition + Time)
    """
    # 1. Colon Time: \d{1,2}:\d{2}(?:\s*[ap]m)?
    # 2. AMPM Time: \d{1,2}\s*[ap]m
    # 3. Preposition Time: (?<=at|to|from|until|by)\s+(\d{1,2}) (Lookbehind hard in variable width)
    # easier: (?:at|to|from|until|by)\s+(\d{1,2}(?::\d{2})?)
    
    # We want to capture the TIME part.
    
    # Pattern: \b((?:at|to|from|until|by)\s+)?(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)
    # But this matches "Session 1" if "at" is optional!
    
    # We need strict alternatives.
    # A: \d{1,2}:\d{2}(?:\s*[ap]m)?  (Match 12:30 or 12:30am)
    # B: \d{1,2}\s*[ap]m             (Match 5am)
    # C: (?:at|to|from|until|by)\s+(\d{1,2}(?::\d{2})?) (Match at 5)
    
    pat = r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b|\b(\d{1,2}\s*[ap]m)\b|\b(?:at|to|from|until|by)\s+(\d{1,2}(?::\d{2})?)\b'
    
    matches = []
    for m in re.finditer(pat, text.lower()):
        # m.groups() will be (TimeColon, TimeAMPM, TimePreposition)
        # One will be not None.
        t = next((x for x in m.groups() if x is not None), None)
        if t:
            matches.append(t)
    return matches

test_cases = [
    "change lunch time at 13:00 to 14:00",
    "make focus session 1 from 10:00 to 13:00",
    "change focus session 1 at 10:00 to 13:00",
    "change Focus Session 1 work at 10:00",
    "Meeting at 5",
    "Gym at 5pm",
    "Session 1",
    "Session 10",
]

print("--- Testing Combined Regex ---")
for t in test_cases:
    print(f"'{t}' -> {extract_times_combined(t)}")
