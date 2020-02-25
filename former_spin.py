import random # to generate inside walls with a probability.
import os

list_sprites = []

promela_whole_file = """
{}
{}
{}
{}
{}
{}
{}
"""
#Formatted areas:
#1- promela_comment_01
#2- promela_comment_02
#3- promela_header
#4- promela_avatar_process
#5- promela_opponent_process
#6- promela_init
#7- promela_ltl_formula

promela_comment_01 = """
//Game:
//Escape the opponent via stepping on the portal
//Game level presentation:
//.- Floor
//W- Wall
//A- Avatar
//E- End portal
//O- Opponent
//The level:
"""

promela_comment_02 = """
//The level as enumeration:
//0- Floor
//1- Wall
//2- Avatar
//3- End portal
//4- Opponent
"""

promela_header = """
typedef row{ //2D arrays are not supported directly.
	byte a[8];
}
bit win = 0; // Becomes 1 when maze is won.
bit dead = 0; // Becomes 1 when maze is lost.
bool lock = 0; // Avatar and Enemy must not move interleavingly.
row map[8];  // This becomes a 2D array.
"""

promela_avatar_process = """
proctype avatar(byte x; byte y) {
	map[x].a[y] = 2;
	byte w, a, s, d;
	do
	:: ( (win == 0) && (dead == 0) ) ->
		!lock; //Wait for your turn
		atomic { // Even if it is locked, enemy not checking lock while avatar is moving may improve performance.
			// Lookup for future checks.
			w = map[x].a[y-1];
			a = map[x-1].a[y];
			s = map[x].a[y+1];
			d = map[x+1].a[y];
			if
			:: w != 1 -> // Chooses to move up if there is not a wall.
				printf("Avatar - W\\n");
				if
				:: w == 0 -> // Regular move to an empty cell
					map[x].a[y] = 0;
					map[x].a[y-1] = 2;
					y = y - 1
				:: w == 3 -> // Move to the portal to win
					win = 1
				:: w == 4 -> // Move to the enemy to lose
					dead = 1
				fi;
			:: a != 1 -> // Chooses to move left if there is not a wall
				printf("Avatar - A\\n");
				if
				:: a == 0 -> // Regular move to an empty cell
					map[x].a[y] = 0;
					map[x-1].a[y] = 2;
					x = x - 1
				:: a == 3 -> // Move to the portal to win
					win = 1
				:: a == 4 -> // Move to the enemy to lose
					dead = 1
				fi;
			:: s != 1 -> // Chooses to move down if there is not a wall
				printf("Avatar - S\\n");
				if
				:: s == 0 -> // Regular move to an empty cell
					map[x].a[y] = 0;
					map[x].a[y+1] = 2;
					y = y + 1
				:: s == 3 -> // Move to the portal to win
					win = 1
				:: s == 4 -> // Move to the enemy to lose
					dead = 1
				fi;
			:: d != 1 -> // Chooses to move right if there is not a wall
				printf("Avatar - D\\n");
				if
				:: d == 0 -> // Regular move to an empty cell
					map[x].a[y] = 0;
					map[x+1].a[y] = 2;
					x = x + 1
				:: d == 3 -> // Move to the portal to win
					win = 1
				:: d == 4 -> // Move to the enemy to lose
					dead = 1
				fi;
			:: true -> skip // May skip the turn
			fi;
		lock = 1 // Pass the turn no matter what you choose
		}
	:: ( (win == 1) ) ->
		printf("Avatar - Win\\n");
		lock = 1; // Pass the turn even if the game ends
		break // Game ended
	:: ( (dead == 1) ) ->
		printf("Avatar - Dead\\n");
		lock = 1;
		break
	od;
}
"""

promela_opponent_process = """
proctype opponent(byte x; byte y){
	map[x].a[y] = 4;
	byte w, a, s, d;
	do
	:: ( (win == 0) && (dead == 0) ) -> // Game continues
		lock; // Wait for your turn
		atomic{  // Even if it is locked, avatar not checking lock while opponent is moving may improve performance.
			//lookup
			w = map[x].a[y-1];
			a = map[x-1].a[y];
			s = map[x].a[y+1];
			d = map[x+1].a[y];
			if
			:: ( ( w != 1 ) && ( w != 3 ) ) -> //Move to up, cannot move on walls or portal.
				printf("Opponent - W\\n");
				if
				:: w == 0 -> // Regular move
					map[x].a[y-1] = 4;
					map[x].a[y] = 0;
					y = y - 1
				:: w == 2 -> // Move to the avatar, make it lose
					dead = 1
				fi;
			:: ( ( a != 1 ) && ( a != 3 ) ) -> //Move to left, cannot move on walls or portal.
				printf("Opponent - A\\n");
				if
				:: a == 0 -> // Regular move
					map[x-1].a[y] = 4;
					map[x].a[y] = 0;
					x = x - 1
				:: a == 2 -> // Move to the avatar, make it lose
					dead = 1
				fi;
			:: ( ( s != 1 ) && ( s != 3 ) ) -> // Move to down, cannot move on walls or portal.
				printf("Opponent - S\\n");
				if
				:: s == 0 -> // Regular move.
					map[x].a[y+1] = 4;
					map[x].a[y] = 0;
					y = y + 1
				:: s == 2 -> // Move to the avatar, make it lose.
					dead = 1
				fi;
			:: ( ( d != 1 ) && ( d != 3 ) ) -> // Move to right, cannot move on walls or portals.
				printf("Opponent - D\\n");
				if
				:: d == 0 -> // Regular move.
					map[x+1].a[y] = 4;
					map[x].a[y] = 0;
					x = x + 1
				:: d == 2 -> // Move to the avatar, make it lose.
					dead = 1
				fi;
			:: true -> skip // May skip a turn.
			fi;
			lock = 0 // Pass the turn no matter what you choose
		}
	:: ( (win == 1) ) -> // Game has ended
		printf("Opponent - Win\\n");
		lock = 0; // Pass the turn even if the game ends
		break
	:: ( (dead == 1) ) ->
		printf("Opponent - Dead\\n");
		lock = 0;
		break
	od;
}
"""

promela_ltl_formula = """
// LTL Formula : In any time, win never be true.
// Counter-Example will be generated -> A scenario to win.
ltl  { [] !win };
"""

promela_init = """
init{{
    byte i, ii;
    for (i : 0 .. 7) {{
        // Initialize walls
        map[7].a[i] = 1;
        map[0].a[i] = 1;
        map[i].a[0] = 1;
        map[i].a[7] = 1;
    }}
    for (i : 1 .. 6) {{
        for (ii : 1 .. 6) {{
            // Initialize floors
            map[i].a[ii] = 0;
        }}
    }}
    //Generic placement of walls
    {}
    //Place portal
    map[{}].a[{}] = 3;
    run avatar({},{});
    run opponent({},{});
}}
"""
#Formatted area:
#1- Generic walls
#2- Portal, X coordinate
#3- Portal, Y coordinate
#4- Avatar, X coordinate
#5- Avatar, Y coordinate
#6- Opponent, X coordinate
#7- Opponent, Y coordinate

def generate_walls():
	walls = []
	flag = False
	wall_string = """{}"""

	for i in range (1,7):
		for ii in range (1,7):
			if(random.random() >= 0.8):
				for a in list_sprites:
					if a[1] == i and a[2] == ii:
						flag = True
				if flag is False:
					walls.append([i,ii])
				flag = False

	for wall in walls:
		list_sprites.append(["Wall", wall[0], wall[1]])
		wall_string = wall_string.format("\tmap[{}].a[{}] = 1; \n{}".format(wall[0], wall[1], "{}"))
		if walls.index(wall) == (len(walls)-1):
			wall_string = wall_string.format("")

	return wall_string

def generate_portal_avatar_opponent():

    portal = [random.randint(1,6), random.randint(1,6)]
    avatar = [random.randint(1,6), random.randint(1,6)]
    opponent = [random.randint(1,6), random.randint(1,6)]

    if portal == avatar or portal == opponent or opponent == avatar:
        return generate_portal_avatar_opponent()

    return portal[0], portal[1], avatar[0], avatar[1], opponent[0], opponent[1]

def generate_all():
	li = generate_portal_avatar_opponent()
	temp_p = ["Portal", li[0], li[1]]
	list_sprites.append(temp_p)
	temp_a = ["Avatar", li[2], li[3]]
	list_sprites.append(temp_a)
	temp_o = ["Opponent", li[4], li[5]]
	list_sprites.append(temp_o)

	formatted_init = promela_init.format(generate_walls(), li[0], li[1], li[2], li[3], li[4], li[5])
	return promela_whole_file.format(promela_comment_01, promela_comment_02, promela_header, promela_avatar_process, promela_opponent_process, formatted_init, promela_ltl_formula)


def generate_compile_spin():
	os.system("mkdir spin")
	os.system("rm spin/temp.pml")

	f = open("spin/temp.pml", "a")
	f.write(generate_all())
	f.close()

	os.system("spin -a spin/temp.pml")
	os.system("gcc pan.c -DREACH -o temp.out")
	os.system("./temp.out -a -i -m3000")

def generate_only_spin():
	return generate_all()

def mazify():

	arr = [list("......"), list("......"), list("......"), list("......"), list("......"), list("......")]



	print(list_sprites)

	for elem in list_sprites:
		if elem[0] is "Portal":
			arr[elem[1]-1][elem[2]-1] = "G"
		elif elem[0] is "Avatar":
			arr[elem[1]-1][elem[2]-1] = "A"
		elif elem[0] is "Opponent":
			arr[elem[1]-1][elem[2]-1] = "E"
		elif elem[0] is "Wall":
			arr[elem[1]-1][elem[2]-1] = "w"


	maze_str = ""
	maze_str += "wwwwwwww\n"
	for line in arr:
		maze_str += "w"

		for a in line:
			maze_str += a

		maze_str += "w"
		maze_str += "\n"
	maze_str += "wwwwwwww"

	return maze_str

if __name__ == "__main__":
	print(generate_only_spin())
	print(mazify())
