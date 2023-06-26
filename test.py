def clue(word, guess):
    clue_str = ""
    for i in range(len(word)):
        if word[i] == guess[i]:
            clue_str += word[i].upper()
        elif guess[i] in word:
            clue_str += guess[i].lower()
        else:
            clue_str += "-"
    return clue_str

print(clue("stair",'trail'))
print(clue("stair","steer"))
print(clue("stair","braid"))