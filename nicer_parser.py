import os

test_file = "temp.pml.trail"
test_exec = "./a.out"
output_file = "tempfile.txt"

def get_trail_out(executable, trail):
    system_command = "{} -r -S {} > {}".format(executable, trail, output_file)

    os.system(system_command)

def parse_trail_out():
    file = open(output_file)
    lines = file.readlines()
    file.close()

    li = []
    last = ""

    for line in lines:
        spl = line.split()
        if spl[0] == "pan:1:" and spl[1] == "assertion" and spl[2] == "violated" : # end of trail.
            elem = ["WIN", spl[-1][:-1]]
            li.append(elem)
            return li

        elif spl[1] == "-":

            if spl[0] == last:
                #add a skip to other
                if spl[0] == "Opponent":
                    add = ["Avatar", "Skip"]
                else:
                    add = ["Opponent", "Skip"]
                li.append(add)

            elem = [spl[0], spl[-1]]
            last = spl[0]
            li.append(elem)

        elif spl[0] == "MSC:":
            continue

        else:
            elem = ["LOSE", "-1"]
            return li

    delete_command = "rm {}".format(output_file)
    os.system(delete_command)

def print_playback(moves):
    if len(moves) == 0:
        print("LOST - LOST")
    for move in moves:
        print("{} - {}".format(move[0], move[1]))

def parse_moves(moves):
    if len(moves) == 0:
        return None, None

    if moves[-1][0] is "LOSE":
        return None, None

    avatar = []
    opponent = []
    if len(moves) == 0:
        return avatar, opponent
    else:
        for move in moves:
            if move[0] == "Avatar":
                avatar.append(move[1])
            elif move[0] == "Opponent":
                opponent.append(move[1])
            else:
                return avatar,opponent

def change_to_actions(avatar, opponent):
    av = []
    op = []

    for m_av in avatar:
        if m_av is "Skip":
            av.append(None)
        if m_av is "D":
            av.append(2)
        if m_av is "S":
            av.append(3)
        if m_av is "A":
            av.append(0)
        if m_av is "W":
            av.append(1)

    # TODO: Opponent cannot be moved yet, thus no point filling it.

    return av, op

if __name__ == "__main__":
    a, b = parse_moves(parse_trail_out())
    print(change_to_actions(a, b)) #passed
